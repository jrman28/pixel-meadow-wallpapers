#!/usr/bin/env python3
"""Shared timing, filter, and quality analysis for AI video wallpapers."""

from __future__ import annotations

import json
import math
import statistics
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Sequence


class PipelineError(ValueError):
    """Raised when a source cannot satisfy the wallpaper delivery contract."""


@dataclass(frozen=True)
class Timing:
    fps: int
    slowdown: float
    source_duration: float
    processed_frames: int
    processed_duration: float
    crossfade_frames: int
    crossfade_duration: float
    xfade_offset_frames: int
    xfade_offset: float
    output_frames: int
    output_duration: float


@dataclass(frozen=True)
class Crop:
    width: int
    height: int
    x: int
    y: int = 0


@dataclass(frozen=True)
class DeltaReport:
    frame_count: int
    moving_frame_count: int
    adjacent_mean: float
    moving_median: float
    moving_p90: float
    moving_p95: float
    maximum_delta: float
    maximum_delta_frame: int
    seam_delta: float
    seam_ratio: float
    seam_limit: float
    seam_pass: bool
    anomaly_frames: tuple[int, ...]


def _frame_count(seconds: float, fps: int) -> int:
    return int(math.floor(seconds * fps + 0.5))


def calculate_timing(
    source_duration: float,
    *,
    slowdown: float = 2.0,
    crossfade: float = 1.5,
    fps: int = 24,
) -> Timing:
    if source_duration <= 0:
        raise PipelineError("source duration must be greater than zero")
    if slowdown <= 0:
        raise PipelineError("slowdown must be greater than zero")
    if fps <= 0:
        raise PipelineError("fps must be greater than zero")

    processed_frames = _frame_count(source_duration * slowdown, fps)
    crossfade_frames = _frame_count(crossfade, fps)
    if crossfade_frames <= 0:
        raise PipelineError("crossfade must be at least one output frame")
    if crossfade_frames * 2 >= processed_frames:
        raise PipelineError("crossfade must be shorter than half the slowed video")

    processed_duration = processed_frames / fps
    crossfade_duration = crossfade_frames / fps
    output_frames = processed_frames - crossfade_frames
    xfade_offset_frames = processed_frames - 2 * crossfade_frames

    return Timing(
        fps=fps,
        slowdown=slowdown,
        source_duration=source_duration,
        processed_frames=processed_frames,
        processed_duration=processed_duration,
        crossfade_frames=crossfade_frames,
        crossfade_duration=crossfade_duration,
        xfade_offset_frames=xfade_offset_frames,
        xfade_offset=xfade_offset_frames / fps,
        output_frames=output_frames,
        output_duration=output_frames / fps,
    )


def calculate_crop(width: int, height: int, crop_x: int | None = None) -> Crop:
    if width <= 0 or height <= 0:
        raise PipelineError("input dimensions must be positive")

    crop_width = int(height * 8 / 5)
    crop_width -= crop_width % 2
    if width < crop_width:
        raise PipelineError("input is narrower than 16:10")

    maximum_x = width - crop_width
    selected_x = maximum_x // 2 if crop_x is None else crop_x
    selected_x -= selected_x % 2
    if selected_x < 0 or selected_x > maximum_x:
        raise PipelineError(f"crop x must be between 0 and {maximum_x}")
    return Crop(width=crop_width, height=height, x=selected_x)


def build_filter_graph(
    timing: Timing,
    crop: Crop,
    *,
    target_width: int = 2560,
    target_height: int = 1600,
) -> str:
    if target_width <= 0 or target_height <= 0:
        raise PipelineError("target dimensions must be positive")

    return (
        f"[0:v]crop={crop.width}:{crop.height}:{crop.x}:{crop.y},"
        f"setpts={timing.slowdown:.8f}*(PTS-STARTPTS),"
        f"fps={timing.fps},trim=end_frame={timing.processed_frames},"
        "setpts=PTS-STARTPTS,"
        f"scale={target_width}:{target_height}:flags=neighbor,split=2[tail][head];"
        f"[tail]trim=start_frame={timing.crossfade_frames}:"
        f"end_frame={timing.processed_frames},setpts=PTS-STARTPTS[tailr];"
        # xfade samples crossfade_frames inputs but does not reach the final
        # head frame on its last output frame. Advancing the head by one frame
        # closes that discrete phase gap at the loop boundary.
        f"[head]trim=start_frame=1:end_frame={timing.crossfade_frames + 1},"
        "setpts=PTS-STARTPTS[headr];"
        f"[tailr][headr]xfade=transition=fade:"
        f"duration={timing.crossfade_duration:.6f}:"
        f"offset={timing.xfade_offset:.6f},format=yuv420p10le[outv]"
    )


def _mean_absolute_delta(left: bytes, right: bytes) -> float:
    if len(left) != len(right) or not left:
        raise PipelineError("frames must be non-empty and equally sized")
    return sum(abs(a - b) for a, b in zip(left, right)) / len(left)


def _percentile(sorted_values: Sequence[float], percentile: float) -> float:
    index = min(len(sorted_values) - 1, int((len(sorted_values) - 1) * percentile))
    return sorted_values[index]


def analyze_frame_deltas(
    frames: Sequence[bytes],
    *,
    moving_threshold: float = 0.1,
    seam_limit: float = 1.25,
) -> DeltaReport:
    if len(frames) < 3:
        raise PipelineError("at least three decoded frames are required")

    adjacent = [
        _mean_absolute_delta(frames[index], frames[index + 1])
        for index in range(len(frames) - 1)
    ]
    moving = sorted(delta for delta in adjacent if delta > moving_threshold)
    if not moving:
        raise PipelineError("video contains no measurable motion")

    p90 = _percentile(moving, 0.90)
    p95 = _percentile(moving, 0.95)
    seam = _mean_absolute_delta(frames[-1], frames[0])
    seam_ratio = seam / p90 if p90 else math.inf
    maximum = max(adjacent)
    anomaly_limit = p95 * 1.75

    return DeltaReport(
        frame_count=len(frames),
        moving_frame_count=len(moving),
        adjacent_mean=statistics.mean(adjacent),
        moving_median=statistics.median(moving),
        moving_p90=p90,
        moving_p95=p95,
        maximum_delta=maximum,
        maximum_delta_frame=adjacent.index(maximum),
        seam_delta=seam,
        seam_ratio=seam_ratio,
        seam_limit=seam_limit,
        seam_pass=seam_ratio <= seam_limit,
        anomaly_frames=tuple(
            index for index, delta in enumerate(adjacent) if delta > anomaly_limit
        ),
    )


def probe_video(path: str | Path) -> dict[str, Any]:
    completed = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-count_frames",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def source_video_info(metadata: dict[str, Any]) -> tuple[int, int, float, int]:
    videos = [stream for stream in metadata.get("streams", []) if stream.get("codec_type") == "video"]
    if len(videos) != 1:
        raise PipelineError("input must contain exactly one video stream")
    video = videos[0]
    duration = float(video.get("duration") or metadata.get("format", {}).get("duration") or 0)
    frame_count = int(video.get("nb_read_frames") or video.get("nb_frames") or 0)
    if frame_count <= 0:
        raise PipelineError("input frame count could not be detected")
    return int(video["width"]), int(video["height"]), duration, frame_count


def decode_analysis_frames(path: str | Path, width: int = 320, height: int = 200) -> list[bytes]:
    frame_size = width * height
    completed = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-vf",
            # Score low-frequency motion rather than HEVC block/GOP noise.
            # This still exposes real restart jumps while making frame zero
            # comparable to inter-predicted frames at the end of the file.
            f"scale={width}:{height}:flags=area,boxblur=1:1,format=gray",
            "-f",
            "rawvideo",
            "-",
        ],
        check=True,
        capture_output=True,
    )
    data = completed.stdout
    if len(data) % frame_size:
        raise PipelineError("decoded analysis stream ended on a partial frame")
    return [data[index : index + frame_size] for index in range(0, len(data), frame_size)]


def validate_delivery_metadata(
    metadata: dict[str, Any], expected_frames: int
) -> list[str]:
    streams = metadata.get("streams", [])
    videos = [stream for stream in streams if stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if stream.get("codec_type") == "audio"]
    errors: list[str] = []
    if len(videos) != 1:
        return ["expected exactly one video stream"]
    if audios:
        errors.append("expected zero audio streams")

    video = videos[0]
    expected = {
        "codec_name": "hevc",
        "codec_tag_string": "hvc1",
        "width": 2560,
        "height": 1600,
        "pix_fmt": "yuv420p10le",
        "r_frame_rate": "24/1",
    }
    for key, value in expected.items():
        if video.get(key) != value:
            errors.append(f"expected {key}={value}, got {video.get(key)}")

    actual_frames = int(video.get("nb_read_frames") or video.get("nb_frames") or 0)
    if actual_frames != expected_frames:
        errors.append(f"expected {expected_frames} frames, got {actual_frames}")
    expected_duration = expected_frames / 24
    actual_duration = float(metadata.get("format", {}).get("duration") or 0)
    if abs(actual_duration - expected_duration) > 1 / 48:
        errors.append(
            f"expected duration {expected_duration:.6f}, got {actual_duration:.6f}"
        )
    return errors


def summarize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    streams = metadata.get("streams", [])
    videos = [stream for stream in streams if stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if stream.get("codec_type") == "audio"]
    video = videos[0] if videos else {}
    frame_rate = video.get("r_frame_rate") or video.get("avg_frame_rate")
    return {
        "codec": video.get("codec_name"),
        "profile": video.get("profile"),
        "codec_tag": video.get("codec_tag_string"),
        "pixel_format": video.get("pix_fmt"),
        "width": video.get("width"),
        "height": video.get("height"),
        "frame_rate": frame_rate,
        "frame_count": int(video.get("nb_read_frames") or video.get("nb_frames") or 0),
        "duration": float(
            video.get("duration")
            or metadata.get("format", {}).get("duration")
            or 0
        ),
        "audio_streams": len(audios),
    }


def report_as_dict(report: DeltaReport) -> dict[str, Any]:
    return asdict(report)

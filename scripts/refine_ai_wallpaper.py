#!/usr/bin/env python3
"""Create a silent, frame-quantized, cyclically crossfaded video wallpaper."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

from analyze_loop import analyze
from wallpaper_pipeline import (
    PipelineError,
    build_filter_graph,
    calculate_crop,
    calculate_timing,
    probe_video,
    source_video_info,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--slowdown", type=float, default=2.0)
    parser.add_argument("--crossfade", type=float, default=1.5)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--width", type=int, default=2560)
    parser.add_argument("--height", type=int, default=1600)
    parser.add_argument("--crop-x", default="center")
    parser.add_argument("--mode", choices=("preview", "production"), default="production")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--visual-approval",
        action="store_true",
        help="keep seam scoring informational after a three-loop visual approval",
    )
    return parser.parse_args()


def crop_x_value(raw: str) -> int | None:
    if raw == "center":
        return None
    try:
        return int(raw)
    except ValueError as error:
        raise PipelineError("--crop-x must be 'center' or an integer") from error


def ffmpeg_command(args: argparse.Namespace, filter_graph: str) -> list[str]:
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(args.input),
        "-filter_complex",
        filter_graph,
        "-map",
        "[outv]",
        "-an",
    ]
    if args.mode == "production":
        command.extend(
            [
                "-c:v",
                "libx265",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p10le",
                "-tag:v",
                "hvc1",
            ]
        )
    else:
        command.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-tag:v",
                "avc1",
            ]
        )
    command.extend(["-movflags", "+faststart", str(args.output)])
    return command


def main() -> int:
    args = parse_args()
    try:
        metadata = probe_video(args.input)
        source_width, source_height, source_duration, source_frames = source_video_info(
            metadata
        )
        timing = calculate_timing(
            source_duration,
            slowdown=args.slowdown,
            crossfade=args.crossfade,
            fps=args.fps,
        )
        crop = calculate_crop(
            source_width, source_height, crop_x=crop_x_value(args.crop_x)
        )
        filter_graph = build_filter_graph(
            timing,
            crop,
            target_width=args.width,
            target_height=args.height,
        )
    except (PipelineError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Refinement setup failed: {error}", file=sys.stderr)
        return 1

    specification = {
        "input": str(args.input),
        "output": str(args.output),
        "mode": args.mode,
        "source": {
            "width": source_width,
            "height": source_height,
            "duration": source_duration,
            "frame_count": source_frames,
        },
        "timing": asdict(timing),
        "crop": asdict(crop),
        "filter_graph": filter_graph,
    }
    if args.dry_run:
        print(json.dumps(specification, indent=2))
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    command = ffmpeg_command(args, filter_graph)
    try:
        subprocess.run(command, check=True)
        report = analyze(
            args.output,
            seam_limit=1.25,
            expected_frames=timing.output_frames,
            production=args.mode == "production",
        )
    except (PipelineError, OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"Refinement failed: {error}", file=sys.stderr)
        return 1

    report["specification"] = specification
    report_path = args.output.with_suffix(args.output.suffix + ".analysis.json")
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    motion = report["motion"]
    print(
        f"Created {args.output}: {timing.output_frames} frames, "
        f"{timing.output_duration:.3f}s, seam ratio {motion['seam_ratio']:.2f}x"
    )
    seam_blocks_delivery = not motion["seam_pass"] and not args.visual_approval
    if args.mode == "production" and (
        report["metadata_errors"] or seam_blocks_delivery
    ):
        print(f"Production gate failed; inspect {report_path}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

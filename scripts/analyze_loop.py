#!/usr/bin/env python3
"""Measure wallpaper loop continuity and optionally enforce delivery metadata."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from wallpaper_pipeline import (
    PipelineError,
    analyze_frame_deltas,
    decode_analysis_frames,
    probe_video,
    report_as_dict,
    summarize_metadata,
    validate_delivery_metadata,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--expected-frames", type=int)
    parser.add_argument("--expect-production", action="store_true")
    parser.add_argument("--require-seam", action="store_true")
    parser.add_argument("--seam-limit", type=float, default=1.25)
    return parser.parse_args()


def analyze(path: Path, seam_limit: float, expected_frames: int | None, production: bool):
    metadata = probe_video(path)
    motion = analyze_frame_deltas(
        decode_analysis_frames(path), seam_limit=seam_limit
    )
    metadata_errors: list[str] = []
    if production:
        if expected_frames is None:
            raise PipelineError("--expected-frames is required with --expect-production")
        metadata_errors = validate_delivery_metadata(metadata, expected_frames)
    report = {
        "video": str(path),
        "media": summarize_metadata(metadata),
        "motion": report_as_dict(motion),
        "metadata_errors": metadata_errors,
    }
    return report


def main() -> int:
    args = parse_args()
    try:
        report = analyze(
            args.video,
            args.seam_limit,
            args.expected_frames,
            args.expect_production,
        )
    except (PipelineError, OSError, ValueError) as error:
        print(f"Analysis failed: {error}", file=sys.stderr)
        return 1

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(report, indent=2) + "\n")

    motion = report["motion"]
    media = report["media"]
    print(
        "Media: "
        f"{media['codec']} {media['profile']} {media['codec_tag']} "
        f"{media['width']}x{media['height']} {media['frame_rate']} "
        f"frames={media['frame_count']} duration={media['duration']:.3f}s "
        f"audio={media['audio_streams']}\n"
        "Loop analysis: "
        f"frames={motion['frame_count']} "
        f"seam={motion['seam_delta']:.4f} "
        f"p90={motion['moving_p90']:.4f} "
        f"ratio={motion['seam_ratio']:.2f}x "
        f"limit={motion['seam_limit']:.2f}x "
        f"pass={str(motion['seam_pass']).lower()}"
    )
    if motion["anomaly_frames"]:
        print(f"Motion anomaly frames: {motion['anomaly_frames']}")
    for error in report["metadata_errors"]:
        print(f"Metadata error: {error}")

    failed = bool(report["metadata_errors"]) or (
        args.require_seam and not motion["seam_pass"]
    )
    return 2 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build immutable 16:10 plates with a deterministic sampled-sky extension."""

from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
ASSET_ROOT = ROOT / "public" / "wallpapers"
TOP_EXTENSION = 104
SAFE_X0 = 400
SAFE_X1 = 1040


def smoothstep(value: float) -> float:
    clamped = min(1.0, max(0.0, value))
    return clamped * clamped * (3.0 - 2.0 * clamped)


def ping_pong(value: int, length: int) -> int:
    period = 2 * length - 2
    wrapped = value % period
    return wrapped if wrapped < length else period - wrapped


def sampled_sky_extension(source: Image.Image) -> Image.Image:
    extension = Image.new("RGBA", (source.width, TOP_EXTENSION))
    source_pixels = source.load()
    target_pixels = extension.load()
    safe_width = SAFE_X1 - SAFE_X0

    for y in range(TOP_EXTENSION):
        sample_y = TOP_EXTENSION - 1 - y
        seam_weight = smoothstep(y / (TOP_EXTENSION - 1)) ** 2
        for x in range(source.width):
            sample_x = SAFE_X0 + ping_pong(x, safe_width)
            base = source_pixels[sample_x, sample_y]
            seam = source_pixels[x, 0]
            target_pixels[x, y] = tuple(
                round(base[channel] + (seam[channel] - base[channel]) * seam_weight)
                for channel in range(4)
            )

    return extension


def process_variant(variant: str) -> None:
    directory = ASSET_ROOT / variant
    source = Image.open(directory / "source.png").convert("RGBA")
    if source.size != (1672, 941):
        raise ValueError(f"Unexpected {variant} source size: {source.size}")

    plate = Image.new("RGBA", (source.width, source.height + TOP_EXTENSION))
    plate.paste(sampled_sky_extension(source), (0, 0))
    plate.paste(source, (0, TOP_EXTENSION))
    plate.save(directory / "plate.png", optimize=True)

    for cloud_layer in directory.glob("cloud-*.png"):
        cloud_layer.unlink()


def main() -> None:
    process_variant("day")
    process_variant("night")


if __name__ == "__main__":
    main()

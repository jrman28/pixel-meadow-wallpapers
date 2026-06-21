#!/usr/bin/env python3
"""Keep one Aerial video active and switch it at local solar events."""

from __future__ import annotations

import datetime as dt
import math
import os
import shutil
import subprocess
from pathlib import Path


LATITUDE = float(os.environ.get("PIXEL_MEADOW_LATITUDE", "34.7304"))
LONGITUDE = float(os.environ.get("PIXEL_MEADOW_LONGITUDE", "-86.5861"))
ACTIVE = Path("/Users/Shared/Aerial/My Videos")
STAGED = Path("/Users/Shared/Aerial/Scheduled Videos")
DAY = "Pixel-Meadow-Day-AI-Seamless-Loop.mp4"
NIGHT = "Pixel-Meadow-Night-AI-Seamless-Loop.mp4"
LOG = Path.home() / "Library/Logs/PixelMeadowWallpaper.log"


def solar_event(date: dt.date, sunrise: bool) -> dt.datetime:
    day = date.timetuple().tm_yday
    longitude_hour = LONGITUDE / 15
    approximate = day + ((6 if sunrise else 18) - longitude_hour) / 24
    anomaly = 0.9856 * approximate - 3.289
    longitude = (
        anomaly
        + 1.916 * math.sin(math.radians(anomaly))
        + 0.020 * math.sin(math.radians(2 * anomaly))
        + 282.634
    ) % 360
    ascension = math.degrees(
        math.atan(0.91764 * math.tan(math.radians(longitude)))
    ) % 360
    ascension += (
        math.floor(longitude / 90) * 90
        - math.floor(ascension / 90) * 90
    )
    ascension /= 15
    sin_declination = 0.39782 * math.sin(math.radians(longitude))
    cos_declination = math.cos(math.asin(sin_declination))
    cos_hour = (
        math.cos(math.radians(90.833))
        - sin_declination * math.sin(math.radians(LATITUDE))
    ) / (cos_declination * math.cos(math.radians(LATITUDE)))
    hour_angle = math.degrees(math.acos(cos_hour))
    if sunrise:
        hour_angle = 360 - hour_angle
    mean_time = hour_angle / 15 + ascension - 0.06571 * approximate - 6.622
    utc_hour = (mean_time - longitude_hour) % 24
    midnight = dt.datetime.combine(date, dt.time(), tzinfo=dt.timezone.utc)
    return midnight + dt.timedelta(hours=utc_hour)


def solar_window(date: dt.date) -> tuple[dt.datetime, dt.datetime]:
    sunrise = solar_event(date, sunrise=True)
    sunset = solar_event(date, sunrise=False)
    if sunset <= sunrise:
        sunset += dt.timedelta(days=1)
    return sunrise, sunset


def write_log(message: str) -> None:
    timestamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    with LOG.open("a") as handle:
        handle.write(f"{timestamp} {message}\n")


def main() -> None:
    now = dt.datetime.now(dt.timezone.utc)
    sunrise, sunset = solar_window(now.date())
    desired = DAY if sunrise <= now < sunset else NIGHT
    inactive = NIGHT if desired == DAY else DAY

    if (ACTIVE / desired).exists() and not (ACTIVE / inactive).exists():
        return

    source = STAGED / desired
    if not source.exists():
        write_log(f"switch skipped: staged file missing: {source}")
        return

    STAGED.mkdir(parents=True, exist_ok=True)
    if (ACTIVE / inactive).exists():
        shutil.move(ACTIVE / inactive, STAGED / inactive)
    shutil.move(source, ACTIVE / desired)
    write_log(
        f"switched to {desired} "
        f"(sunrise={sunrise.isoformat()}, sunset={sunset.isoformat()})"
    )
    subprocess.run(["killall", "Aerial"], check=False)
    subprocess.run(["open", "-a", "Aerial"], check=True)


if __name__ == "__main__":
    main()

#!/bin/zsh

set -euo pipefail

ROOT="${0:A:h:h}"
OUTPUT="$ROOT/out/retail"
DAY_SOURCE="${PIXEL_MEADOW_DAY_SOURCE:-/private/tmp/pixel-meadow-retail/Pixel-Meadow-Day-Dynamic-Wallpaper.mp4}"
NIGHT_SOURCE="${PIXEL_MEADOW_NIGHT_SOURCE:-$HOME/Movies/Wallpapers/Pixel-Meadow-Night-AI-Seamless-Loop.mp4}"

/bin/mkdir -p "$OUTPUT/automation" "$OUTPUT/static"
/bin/cp "$DAY_SOURCE" "$OUTPUT/Pixel-Meadow-Day-Dynamic-Wallpaper.mp4"
/bin/cp "$NIGHT_SOURCE" "$OUTPUT/Pixel-Meadow-Night-Dynamic-Wallpaper.mp4"
/bin/cp "$ROOT/retail/Install Pixel Meadow.command" "$ROOT/retail/Uninstall Pixel Meadow.command" "$ROOT/retail/switch_pixel_meadow.zsh" "$ROOT/retail/PERSONAL_USE_LICENSE.txt" "$OUTPUT/automation/"
/bin/chmod 755 "$OUTPUT/automation/Install Pixel Meadow.command" "$OUTPUT/automation/Uninstall Pixel Meadow.command" "$OUTPUT/automation/switch_pixel_meadow.zsh"
/bin/cp "$ROOT/public/wallpapers/day/source.png" "$OUTPUT/static/Pixel-Meadow-Day-Static.png"
/bin/cp "$ROOT/public/wallpapers/night/source.png" "$OUTPUT/static/Pixel-Meadow-Night-Static.png"

for video in "$OUTPUT"/*.mp4; do
  size=$(/usr/bin/stat -f '%z' "$video")
  (( size < 20000000 )) || { print -u2 "Etsy file limit exceeded: $video ($size bytes)"; exit 1; }
  /opt/homebrew/bin/ffprobe -v error -select_streams v:0 \
    -show_entries stream=codec_name,profile,codec_tag_string,width,height,r_frame_rate,nb_frames \
    -show_entries format=duration -of default=nw=1 "$video"
done

cd "$OUTPUT"
/usr/bin/zip -qr Pixel-Meadow-Automation.zip automation
/usr/bin/zip -qr Pixel-Meadow-Static-Wallpapers.zip static

print "Retail package created at $OUTPUT"

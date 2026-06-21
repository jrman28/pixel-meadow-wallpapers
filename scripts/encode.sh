#!/usr/bin/env bash
set -euo pipefail

mkdir -p out/delivery

for variant in day night; do
  input="out/masters/pixel-meadow-${variant}.mov"
  ffmpeg -y -i "$input" -an -c:v libx265 -preset medium -crf 18 -pix_fmt yuv420p10le -tag:v hvc1 -movflags +faststart "out/delivery/pixel-meadow-${variant}-hevc.mp4"
  ffmpeg -y -i "$input" -an -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -profile:v high -movflags +faststart "out/delivery/pixel-meadow-${variant}-h264.mp4"
done

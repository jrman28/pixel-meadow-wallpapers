#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <input-video> <output-mp4>" >&2
  exit 64
fi

input=$1
output=$2

if [[ ! -f "$input" ]]; then
  echo "Input video not found: $input" >&2
  exit 66
fi

read -r width height < <(
  ffprobe -v error -select_streams v:0 \
    -show_entries stream=width,height \
    -of csv=p=0:s=' ' "$input"
)

crop_width=$((height * 8 / 5))
crop_width=$((crop_width / 2 * 2))

if (( width < crop_width )); then
  echo "Input is narrower than 16:10; this converter only performs centered horizontal crops." >&2
  exit 65
fi

crop_x=$(((width - crop_width) / 2))
mkdir -p "$(dirname "$output")"

ffmpeg -y -i "$input" \
  -vf "crop=${crop_width}:${height}:${crop_x}:0,setpts=2.0*(PTS-STARTPTS),fps=24,scale=2560:1600:flags=neighbor" \
  -an \
  -c:v libx265 \
  -preset medium \
  -crf 18 \
  -pix_fmt yuv420p10le \
  -tag:v hvc1 \
  -movflags +faststart \
  "$output"

ffprobe -v error \
  -show_entries format=duration:stream=codec_type,codec_name,codec_tag_string,width,height,pix_fmt,r_frame_rate \
  -of default=noprint_wrappers=1 \
  "$output"

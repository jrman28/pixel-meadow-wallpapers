#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 <input-video> <output-mp4>" >&2
  exit 64
fi

input=$1
output=$2
crossfade_seconds=${CROSSFADE_SECONDS:-1.5}

if [[ ! -f "$input" ]]; then
  echo "Input video not found: $input" >&2
  exit 66
fi

read -r width height < <(
  ffprobe -v error -select_streams v:0 \
    -show_entries stream=width,height \
    -of csv=p=0:s=' ' "$input"
)

source_duration=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$input")
loop_duration=$(awk -v duration="$source_duration" 'BEGIN { printf "%.6f", duration * 2 }')
crossfade_offset=$(awk -v duration="$loop_duration" -v fade="$crossfade_seconds" 'BEGIN {
  if (fade <= 0 || fade >= duration) exit 1
  printf "%.6f", duration - fade
}') || {
  echo "CROSSFADE_SECONDS must be greater than zero and shorter than the slowed video." >&2
  exit 65
}

crop_width=$((height * 8 / 5))
crop_width=$((crop_width / 2 * 2))

if (( width < crop_width )); then
  echo "Input is narrower than 16:10; this converter only performs centered horizontal crops." >&2
  exit 65
fi

crop_x=$(((width - crop_width) / 2))
mkdir -p "$(dirname "$output")"

ffmpeg -y -i "$input" \
  -filter_complex "[0:v]crop=${crop_width}:${height}:${crop_x}:0,setpts=2.0*(PTS-STARTPTS),fps=24,scale=2560:1600:flags=neighbor,split=2[main][head];[main]trim=start=0:end=${loop_duration},setpts=PTS-STARTPTS[mainloop];[head]trim=start=0:end=${crossfade_seconds},setpts=PTS-STARTPTS[headloop];[mainloop][headloop]xfade=transition=fade:duration=${crossfade_seconds}:offset=${crossfade_offset},format=yuv420p10le[outv]" \
  -map "[outv]" \
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

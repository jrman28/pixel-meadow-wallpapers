#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if [[ -n "${CROSSFADE_SECONDS:-}" ]]; then
  exec python3 "$script_dir/refine_ai_wallpaper.py" \
    --crossfade "$CROSSFADE_SECONDS" "$@"
fi

exec python3 "$script_dir/refine_ai_wallpaper.py" "$@"

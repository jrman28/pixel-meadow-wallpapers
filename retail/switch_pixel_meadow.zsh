#!/bin/zsh

set -u

ACTIVE_DIR="/Users/Shared/Aerial/My Videos"
STAGED_DIR="/Users/Shared/Aerial/Pixel Meadow"
SETTINGS_FILE="/Users/Shared/Aerial/screensaver.json"
DAY_FILE="Pixel-Meadow-Day-Dynamic-Wallpaper.mp4"
NIGHT_FILE="Pixel-Meadow-Night-Dynamic-Wallpaper.mp4"
LOG_FILE="$HOME/Library/Logs/PixelMeadowWallpaper.log"
APPLE_EPOCH_OFFSET=978307200

log_message() {
  /bin/mkdir -p "${LOG_FILE:h}"
  print -r -- "$(/bin/date '+%Y-%m-%dT%H:%M:%S%z') $1" >> "$LOG_FILE"
}

event_time() {
  local key="$1"
  local apple_seconds
  apple_seconds=$(/usr/bin/plutil -extract "time.$key" raw -o - "$SETTINGS_FILE" 2>/dev/null) || return 1
  [[ "$apple_seconds" == <-> ]] || return 1
  /bin/date -r $((apple_seconds + APPLE_EPOCH_OFFSET)) '+%H%M'
}

sunrise="${PIXEL_MEADOW_SUNRISE:-$(event_time cachedNightShiftSunrise 2>/dev/null)}"
sunset="${PIXEL_MEADOW_SUNSET:-$(event_time cachedNightShiftSunset 2>/dev/null)}"

[[ "$sunrise" == <-> ]] || sunrise="0700"
[[ "$sunset" == <-> ]] || sunset="1900"

now=$(/bin/date '+%H%M')
if (( 10#$now >= 10#$sunrise && 10#$now < 10#$sunset )); then
  desired="$DAY_FILE"
  inactive="$NIGHT_FILE"
else
  desired="$NIGHT_FILE"
  inactive="$DAY_FILE"
fi

/bin/mkdir -p "$ACTIVE_DIR" "$STAGED_DIR"

if [[ -f "$ACTIVE_DIR/$desired" && ! -f "$ACTIVE_DIR/$inactive" ]]; then
  exit 0
fi

if [[ -f "$ACTIVE_DIR/$inactive" ]]; then
  /bin/mv "$ACTIVE_DIR/$inactive" "$STAGED_DIR/$inactive"
fi

if [[ -f "$STAGED_DIR/$desired" ]]; then
  /bin/mv "$STAGED_DIR/$desired" "$ACTIVE_DIR/$desired"
elif [[ ! -f "$ACTIVE_DIR/$desired" ]]; then
  log_message "switch skipped: missing $desired"
  exit 1
fi

log_message "switched to $desired (sunrise=$sunrise sunset=$sunset)"
/usr/bin/killall Aerial >/dev/null 2>&1 || true
/bin/sleep 1
/usr/bin/open -a Aerial >/dev/null 2>&1 || true

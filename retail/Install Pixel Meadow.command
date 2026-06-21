#!/bin/zsh

set -euo pipefail

PACKAGE_DIR="${0:A:h}"
SUPPORT_DIR="$HOME/Library/Application Support/QuietPixelStudio/Pixel Meadow"
LAUNCH_AGENT="$HOME/Library/LaunchAgents/com.quietpixelstudio.pixel-meadow.plist"
ACTIVE_DIR="/Users/Shared/Aerial/My Videos"
STAGED_DIR="/Users/Shared/Aerial/Pixel Meadow"
DAY_FILE="Pixel-Meadow-Day-Dynamic-Wallpaper.mp4"
NIGHT_FILE="Pixel-Meadow-Night-Dynamic-Wallpaper.mp4"

fail() {
  /usr/bin/osascript -e "display alert \"Pixel Meadow could not be installed\" message \"$1\" as critical"
  exit 1
}

[[ -d /Applications/Aerial.app ]] || fail "Install and open the free Aerial 4 app first, then run this installer again."
[[ -f "$PACKAGE_DIR/$DAY_FILE" ]] || fail "$DAY_FILE must be in the same folder as this installer."
[[ -f "$PACKAGE_DIR/$NIGHT_FILE" ]] || fail "$NIGHT_FILE must be in the same folder as this installer."

/bin/mkdir -p "$SUPPORT_DIR" "$HOME/Library/LaunchAgents" "$ACTIVE_DIR" "$STAGED_DIR"
/bin/cp "$PACKAGE_DIR/switch_pixel_meadow.zsh" "$SUPPORT_DIR/switch_pixel_meadow.zsh"
/bin/chmod 755 "$SUPPORT_DIR/switch_pixel_meadow.zsh"
/bin/cp "$PACKAGE_DIR/$DAY_FILE" "$STAGED_DIR/$DAY_FILE"
/bin/cp "$PACKAGE_DIR/$NIGHT_FILE" "$STAGED_DIR/$NIGHT_FILE"

cat > "$LAUNCH_AGENT" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.quietpixelstudio.pixel-meadow</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/zsh</string>
    <string>$SUPPORT_DIR/switch_pixel_meadow.zsh</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>300</integer>
  <key>StandardOutPath</key>
  <string>$HOME/Library/Logs/PixelMeadowWallpaper.stdout.log</string>
  <key>StandardErrorPath</key>
  <string>$HOME/Library/Logs/PixelMeadowWallpaper.stderr.log</string>
</dict>
</plist>
PLIST

if [[ -f /Users/Shared/Aerial/screensaver.json ]]; then
  /usr/bin/plutil -replace time.intTimeMode -integer 0 /Users/Shared/Aerial/screensaver.json 2>/dev/null || true
fi

/bin/launchctl bootout "gui/$(/usr/bin/id -u)/com.quietpixelstudio.pixel-meadow" 2>/dev/null || true
/bin/launchctl bootstrap "gui/$(/usr/bin/id -u)" "$LAUNCH_AGENT"
/bin/launchctl kickstart -k "gui/$(/usr/bin/id -u)/com.quietpixelstudio.pixel-meadow"

/usr/bin/osascript -e 'display alert "Pixel Meadow installed" message "Open Aerial, select My Videos, set playback speed to 1.0x, mute audio, and start Wallpaper mode. Day and night will switch within five minutes of sunrise or sunset."'

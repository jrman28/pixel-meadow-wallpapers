#!/bin/zsh

set -u

LABEL="com.quietpixelstudio.pixel-meadow"
LAUNCH_AGENT="$HOME/Library/LaunchAgents/$LABEL.plist"
SUPPORT_DIR="$HOME/Library/Application Support/QuietPixelStudio/Pixel Meadow"
ACTIVE_DIR="/Users/Shared/Aerial/My Videos"
STAGED_DIR="/Users/Shared/Aerial/Pixel Meadow"
BACKUP_DIR="$HOME/Movies/Pixel Meadow Wallpapers"

/bin/launchctl bootout "gui/$(/usr/bin/id -u)/$LABEL" 2>/dev/null || true
/bin/mkdir -p "$BACKUP_DIR"

for file in Pixel-Meadow-Day-Dynamic-Wallpaper.mp4 Pixel-Meadow-Night-Dynamic-Wallpaper.mp4; do
  [[ -f "$ACTIVE_DIR/$file" ]] && /bin/mv "$ACTIVE_DIR/$file" "$BACKUP_DIR/$file"
  [[ -f "$STAGED_DIR/$file" ]] && /bin/mv "$STAGED_DIR/$file" "$BACKUP_DIR/$file"
done

/bin/rm -f "$LAUNCH_AGENT" "$HOME/Library/Logs/PixelMeadowWallpaper.stdout.log" "$HOME/Library/Logs/PixelMeadowWallpaper.stderr.log"
/bin/rm -rf "$SUPPORT_DIR"
/usr/bin/killall Aerial >/dev/null 2>&1 || true
/bin/sleep 1
/usr/bin/open -a Aerial >/dev/null 2>&1 || true

/usr/bin/osascript -e 'display alert "Pixel Meadow automation removed" message "Your wallpaper videos were preserved in Movies/Pixel Meadow Wallpapers."'

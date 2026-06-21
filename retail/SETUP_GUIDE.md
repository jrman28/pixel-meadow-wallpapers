# Pixel Meadow Setup Guide

QuietPixelStudio's day-and-night animated wallpaper pack for Apple Silicon Macs.

## Before you begin

- Apple Silicon Mac (M1 or newer)
- macOS 15 or later
- Free Aerial 4 app from https://aerialscreensaver.github.io/
- Both Pixel Meadow MP4 files and the unzipped automation folder

Aerial is a separate open-source project. QuietPixelStudio is not affiliated
with or endorsed by Aerial.

## Install

1. Install and open Aerial once.
2. Put both MP4 files inside the unzipped Pixel Meadow Automation folder.
3. Control-click **Install Pixel Meadow.command**, choose **Open**, and confirm
   the macOS prompt. The installer does not require an administrator password.
4. In Aerial, select **My Videos**, set playback speed to **1.0x**, mute audio,
   and start **Wallpaper** mode.

The automation checks every five minutes. It keeps exactly one scene active so
each 18.5-second video loops continuously. At sunrise or sunset, it swaps the
active scene and restarts Aerial once.

## Recommended Aerial settings

- Filter: My Videos
- Playback speed: 1.0x
- Audio: muted
- Wallpaper: enabled
- Pause on battery or fullscreen: your preference
- Native Aerial time filtering: disabled by the installer

## If macOS blocks the installer

The included installer is an unsigned shell script, not a notarized Mac app.
Control-click the file and choose **Open**. If macOS still blocks it, open
System Settings > Privacy & Security and choose **Open Anyway** for the Pixel
Meadow installer. Never bypass a warning for a file obtained outside your Etsy
download.

## Troubleshooting

### The wallpaper is moving too slowly

Set Aerial's playback speed to 1.0x. The slower motion is already encoded into
the video.

### The screen flashes black every 18.5 seconds

Only one Pixel Meadow file should be in `/Users/Shared/Aerial/My Videos/`.
Run the installer again to restore the single-active-file configuration.

### The wrong scene is active

Confirm macOS date and time are set automatically, open Aerial once, and wait
up to five minutes. If Aerial has not cached sunrise/sunset data, Pixel Meadow
uses 7:00 AM and 7:00 PM as safe defaults.

### Aerial says no video is available

Open Aerial's Video Library and select My Videos. If neither Pixel Meadow file
appears, run the installer again with both MP4 files beside it.

## Remove the automation

Control-click **Uninstall Pixel Meadow.command** and choose **Open**. The
automation and LaunchAgent are removed. Your two MP4 files are preserved in
`~/Movies/Pixel Meadow Wallpapers/`.

## Support information

When requesting help, include your Mac model, macOS version, Aerial version,
and a screenshot of the issue. Do not send passwords or private system data.

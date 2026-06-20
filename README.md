# Pixel Meadow Wallpapers

A reproducible workflow for converting AI-animated pixel-art scenes into quiet, silent macOS video wallpapers.

## Current status

- **Night:** finished and installed locally as a 2560×1600, 24 fps, 20-second HEVC Main10 wallpaper.
- **Day:** source artwork only. The failed experimental day renders were removed; the image will be animated with the same AI-to-FFmpeg workflow later.

The original day and night artwork remains under `public/wallpapers/*/source.png`. The Remotion code in `src/` is retained as an experimental motion prototype, but it is not the source of the delivered night wallpaper.

## Convert an AI animation

Requirements: FFmpeg with `libx265` and FFprobe.

```bash
./scripts/convert_ai_wallpaper.sh input.mp4 output.mp4
```

The converter applies the approved delivery recipe:

- centered 16:10 crop;
- half-speed playback with source frames preserved;
- 2560×1600 at 24 fps;
- silent HEVC Main10 with the macOS-compatible `hvc1` tag;
- nearest-neighbor scaling for pixel-art edges;
- CRF 18 with fast-start metadata.

The output intentionally contains no audio stream. Generated videos live outside Git or under the ignored `out/` directory.

## Use on macOS

[Aerial 4](https://aerialscreensaver.github.io/) is the recommended player. Copy the finished MP4 into:

```text
/Users/Shared/Aerial/My Videos/
```

Then open Aerial’s menu-bar interface, filter to **My Videos**, choose the wallpaper, and enable **Wallpaper** mode. Aerial can auto-pause when the desktop is covered to reduce battery and GPU use.

For the intended motion, set Aerial's global playback speed to **1.0×**. The video is already slowed by FFmpeg, so applying Aerial's default `0.125×` speed makes it eight times too slow. Disable **Pause when wallpaper is hidden** if the animation should keep running continuously behind application windows.

## Development checks

The earlier Remotion prototype remains available for reference:

```bash
npm install
npm test
npm run lint
npm run build
```

# Pixel Meadow Wallpapers

A reproducible workflow for converting AI-animated pixel-art scenes into quiet, silent macOS video wallpapers.

## Current status

- **Night:** delivered as an 18.5-second, 444-frame HEVC Main10 loop at the approved motion speed.
- **Day:** delivered from the approved 10-second generation with the same
  18.5-second, 444-frame specification as night.
- **Automation:** A lightweight solar scheduler keeps one video active in Aerial
  and switches at Huntsville sunrise/sunset.

The original day and night artwork remains under `public/wallpapers/*/source.png`. The Remotion code in `src/` is retained as an experimental motion prototype, but it is not the source of the delivered night wallpaper.

## Convert an AI animation

Requirements: FFmpeg with `libx265` and FFprobe.

```bash
python3 scripts/refine_ai_wallpaper.py input.mp4 output.mp4
```

The converter applies the approved delivery recipe:

- centered 16:10 crop;
- configurable slowdown (default: 2× duration / half-speed motion);
- a 1.5-second end-to-start crossfade for a softer seamless loop;
- 2560×1600 at 24 fps;
- silent HEVC Main10 with the macOS-compatible `hvc1` tag;
- nearest-neighbor scaling for pixel-art edges;
- CRF 18 with fast-start metadata.

The output intentionally contains no audio stream. Generated videos live outside Git or under the ignored `out/` directory.

Preview quickly before a production encode:

```bash
python3 scripts/refine_ai_wallpaper.py input.mp4 preview.mp4 --mode preview
```

The original converter path remains a backward-compatible wrapper. Use `--dry-run`
to inspect duration, frame, crop, and filter calculations without encoding.

Analyze any candidate independently:

```bash
python3 scripts/analyze_loop.py output.mp4 --require-seam
```

See [the refinement runbook](docs/WALLPAPER_REFINEMENT.md) for source preflight,
three-loop review, production validation, Aerial installation, and rollback.

## Use on macOS

[Aerial 4](https://aerialscreensaver.github.io/) is the recommended player. Copy the finished MP4 into:

```text
/Users/Shared/Aerial/My Videos/
```

Then open Aerial’s menu-bar interface, filter to **My Videos**, choose the wallpaper, and enable **Wallpaper** mode.

For the intended motion, set Aerial's global playback speed to **1.0×**. The video is already slowed by FFmpeg, so applying Aerial's default `0.125×` speed makes it eight times too slow. Disable **Pause when wallpaper is hidden** if the animation should keep running continuously behind application windows.

Do not leave day and night together in Aerial's active **My Videos** folder.
Aerial treats two files as a rotating playlist and reloads its player at every
18.5-second boundary, producing a black flash. See
[Automatic day/night switching](docs/WALLPAPER_REFINEMENT.md#automatic-daynight-switching)
for the single-active-file scheduler.

## Development checks

The earlier Remotion prototype remains available for reference:

```bash
npm install
npm test
npm run test:pipeline
npm run lint
npm run build
```

## Retail package

The Etsy-ready product uses Aerial as the playback engine and a portable zsh
scheduler to keep one wallpaper active at a time. Aerial's native time filter
was tested and rejected because it reloads a two-video local playlist at each
18.5-second boundary (`shouldLoop=false`), which can create a black flash.

Build the customer guide and five delivery files with:

```bash
python3 scripts/build_setup_guide.py
./scripts/build_retail_package.sh
```

Outputs are written to the ignored `out/retail/` directory. See
[`docs/ETSY_LAUNCH.md`](docs/ETSY_LAUNCH.md) for listing copy, tags, disclosure
language, image prompts, and the clean-account launch gate.

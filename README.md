# Pixel Meadow Wallpapers

Two seamless, silent pixel-art video wallpapers built with Remotion and a deterministic WebGL motion system.

## Compositions

- `PixelMeadow-Day` — localized cloud drift and a rooted foreground breeze
- `PixelMeadow-Night` — the same motion system plus restrained star twinkle and moon glow

Both compositions render at 2560×1600, 30 fps, and loop every 24 seconds.

## Development

```bash
npm install
npm run prepare:assets
npm test
npm run lint
npm run dev
```

The original PNGs remain immutable under `public/wallpapers/*/source.png`. The preparation script extends them to 16:10 using sampled sky texture, preserves every original pixel at a fixed offset, and writes derived `plate.png` files.

## Rendering

```bash
npm run render:posters
npm run render:masters
npm run encode
```

Outputs are written to `out/`:

- `masters/` — ProRes 422 HQ masters
- `delivery/*-hevc.mp4` — silent HEVC Main10 with `hvc1` compatibility
- `delivery/*-h264.mp4` — silent H.264 fallbacks
- `posters/` — static day and night posters

Import the HEVC files into a macOS video-wallpaper utility such as Vidwall. Use H.264 only if the player does not accept Main10 HEVC.

## Motion design

- The intact plate is sampled through one WebGL shader; no clouds are extracted or inpainted.
- Soft elliptical UV influence fields move clouds by approximately 6–18 output pixels without holes or rectangular patches.
- Grass roots remain fixed while two spatial wind waves move the foreground tips with 6- and 12-second periods.
- Nearest-neighbor sampling, disabled mipmaps, and integer-pixel displacement preserve pixel-art edges.
- Every animation is derived from the Remotion frame number and repeats exactly every 720 frames.

## Verification

```bash
npm test
npm run lint
npm run build
```

The motion tests cover exact loop periodicity, rooted grass influence, cloud depth and bounds, localized cloud falloff, and restrained night luminance.

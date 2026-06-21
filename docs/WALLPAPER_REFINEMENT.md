# AI Wallpaper Refinement Runbook

This workflow begins with a user-approved AI animation. It does not generate
motion. Remotion remains an experiment and is not part of delivery.

## Delivery contract

- 2560×1600, 24 fps
- HEVC Main10, `hvc1`, CRF 18
- no audio stream
- centered 16:10 crop unless an explicit `--crop-x` is approved
- nearest-neighbor output scaling
- frame-quantized slowdown, trim, and cyclic blend
- seam analysis is diagnostic; a visually approved three-loop review is final

Expected duration is:

```text
round(source seconds × slowdown × 24) / 24 − round(crossfade seconds × 24) / 24
```

The default slowdown is 2× and the default crossfade is 1.5 seconds.

## Immutable source policy

Copy the approved clip to durable storage and never overwrite it. Record its
duration and hash before refinement.

Do not infer an approved duration from an earlier generation. Probe every new
source and confirm the full accepted range. The delivered daytime source is a
new, fully approved 10-second generation; it is unrelated to the earlier
6.5-second partial clip.

Reject an AI-motion source before encoding if three-loop inspection shows:

- camera pan, zoom, rotation, or framing drift;
- geometry morphing or unstable trees, hills, sun, or moon;
- pixel smearing, crawling edges, or invented details;
- unacceptable grass direction, cloud motion, flashes, or speed changes.

Encoding cannot repair those defects.

## 1. Inspect and plan

```bash
ffprobe -v error -show_streams -show_format -of json approved-source.mp4
python3 scripts/refine_ai_wallpaper.py approved-source.mp4 candidate.mp4 --dry-run
```

The dry run reports detected source duration and dimensions, crop, exact frame
counts, expected duration, and the FFmpeg filter graph. For a non-centered crop,
pass an even pixel offset such as `--crop-x 96`.

## 2. Create a fast preview

```bash
python3 scripts/refine_ai_wallpaper.py approved-source.mp4 preview.mp4 --mode preview
ffmpeg -y -stream_loop 2 -i preview.mp4 -t 55.5 -an -c copy preview-three-loops.mp4
```

Replace `34.5` with three times the reported output duration. Review every
restart at normal playback speed. Stop if there is a tick, flash, pause, speed
change, excessive dissolve ghosting, or a source defect.

## 3. Encode production

```bash
python3 scripts/refine_ai_wallpaper.py approved-source.mp4 wallpaper.mp4 --mode production
```

For the night wallpaper, the input is already the untouched approved 20-second
slowed master, so preserve its pacing:

```bash
python3 scripts/refine_ai_wallpaper.py night-20s-slowed-master.mp4 night-loop.mp4 \
  --slowdown 1 --crossfade 1.5 --mode production
```

The approved 10-second daytime clip uses the defaults:

```bash
python3 scripts/refine_ai_wallpaper.py day-approved-10s.mp4 day-loop.mp4 \
  --slowdown 2 --crossfade 1.5 --mode production
```

After explicit three-loop visual approval, add `--visual-approval` so metadata
remains blocking while seam scoring is informational. Do not redesign the
analyzer or create extra encodes to satisfy a metric when the loop looks right.
Each encode writes a sibling `.analysis.json` report.

## 4. Verify independently

```bash
python3 scripts/analyze_loop.py wallpaper.mp4 \
  --expected-frames 444 --expect-production --require-seam
```

Both delivered wallpapers use 444 frames. The analyzer reports codec,
dimensions through metadata validation, frame count, motion percentiles,
anomaly frames, seam ratio, and audio violations.

Review a three-loop production preview before installation. Automated metrics
are a gate, not a substitute for watching the loop on the target display.
Motion deltas use a one-pixel low-pass analysis image so HEVC intra/inter-frame
noise is not mistaken for scene motion; actual restart jumps remain detectable.

## 5. Install one wallpaper in Aerial

1. Keep the currently installed MP4 in `~/Movies/Wallpapers` as rollback.
2. Keep exactly one MP4 in `/Users/Shared/Aerial/My Videos/`.
3. Keep inactive scheduled videos in
   `/Users/Shared/Aerial/Scheduled Videos/`.
4. Set global playback speed to **1.0×**; slowdown is already baked in.
5. Keep playback muted. Configure launch-at-login and battery/fullscreen pause
   behavior deliberately.
6. Restart Aerial and confirm its log reports `loop=true`,
   `shouldLoop=true`, and `Looping mode`.

If playback stalls or speed is wrong, restore the previous selection/file and
inspect Aerial's configuration and logs before re-encoding. A playback setting
problem must not be “fixed” by changing source timing.

## Automatic day/night switching

Aerial's native time filtering must not be used with these two short local
videos. With both files in **My Videos**, Aerial constructs a two-entry rotating
playlist and sets `shouldLoop=false`. It tears down and reloads its player every
18.5 seconds, which creates a black flash even when time filtering selects the
same video again.

Use the repository scheduler instead. The installed personal workflow uses the
original Python scheduler; the retail package uses the dependency-free zsh
scheduler under `retail/`:

1. Put the current video in **My Videos** and the inactive video in
   **Scheduled Videos**.
2. Copy `scripts/switch_wallpaper.py` to
   `~/Library/Application Support/Pixel Meadow/`.
3. Copy the LaunchAgent template from `config/` to `~/Library/LaunchAgents/`.
4. Disable Aerial's native time mode and bootstrap the LaunchAgent.

The LaunchAgent wakes every five minutes and exits immediately unless a solar
boundary has crossed. At sunrise or sunset it swaps the files and restarts
Aerial once. Default coordinates are Huntsville, Alabama; override them through
`PIXEL_MEADOW_LATITUDE` and `PIXEL_MEADOW_LONGITUDE` in the LaunchAgent
environment for another location.

For customers, `Install Pixel Meadow.command` installs a zsh LaunchAgent that
reads Aerial's cached Night Shift sunrise and sunset times, falls back to
7:00 AM/7:00 PM when unavailable, and requires no Python installation. The
included uninstaller preserves both purchased videos in the user's Movies
folder.

## Bounded refinement policy

- One preview, one three-loop visual review, and one production encode.
- At most one corrective preview for a named visible defect.
- Never tune codecs, filters, or analyzers after visual approval.
- Do not run Remotion, procedural animation, or unrelated repository work.
- If the AI motion itself is defective, report its timestamp and stop.
- Validate only dimensions, frame rate/count, duration, codec/tag, and no audio.

### Delivered reference

| Scene | Approved input | Slowdown | Blend | Output |
| --- | --- | --- | --- | --- |
| Night | 20-second already-slowed master | 1× | 1.5 s | 18.5 s / 444 frames |
| Day | 10-second AI generation | 2× | 1.5 s | 18.5 s / 444 frames |

## Development checks

```bash
npm test
npm run test:pipeline
npm run lint
npm run build
bash -n scripts/convert_ai_wallpaper.sh
git diff --check
```

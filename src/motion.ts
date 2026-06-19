export const FPS = 30;
export const LOOP_FRAMES = 24 * FPS;

const TAU = Math.PI * 2;

const normalizedFrame = (frame: number) => {
  const wrapped = ((frame % LOOP_FRAMES) + LOOP_FRAMES) % LOOP_FRAMES;
  return wrapped / LOOP_FRAMES;
};

const smoothstep = (edge0: number, edge1: number, value: number) => {
  const t = Math.min(1, Math.max(0, (value - edge0) / (edge1 - edge0)));
  return t * t * (3 - 2 * t);
};

export const grassDisplacementPx = (
  frame: number,
  xNormalized: number,
  yNormalized: number,
) => {
  const rootedBand =
    smoothstep(0.02, 0.13, yNormalized) *
    (1 - smoothstep(0.3, 0.4, yNormalized));
  if (rootedBand === 0) return 0;

  const progress = normalizedFrame(frame);
  const sixSecondWave = Math.sin(TAU * 4 * progress + xNormalized * 11.5);
  const twelveSecondWave = Math.sin(TAU * 2 * progress + xNormalized * 5.25 + 0.8);
  const displacement =
    8 * rootedBand * (sixSecondWave * 0.68 + twelveSecondWave * 0.32);

  return Math.round(displacement);
};

export const cloudDisplacementPx = (
  frame: number,
  index: number,
  depth: number,
) => {
  const clampedDepth = Math.min(1, Math.max(0, depth));
  const progress = normalizedFrame(frame);
  const phase = TAU * progress + index * 0.73;
  const amplitude = 6 + clampedDepth * 12;

  return {
    x: Math.round(Math.sin(phase) * amplitude),
    y: Math.round(Math.sin(phase * 2 + index * 0.41) * (0.75 + clampedDepth * 1.25)),
  };
};

export const cloudInfluence = (ellipseX: number, ellipseY: number) => {
  const distance = Math.hypot(ellipseX, ellipseY);
  return 1 - smoothstep(0.72, 1, distance);
};

export const starTwinkle = (frame: number, index: number) => {
  const progress = normalizedFrame(frame);
  const cycleCount = 2 + (index % 3);
  const wave = 0.5 + 0.5 * Math.sin(TAU * cycleCount * progress + index * 1.17);
  return 0.72 + wave * 0.28;
};

export const moonGlow = (frame: number) => {
  const progress = normalizedFrame(frame);
  return 0.99 + Math.sin(TAU * progress) * 0.03;
};

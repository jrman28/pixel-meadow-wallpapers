export type CloudSpec = {
  readonly x: number;
  readonly y: number;
  readonly width: number;
  readonly height: number;
  readonly depth: number;
};

export const PLATE_WIDTH = 1672;
export const PLATE_HEIGHT = 1045;
export const TOP_EXTENSION = 104;

const boxes = [
  [35, 102, 318, 220, 0.8], [202, 224, 486, 332, 0.72],
  [34, 324, 246, 410, 0.48], [390, 386, 558, 458, 0.36],
  [1042, 404, 1248, 480, 0.38], [1307, 312, 1522, 393, 0.55],
  [1421, 207, 1634, 318, 0.78], [1432, 447, 1614, 528, 0.42],
  [1277, 510, 1414, 573, 0.24], [576, 501, 713, 563, 0.22],
  [376, 500, 509, 562, 0.2],
] as const;

export const CLOUDS: readonly CloudSpec[] = boxes.map(
  ([x0, y0, x1, y1, depth]) => ({
    x: x0,
    y: y0 + TOP_EXTENSION,
    width: x1 - x0,
    height: y1 - y0,
    depth,
  }),
);

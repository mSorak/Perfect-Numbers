/** Baseline (Maryland) and categorical colors for selected geographies. */

export const BASELINE_RGB: [number, number, number] = [87, 83, 78];

const PALETTE: Array<[number, number, number]> = [
  [194, 65, 12],
  [13, 148, 136],
  [124, 58, 237],
  [217, 119, 6],
  [37, 99, 235],
  [190, 24, 93],
  [5, 150, 105],
  [79, 70, 229],
  [220, 38, 38],
  [21, 128, 61],
];

export function colorForSelection(
  isBaseline: boolean,
  indexAmongOthers: number,
): [number, number, number] {
  if (isBaseline) return BASELINE_RGB;
  return PALETTE[indexAmongOthers % PALETTE.length];
}

export function colorCss(rgb: [number, number, number], alpha = 1): string {
  return alpha < 1
    ? `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${alpha})`
    : `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
}

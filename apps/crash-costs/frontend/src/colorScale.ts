import { CHOROPLETH_RAMP } from "./config";

export type RGBA = [number, number, number, number];

export interface Scale {
  breaks: number[];
  colors: Array<[number, number, number]>;
  min: number;
  max: number;
}

/**
 * Build a quantile-based color scale from the set of non-null values. Falls
 * back to an equal-interval scale when there is not enough variance.
 */
export function buildQuantileScale(values: number[]): Scale | null {
  const cleaned = values.filter((v) => v !== null && v !== undefined && !Number.isNaN(v));
  if (cleaned.length === 0) return null;
  cleaned.sort((a, b) => a - b);

  const ramp = CHOROPLETH_RAMP;
  const n = ramp.length;
  const breaks: number[] = [];
  for (let i = 1; i < n; i++) {
    const q = i / n;
    const idx = Math.min(cleaned.length - 1, Math.floor(q * cleaned.length));
    breaks.push(cleaned[idx]);
  }
  return {
    breaks,
    colors: ramp,
    min: cleaned[0],
    max: cleaned[cleaned.length - 1],
  };
}

export function colorFor(value: number | null | undefined, scale: Scale | null, alpha = 180): RGBA {
  if (scale === null || value === null || value === undefined || Number.isNaN(value)) {
    return [200, 200, 200, 40];
  }
  let bucket = scale.colors.length - 1;
  for (let i = 0; i < scale.breaks.length; i++) {
    if (value <= scale.breaks[i]) {
      bucket = i;
      break;
    }
  }
  const [r, g, b] = scale.colors[bucket];
  return [r, g, b, alpha];
}

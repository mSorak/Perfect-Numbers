import type { Level } from "./types";

export const MARYLAND_INITIAL_VIEW = {
  longitude: -76.8,
  latitude: 39.0,
  zoom: 7,
  pitch: 0,
  bearing: 0,
};

/**
 * Zoom thresholds for switching between geographic summary levels and for
 * revealing individual crash points. Tuned for Maryland; adjust here to
 * change the entire zoom UX in one place.
 */
export const ZOOM = {
  countyMin: 0,
  countyMax: 8.5,
  placeMin: 8.5,
  placeMax: 11,
  tractMin: 11,
  crashesMin: 11.5,
  crashesMax: 22,
};

export function levelForZoom(zoom: number): Level {
  if (zoom < ZOOM.countyMax) return "county";
  if (zoom < ZOOM.placeMax) return "place";
  return "tract";
}

/**
 * Basemap styles. OpenFreeMap vector tiles are free to use without an API
 * key and include the three style variants below. Swap in any MapLibre
 * style URL to add more options.
 */
export const BASEMAPS = [
  { id: "positron", label: "Positron (light)", url: "https://tiles.openfreemap.org/styles/positron" },
  { id: "bright", label: "Bright", url: "https://tiles.openfreemap.org/styles/bright" },
  { id: "liberty", label: "Liberty", url: "https://tiles.openfreemap.org/styles/liberty" },
];

export const DEFAULT_BASEMAP = BASEMAPS[0].id;

export const CRASH_TYPE_COLORS: Record<string, [number, number, number]> = {
  fatal: [220, 38, 38],
  injury: [234, 88, 12],
  property_damage: [37, 99, 235],
};

export const CHOROPLETH_RAMP: Array<[number, number, number]> = [
  [255, 247, 236],
  [254, 232, 200],
  [253, 212, 158],
  [253, 187, 132],
  [252, 141, 89],
  [239, 101, 72],
  [215, 48, 31],
  [153, 0, 0],
];

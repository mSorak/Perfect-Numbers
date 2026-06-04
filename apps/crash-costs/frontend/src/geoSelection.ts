import type { GeoLevel, SelectedGeo } from "./types";

export const MARYLAND_STATE_GEOID = "24";

export const MARYLAND_BASELINE: SelectedGeo = {
  key: "state:24",
  level: "state",
  geoid: MARYLAND_STATE_GEOID,
  name: "Maryland",
};

export function selectionKey(level: GeoLevel, geoid: string): string {
  return `${level}:${geoid}`;
}

export function parseSelectionKey(key: string): { level: GeoLevel; geoid: string } | null {
  const idx = key.indexOf(":");
  if (idx <= 0) return null;
  const level = key.slice(0, idx) as GeoLevel;
  const geoid = key.slice(idx + 1);
  if (!geoid) return null;
  if (level !== "state" && level !== "county" && level !== "place" && level !== "tract") {
    return null;
  }
  return { level, geoid };
}

export function levelLabel(level: GeoLevel): string {
  switch (level) {
    case "state":
      return "State";
    case "county":
      return "County";
    case "place":
      return "CDP / Place";
    case "tract":
      return "Census tract";
  }
}

export function makeSelection(
  level: GeoLevel,
  geoid: string,
  name: string,
): SelectedGeo {
  return { key: selectionKey(level, geoid), level, geoid, name };
}

export function isSameSelection(a: SelectedGeo, b: SelectedGeo): boolean {
  return a.key === b.key;
}

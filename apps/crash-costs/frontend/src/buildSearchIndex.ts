import type { GeoLevel, Level } from "./types";
import { makeSelection } from "./geoSelection";

export interface SearchEntry {
  key: string;
  level: GeoLevel;
  geoid: string;
  name: string;
  searchText: string;
}

const SEARCH_LEVELS: Level[] = ["county", "place"];

export function buildSearchIndex(
  geoByLevel: Partial<Record<Level, GeoJSON.FeatureCollection>>,
): SearchEntry[] {
  const entries: SearchEntry[] = [];

  for (const level of SEARCH_LEVELS) {
    const geo = geoByLevel[level];
    if (!geo) continue;
    for (const feat of geo.features) {
      const props = feat.properties as { GEOID?: string; name?: string; NAMELSAD?: string };
      const geoid = props?.GEOID;
      if (!geoid) continue;
      const name = props?.name ?? props?.NAMELSAD ?? geoid;
      const sel = makeSelection(level, String(geoid), String(name));
      entries.push({
        key: sel.key,
        level,
        geoid: sel.geoid,
        name: sel.name,
        searchText: String(name).toLowerCase(),
      });
    }
  }

  entries.sort((a, b) => a.name.localeCompare(b.name));
  return entries;
}

export function searchGeographies(query: string, index: SearchEntry[], limit = 12): SearchEntry[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return index.filter((e) => e.searchText.includes(q)).slice(0, limit);
}

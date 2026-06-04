import { computeMetricValue } from "./metrics";
import type { GeoLevel, MetricDef, SummaryFeature, SummaryResponse } from "./types";

export type SummaryCache = Partial<Record<GeoLevel, Map<string, SummaryFeature>>>;

export function normalizeGeoid(geoid: string | number | null | undefined): string | null {
  if (geoid === null || geoid === undefined) return null;
  const s = String(geoid).trim();
  return s.length > 0 ? s : null;
}

export function enrichFeature(
  feature: SummaryFeature,
  metric: MetricDef | undefined,
): SummaryFeature {
  const geoid = normalizeGeoid(feature.geoid);
  if (!geoid) return feature;
  const value =
    metric !== undefined ? computeMetricValue(metric, feature) : (feature.value ?? null);
  return { ...feature, geoid, value };
}

export function buildSummaryCache(
  responses: SummaryResponse[],
  metric: MetricDef | undefined,
): SummaryCache {
  const cache: SummaryCache = {};
  for (const resp of responses) {
    const map = new Map<string, SummaryFeature>();
    for (const raw of resp.features ?? []) {
      const geoid = normalizeGeoid(raw.geoid);
      if (!geoid) continue;
      map.set(geoid, enrichFeature(raw, metric));
    }
    cache[resp.level] = map;
  }
  return cache;
}

export function lookupSummary(
  cache: SummaryCache,
  level: GeoLevel,
  geoid: string | number | null | undefined,
): SummaryFeature | undefined {
  const key = normalizeGeoid(geoid);
  if (!key) return undefined;
  return cache[level]?.get(key);
}

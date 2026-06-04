import type { CrashType, Filters, SelectedGeo } from "./types";
import { MARYLAND_BASELINE, parseSelectionKey } from "./geoSelection";

const GEO_PARAM = "geos";

export function encodeGeosInUrl(selections: SelectedGeo[]): string {
  if (selections.length === 0) return "";
  return selections.map((s) => s.key).join("|");
}

export function decodeGeosFromUrl(
  raw: string | null,
  nameResolver: (level: string, geoid: string) => string | null,
): SelectedGeo[] {
  if (!raw?.trim()) return [MARYLAND_BASELINE];
  const parts = raw.split("|").filter(Boolean);
  const out: SelectedGeo[] = [];
  for (const part of parts) {
    const parsed = parseSelectionKey(part);
    if (!parsed) continue;
    const name = nameResolver(parsed.level, parsed.geoid) ?? parsed.geoid;
    out.push({
      key: part,
      level: parsed.level,
      geoid: parsed.geoid,
      name,
    });
  }
  return out.length > 0 ? out : [MARYLAND_BASELINE];
}

export function readFiltersFromUrl(search: URLSearchParams): Partial<Filters> {
  const partial: Partial<Filters> = {};
  const metric = search.get("metric");
  if (metric) partial.metric = metric;
  const from = search.get("from");
  const to = search.get("to");
  if (from) partial.dateFrom = from;
  if (to) partial.dateTo = to;
  const types = search.get("types");
  if (types) partial.crashTypes = types.split(",").filter(Boolean) as CrashType[];
  if (search.get("nm") === "1") partial.nonmotoristInvolved = true;
  return partial;
}

export function writeUrlState(selections: SelectedGeo[], filters: Filters): void {
  const params = new URLSearchParams(window.location.search);
  const geos = encodeGeosInUrl(selections);
  if (geos) params.set(GEO_PARAM, geos);
  else params.delete(GEO_PARAM);
  params.set("metric", filters.metric);
  if (filters.dateFrom) params.set("from", filters.dateFrom);
  else params.delete("from");
  if (filters.dateTo) params.set("to", filters.dateTo);
  else params.delete("to");
  if (filters.crashTypes.length) params.set("types", filters.crashTypes.join(","));
  else params.delete("types");
  if (filters.nonmotoristInvolved) params.set("nm", "1");
  else params.delete("nm");
  const qs = params.toString();
  const url = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
  window.history.replaceState(null, "", url);
}

export function getGeosParam(): string | null {
  return new URLSearchParams(window.location.search).get(GEO_PARAM);
}

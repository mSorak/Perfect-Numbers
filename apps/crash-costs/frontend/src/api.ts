import type { FilterArgs } from "./filterArgs";
import type {
  CrashesResponse,
  GeoLevel,
  Level,
  Metadata,
  SummaryResponse,
} from "./types";

export type { FilterArgs };

const API_BASE = ""; // Vite dev server proxies /api → FastAPI.

function qs(params: Record<string, string | number | boolean | undefined>): string {
  const parts: string[] = [];
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === "" || v === null || v === false) continue;
    parts.push(`${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`);
  }
  return parts.length ? "?" + parts.join("&") : "";
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`GET ${path} failed: ${res.status} ${res.statusText}`);
  }
  return (await res.json()) as T;
}

export async function fetchMetadata(): Promise<Metadata> {
  return getJSON<Metadata>("/api/metadata");
}

export async function fetchGeo(level: Level): Promise<GeoJSON.FeatureCollection> {
  return getJSON<GeoJSON.FeatureCollection>(`/api/geo/${level}`);
}

export async function fetchSummary(
  level: GeoLevel,
  metric: string,
  filters: FilterArgs,
): Promise<SummaryResponse> {
  const path =
    level === "state"
      ? `/api/summary/state${qs({
          metric,
          date_from: filters.dateFrom,
          date_to: filters.dateTo,
          crash_types: filters.crashTypes?.join(","),
          nonmotorist: filters.nonmotoristInvolved ? true : undefined,
        })}`
      : `/api/summary/${level}${qs({
          metric,
          date_from: filters.dateFrom,
          date_to: filters.dateTo,
          crash_types: filters.crashTypes?.join(","),
          nonmotorist: filters.nonmotoristInvolved ? true : undefined,
        })}`;
  return getJSON<SummaryResponse>(path);
}

export async function fetchCrashes(
  bbox: { west: number; south: number; east: number; north: number },
  filters: FilterArgs,
  limit = 50000,
): Promise<CrashesResponse> {
  const path = `/api/crashes${qs({
    west: bbox.west,
    south: bbox.south,
    east: bbox.east,
    north: bbox.north,
    date_from: filters.dateFrom,
    date_to: filters.dateTo,
    crash_types: filters.crashTypes?.join(","),
    nonmotorist: filters.nonmotoristInvolved ? true : undefined,
    limit,
  })}`;
  return getJSON<CrashesResponse>(path);
}

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { buildSearchIndex, type SearchEntry } from "./buildSearchIndex";
import { ComparisonDashboard } from "./components/ComparisonDashboard";
import { CrashDetailCard } from "./components/CrashDetailCard";
import { FilterBar } from "./components/FilterBar";
import { Legend } from "./components/Legend";
import { MapView, type GeoClickPayload } from "./components/MapView";
import { ProsePage } from "./components/ProsePage";
import { SiteFooter } from "./components/SiteFooter";
import { SiteHeader, type SiteTab } from "./components/SiteHeader";
import { StatusPanel } from "./components/StatusPanel";
import { aboutContent } from "./content/about";
import { methodologyContent } from "./content/methodology";
import { siteContent } from "./content/site";
import { colorForSelection } from "./geoColors";
import {
  MARYLAND_BASELINE,
  MARYLAND_STATE_GEOID,
  makeSelection,
} from "./geoSelection";
import type {
  CrashPoint,
  Filters,
  GeoLevel,
  Level,
  Metadata,
  SelectedGeo,
  SummaryFeature,
} from "./types";
import { BASEMAPS, DEFAULT_BASEMAP, ZOOM, levelForZoom } from "./config";
import { fetchCrashes, fetchGeo, fetchMetadata, fetchSummary } from "./api";
import type { Scale } from "./colorScale";
import { buildFilterArgs, filterArgsKey, isDateRangeInvalid } from "./filterArgs";
import { buildSummaryCache, type SummaryCache } from "./summaryCache";
import { decodeGeosFromUrl, getGeosParam, readFiltersFromUrl, writeUrlState } from "./urlState";

type GeoByLevel = Partial<Record<Level, GeoJSON.FeatureCollection>>;

const DEFAULT_FILTERS: Filters = {
  dateFrom: "",
  dateTo: "",
  crashTypes: [],
  nonmotoristInvolved: false,
  metric: "comprehensive_cost_per_capita",
};

const MAX_SELECTIONS = 10;
const DASHBOARD_LEVELS: GeoLevel[] = ["state", "county", "place", "tract"];

export function App() {
  const [activeTab, setActiveTab] = useState<SiteTab>("map");
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const [filters, setFilters] = useState<Filters>(() => ({
    ...DEFAULT_FILTERS,
    ...readFiltersFromUrl(new URLSearchParams(window.location.search)),
  }));
  const [basemapId, setBasemapId] = useState<string>(DEFAULT_BASEMAP);
  const [geoByLevel, setGeoByLevel] = useState<GeoByLevel>({});
  const [summaryCache, setSummaryCache] = useState<SummaryCache>({});
  const [crashes, setCrashes] = useState<CrashPoint[]>([]);
  const [zoom, setZoom] = useState(7);
  const [bbox, setBbox] = useState<[number, number, number, number]>([-79.6, 37.8, -74.9, 39.8]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scale, setScale] = useState<Scale | null>(null);
  const [selections, setSelections] = useState<SelectedGeo[]>([MARYLAND_BASELINE]);
  const [pulseKey, setPulseKey] = useState<string | null>(null);
  const [selectedCrash, setSelectedCrash] = useState<CrashPoint | null>(null);

  const urlSelectionsInit = useRef(false);

  useEffect(() => {
    document.title = siteContent.documentTitle;
  }, []);

  useEffect(() => {
    if (activeTab !== "map") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  }, [activeTab]);

  const filterArgs = useMemo(() => buildFilterArgs(filters), [filters]);
  const filterKey = filterArgsKey(filterArgs);
  const dateRangeInvalid = isDateRangeInvalid(filters);

  const resolveGeoName = useCallback(
    (level: string, geoid: string): string | null => {
      if (level === "state" && geoid === MARYLAND_STATE_GEOID) return "Maryland";
      const lvl = level as Level;
      const geo = geoByLevel[lvl];
      if (!geo) return null;
      const feat = geo.features.find(
        (f) => String((f.properties as { GEOID?: string })?.GEOID) === geoid,
      );
      if (!feat) return null;
      const props = feat.properties as { name?: string; NAMELSAD?: string };
      return props?.name ?? props?.NAMELSAD ?? geoid;
    },
    [geoByLevel],
  );

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        const meta = await fetchMetadata();
        if (cancelled) return;
        setMetadata(meta);
        setFilters((f) => ({
          ...f,
          metric: f.metric || meta.default_metric,
          dateFrom: f.dateFrom || meta.min_crash_date || "",
          dateTo: f.dateTo || meta.max_crash_date || "",
        }));
        const levels: Level[] = meta.levels;
        const geos = await Promise.all(levels.map((l) => fetchGeo(l).then((g) => [l, g] as const)));
        if (cancelled) return;
        const obj: GeoByLevel = {};
        for (const [l, g] of geos) obj[l] = g;
        setGeoByLevel(obj);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!geoByLevel.county || urlSelectionsInit.current) return;
    urlSelectionsInit.current = true;
    setSelections(decodeGeosFromUrl(getGeosParam(), resolveGeoName));
  }, [geoByLevel.county, resolveGeoName]);

  const summaryReqId = useRef(0);
  useEffect(() => {
    if (!metadata) return;
    const metricDefForFetch = metadata.metrics.find((m) => m.id === filters.metric);
    if (!metricDefForFetch) return;

    const myId = ++summaryReqId.current;
    (async () => {
      try {
        setLoading(true);
        const responses = await Promise.all(
          DASHBOARD_LEVELS.map((level) =>
            fetchSummary(level, filters.metric, filterArgs),
          ),
        );
        if (myId !== summaryReqId.current) return;
        setSummaryCache(buildSummaryCache(responses, metricDefForFetch));
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (myId === summaryReqId.current) setLoading(false);
      }
    })();
  }, [metadata, filters.metric, filterKey]);

  const crashReqId = useRef(0);
  useEffect(() => {
    if (!metadata || activeTab !== "map") return;
    if (zoom < ZOOM.crashesMin) {
      setCrashes([]);
      return;
    }
    const myId = ++crashReqId.current;
    const t = window.setTimeout(async () => {
      try {
        setLoading(true);
        const [west, south, east, north] = bbox;
        const resp = await fetchCrashes({ west, south, east, north }, filterArgs, 50_000);
        if (myId !== crashReqId.current) return;
        setCrashes(resp.points);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e));
      } finally {
        if (myId === crashReqId.current) setLoading(false);
      }
    }, 250);
    return () => window.clearTimeout(t);
  }, [zoom, bbox, filterKey, metadata, activeTab]);

  useEffect(() => {
    if (activeTab === "map") writeUrlState(selections, filters);
  }, [selections, filters, activeTab]);

  const onViewStateChange = useCallback(
    (s: { zoom: number; bbox: [number, number, number, number] }) => {
      setZoom(s.zoom);
      setBbox(s.bbox);
    },
    [],
  );

  const basemapUrl = useMemo(
    () => BASEMAPS.find((b) => b.id === basemapId)?.url ?? BASEMAPS[0].url,
    [basemapId],
  );

  const metricDef = useMemo(
    () => metadata?.metrics.find((m) => m.id === filters.metric),
    [metadata, filters.metric],
  );

  const activeLevel: Level = levelForZoom(zoom);
  const activeFeatureCount = summaryCache[activeLevel]?.size ?? 0;
  const crashesVisible = zoom >= ZOOM.crashesMin;

  const searchIndex = useMemo(() => buildSearchIndex(geoByLevel), [geoByLevel]);

  const selectionColors = useMemo(() => {
    const map = new Map<string, [number, number, number]>();
    let otherIdx = 0;
    for (const sel of selections) {
      const isBaseline = sel.level === "state" && sel.geoid === MARYLAND_STATE_GEOID;
      map.set(
        sel.key,
        colorForSelection(isBaseline, isBaseline ? 0 : otherIdx++),
      );
    }
    return map;
  }, [selections]);

  const selectedKeys = useMemo(() => new Set(selections.map((s) => s.key)), [selections]);

  const scrollToDashboard = useCallback(() => {
    requestAnimationFrame(() => {
      document
        .getElementById("comparison-dashboard")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, []);

  const addSelection = useCallback(
    (sel: SelectedGeo) => {
      let added = false;
      setSelections((prev) => {
        if (prev.some((s) => s.key === sel.key)) return prev;
        if (prev.length >= MAX_SELECTIONS) return prev;
        added = true;
        return [...prev, sel];
      });
      if (added) {
        setPulseKey(sel.key);
        window.setTimeout(() => setPulseKey(null), 1200);
      }
      setSelectedCrash(null);
      scrollToDashboard();
    },
    [scrollToDashboard],
  );

  const handleGeoClick = useCallback(
    (payload: GeoClickPayload) => {
      addSelection(makeSelection(payload.level, payload.geoid, payload.name));
    },
    [addSelection],
  );

  const handleSearchAdd = useCallback(
    (entry: SearchEntry) => {
      addSelection(makeSelection(entry.level, entry.geoid, entry.name));
    },
    [addSelection],
  );

  const handleRemoveSelection = useCallback((key: string) => {
    setSelections((prev) => {
      const next = prev.filter((s) => s.key !== key);
      return next.length > 0 ? next : [MARYLAND_BASELINE];
    });
  }, []);

  const summaryByLevelForMap = useMemo(() => {
    const out: Partial<Record<Level, Map<string, SummaryFeature>>> = {};
    for (const level of ["county", "place", "tract"] as Level[]) {
      if (summaryCache[level]) out[level] = summaryCache[level];
    }
    return out;
  }, [summaryCache]);

  return (
    <div className="site">
      <SiteHeader
        activeTab={activeTab}
        onTabChange={setActiveTab}
        showHero={activeTab === "map"}
      />

      {activeTab === "map" && (
        <>
          {metadata && (
            <FilterBar
              metadata={metadata}
              filters={filters}
              basemapId={basemapId}
              dateRangeInvalid={dateRangeInvalid}
              onFiltersChange={setFilters}
              onBasemapChange={setBasemapId}
            />
          )}

          <section className="map-section" aria-label="Interactive map">
            <MapView
              basemapStyleUrl={basemapUrl}
              geoByLevel={geoByLevel}
              summaryByLevel={summaryByLevelForMap}
              crashes={crashes}
              metricDef={metricDef}
              selectedKeys={selectedKeys}
              selectionColors={selectionColors}
              onViewStateChange={onViewStateChange}
              onScaleChange={setScale}
              onGeoClick={handleGeoClick}
              onCrashClick={setSelectedCrash}
            />

            <StatusPanel
              zoom={zoom}
              level={activeLevel}
              summaryFeatureCount={activeFeatureCount}
              crashesVisible={crashesVisible}
              crashCount={crashes.length}
              loading={loading}
            />

            <Legend metric={metricDef} scale={scale} showCrashLegend={crashesVisible} />

            {error && <div className="error-banner">{error}</div>}
          </section>

          {selectedCrash && (
            <div className="crash-detail-wrap">
              <CrashDetailCard
                crash={selectedCrash}
                metric={metricDef}
                onClose={() => setSelectedCrash(null)}
              />
            </div>
          )}

          {metadata && (
            <ComparisonDashboard
              selections={selections}
              summaryCache={summaryCache}
              metrics={metadata.metrics}
              selectionColors={selectionColors}
              pulseKey={pulseKey}
              searchIndex={searchIndex}
              onRemove={handleRemoveSelection}
              onAdd={handleSearchAdd}
            />
          )}
        </>
      )}

      {activeTab === "methodology" && (
        <main className="site-main">
          <ProsePage
            title={methodologyContent.pageTitle}
            intro={methodologyContent.intro}
            sections={methodologyContent.sections}
          />
        </main>
      )}

      {activeTab === "about" && (
        <main className="site-main">
          <ProsePage
            title={aboutContent.pageTitle}
            intro={aboutContent.intro}
            sections={aboutContent.sections}
          />
        </main>
      )}

      <SiteFooter />
    </div>
  );
}

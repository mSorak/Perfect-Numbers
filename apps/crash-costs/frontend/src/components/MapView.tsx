import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import { GeoJsonLayer, ScatterplotLayer } from "@deck.gl/layers";
import { MapboxOverlay } from "@deck.gl/mapbox";
import type { PickingInfo } from "@deck.gl/core";

import type { CrashPoint, Level, MetricDef, SummaryFeature } from "../types";
import { selectionKey } from "../geoSelection";
import { CRASH_TYPE_COLORS, MARYLAND_INITIAL_VIEW, ZOOM, levelForZoom } from "../config";
import { buildQuantileScale, colorFor, type Scale } from "../colorScale";
import { formatMetric } from "../format";
import { computeMetricValue } from "../metrics";
import { normalizeGeoid } from "../summaryCache";

type GeoByLevel = Partial<Record<Level, GeoJSON.FeatureCollection>>;
type SummaryByLevel = Partial<Record<Level, Map<string, SummaryFeature>>>;

export interface GeoClickPayload {
  level: Level;
  geoid: string;
  name: string;
}

interface Props {
  basemapStyleUrl: string;
  geoByLevel: GeoByLevel;
  summaryByLevel: SummaryByLevel;
  crashes: CrashPoint[];
  metricDef: MetricDef | undefined;
  selectedKeys: Set<string>;
  selectionColors: Map<string, [number, number, number]>;
  onViewStateChange: (state: { zoom: number; bbox: [number, number, number, number] }) => void;
  onScaleChange: (scale: Scale | null) => void;
  onGeoClick: (payload: GeoClickPayload) => void;
  onCrashClick: (crash: CrashPoint) => void;
}

export function MapView({
  basemapStyleUrl,
  geoByLevel,
  summaryByLevel,
  crashes,
  metricDef,
  selectedKeys,
  selectionColors,
  onViewStateChange,
  onScaleChange,
  onGeoClick,
  onCrashClick,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const overlayRef = useRef<MapboxOverlay | null>(null);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const [zoom, setZoom] = useState(MARYLAND_INITIAL_VIEW.zoom);

  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: basemapStyleUrl,
      center: [MARYLAND_INITIAL_VIEW.longitude, MARYLAND_INITIAL_VIEW.latitude],
      zoom: MARYLAND_INITIAL_VIEW.zoom,
      minZoom: 5,
      maxZoom: 18,
      attributionControl: { compact: true },
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    const overlay = new MapboxOverlay({ interleaved: false, layers: [] });
    map.addControl(overlay);

    const popup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      maxWidth: "320px",
    });

    mapRef.current = map;
    overlayRef.current = overlay;
    popupRef.current = popup;

    const report = () => {
      const b = map.getBounds();
      onViewStateChange({
        zoom: map.getZoom(),
        bbox: [b.getWest(), b.getSouth(), b.getEast(), b.getNorth()],
      });
      setZoom(map.getZoom());
    };
    map.on("load", report);
    map.on("moveend", report);

    return () => {
      popup.remove();
      map.remove();
      mapRef.current = null;
      overlayRef.current = null;
      popupRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    map.setStyle(basemapStyleUrl);
  }, [basemapStyleUrl]);

  const activeLevel: Level = levelForZoom(zoom);
  const activeSummary = summaryByLevel[activeLevel];

  const scale: Scale | null = useMemo(() => {
    if (!activeSummary || !metricDef) return null;
    const values: number[] = [];
    activeSummary.forEach((row) => {
      const v = computeMetricValue(metricDef, row);
      if (v !== null && v !== undefined && !Number.isNaN(v)) values.push(v);
    });
    return buildQuantileScale(values);
  }, [activeSummary, metricDef]);

  useEffect(() => {
    onScaleChange(scale);
  }, [scale, onScaleChange]);

  const layers = useMemo(() => {
    const result: Array<GeoJsonLayer | ScatterplotLayer> = [];

    const zoomVisibility: Record<Level, [number, number]> = {
      county: [ZOOM.countyMin, ZOOM.countyMax],
      place: [ZOOM.placeMin, ZOOM.placeMax],
      tract: [ZOOM.tractMin, 22],
    };

    (["county", "place", "tract"] as Level[]).forEach((level) => {
      const geo = geoByLevel[level];
      const summary = summaryByLevel[level];
      if (!geo) return;
      const [minZ, maxZ] = zoomVisibility[level];
      if (zoom < minZ || zoom > maxZ) return;

      const levelScale = level === activeLevel ? scale : null;

      result.push(
        new GeoJsonLayer({
          id: `geo-${level}`,
          data: geo,
          pickable: true,
          autoHighlight: true,
          highlightColor: [255, 255, 255, 80],
          stroked: true,
          filled: true,
          getFillColor: (feature) => {
            const geoid = normalizeGeoid(
              (feature.properties as { GEOID?: string })?.GEOID,
            );
            const row = geoid ? summary?.get(geoid) : undefined;
            const value =
              row && metricDef ? computeMetricValue(metricDef, row) : (row?.value ?? null);
            return colorFor(value, levelScale, 180);
          },
          getLineColor: (feature) => {
            const geoid = normalizeGeoid(
              (feature.properties as { GEOID?: string })?.GEOID,
            );
            const key = geoid ? selectionKey(level, geoid) : "";
            if (key && selectedKeys.has(key)) {
              const c = selectionColors.get(key);
              if (c) return [c[0], c[1], c[2], 255];
            }
            return level === "tract" ? [80, 80, 80, 90] : [50, 50, 50, 200];
          },
          getLineWidth: (feature) => {
            const geoid = normalizeGeoid(
              (feature.properties as { GEOID?: string })?.GEOID,
            );
            const key = geoid ? selectionKey(level, geoid) : "";
            if (key && selectedKeys.has(key)) return 3;
            return level === "county" ? 1.5 : 0.5;
          },
          lineWidthUnits: "pixels",
          updateTriggers: {
            getFillColor: [summary, levelScale, metricDef?.id],
            getLineColor: [selectedKeys, selectionColors],
            getLineWidth: [selectedKeys],
          },
          onHover: (info) => handleHover(info, level),
          onClick: (info) => handleGeoClick(info, level),
        }),
      );
    });

    if (zoom >= ZOOM.crashesMin && crashes.length > 0) {
      const maxCost = Math.max(1, ...crashes.map((c) => c.cost_total ?? 0));
      result.push(
        new ScatterplotLayer<CrashPoint>({
          id: "crashes",
          data: crashes,
          pickable: true,
          stroked: true,
          filled: true,
          radiusUnits: "pixels",
          lineWidthMinPixels: 1,
          getPosition: (d) => [d.lon, d.lat],
          getRadius: (d) => {
            const c = d.cost_total ?? 0;
            return 4 + 22 * Math.sqrt(c / maxCost);
          },
          getFillColor: (d) => {
            const rgb = CRASH_TYPE_COLORS[d.crash_type] ?? [110, 110, 110];
            return [rgb[0], rgb[1], rgb[2], 235];
          },
          getLineColor: [25, 25, 25, 230],
          updateTriggers: {
            getRadius: [maxCost],
          },
          onHover: (info) => handleHoverCrash(info),
          onClick: (info) => {
            if (info.object) onCrashClick(info.object as CrashPoint);
          },
        }),
      );
    }

    return result;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    geoByLevel,
    summaryByLevel,
    crashes,
    zoom,
    scale,
    activeLevel,
    selectedKeys,
    selectionColors,
    metricDef,
  ]);

  useEffect(() => {
    const overlay = overlayRef.current;
    if (!overlay) return;
    overlay.setProps({ layers });
  }, [layers]);

  function handleGeoClick(info: PickingInfo, level: Level) {
    if (!info.object) return;
    const props = (info.object as GeoJSON.Feature).properties as {
      GEOID?: string;
      name?: string;
    };
    const geoid = props?.GEOID;
    if (!geoid) return;
    onGeoClick({
      level,
      geoid: String(geoid),
      name: props?.name ?? String(geoid),
    });
  }

  function handleHover(info: PickingInfo, level: Level) {
    const popup = popupRef.current;
    const map = mapRef.current;
    if (!popup || !map) return;
    if (!info.object || !info.coordinate) {
      popup.remove();
      return;
    }
    const props = (info.object as GeoJSON.Feature).properties as {
      GEOID?: string;
      name?: string;
    };
    const geoid = normalizeGeoid(props?.GEOID);
    const summary = geoid ? summaryByLevel[level]?.get(geoid) : undefined;
    const html = renderGeoPopup({
      level,
      name: props?.name ?? geoid ?? "Unknown",
      summary,
      metric: metricDef,
    });
    popup.setLngLat([info.coordinate[0], info.coordinate[1]]).setHTML(html).addTo(map);
  }

  function handleHoverCrash(info: PickingInfo) {
    const popup = popupRef.current;
    const map = mapRef.current;
    if (!popup || !map) return;
    if (!info.object) {
      popup.remove();
      return;
    }
    const p = info.object as CrashPoint;
    popup.setLngLat([p.lon, p.lat]).setHTML(renderCrashPopup(p, metricDef)).addTo(map);
  }

  return <div ref={containerRef} className="map-container" />;
}

const GEO_LEVEL_LABELS: Record<Level, string> = {
  county: "County",
  place: "Census designated place",
  tract: "Census tract",
};

function renderGeoPopup({
  level,
  name,
  summary,
  metric,
}: {
  level: Level;
  name: string;
  summary: SummaryFeature | undefined;
  metric: MetricDef | undefined;
}): string {
  const metricLabel = metric?.label ?? "Primary metric";
  const metricValue = formatMetric(
    summary && metric ? computeMetricValue(metric, summary) : (summary?.value ?? null),
    metric,
  );

  return `
    <h3>${escapeHtml(name)}</h3>
    <div class="popup-level">${GEO_LEVEL_LABELS[level]}</div>
    <div class="popup-metric">
      <div class="popup-metric-label">${escapeHtml(metricLabel)}</div>
      <div class="popup-metric-value">${metricValue}</div>
    </div>
    ${popupMoreHint(name)}
  `;
}

function renderCrashPopup(p: CrashPoint, metric: MetricDef | undefined): string {
  const metricLabel = metric?.label ?? "Primary metric";
  const metricValue = formatMetric(crashMetricValue(p, metric), metric);
  const locationLabel = `Crash ${p.report_number}`;

  return `
    <h3>${escapeHtml(locationLabel)}</h3>
    <div class="popup-level">Crash</div>
    <div class="popup-metric">
      <div class="popup-metric-label">${escapeHtml(metricLabel)}</div>
      <div class="popup-metric-value">${metricValue}</div>
    </div>
    <div class="popup-more-hint">Click for crash details</div>
  `;
}

function crashMetricValue(p: CrashPoint, metric: MetricDef | undefined): number | null {
  if (!metric || metric.denominator) return null;

  switch (metric.id) {
    case "comprehensive_cost_total":
      return p.cost_total;
    case "crashes_total":
      return 1;
    case "fatalities_total":
      return p.n_fatalities_person;
    case "injuries_total":
      return p.n_injuries_person;
    case "medical_cost_total":
      return p.cost_medical;
    case "congestion_cost_total":
      return p.cost_congestion;
    case "property_damage_cost_total":
      return p.cost_propdamage;
    case "total_economic_cost_total":
      return p.cost_total_economic;
    case "qalys_cost_total":
      return p.cost_qalys;
    default:
      return null;
  }
}

function popupMoreHint(locationName: string): string {
  return `<div class="popup-more-hint">Click to compare ${escapeHtml(locationName)}</div>`;
}

function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => {
    switch (c) {
      case "&":
        return "&amp;";
      case "<":
        return "&lt;";
      case ">":
        return "&gt;";
      case '"':
        return "&quot;";
      default:
        return "&#39;";
    }
  });
}

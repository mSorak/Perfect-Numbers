import type { ChangeEvent } from "react";
import type { CrashType, Filters, Metadata } from "../types";
import { BASEMAPS } from "../config";

interface Props {
  metadata: Metadata;
  filters: Filters;
  basemapId: string;
  dateRangeInvalid?: boolean;
  onFiltersChange: (f: Filters) => void;
  onBasemapChange: (id: string) => void;
}

const CRASH_TYPE_LABELS: Record<CrashType, string> = {
  fatal: "Fatal",
  injury: "Injury",
  property_damage: "Property damage",
};

const METRIC_GROUPS: Array<{ label: string; ids: string[] }> = [
  {
    label: "Total",
    ids: [
      "comprehensive_cost_total",
      "crashes_total",
      "fatalities_total",
      "injuries_total",
      "medical_cost_total",
      "congestion_cost_total",
      "property_damage_cost_total",
      "total_economic_cost_total",
      "qalys_cost_total",
    ],
  },
  {
    label: "Per Capita",
    ids: [
      "comprehensive_cost_per_capita",
      "fatalities_per_capita",
      "injuries_per_capita",
      "medical_cost_per_capita",
      "congestion_cost_per_capita",
      "property_damage_cost_per_capita",
      "total_economic_cost_per_capita",
      "qalys_cost_per_capita",
    ],
  },
  {
    label: "Misc",
    ids: ["vehicles_per_person", "pct_households_no_vehicle"],
  },
];

export function FilterBar({
  metadata,
  filters,
  basemapId,
  dateRangeInvalid = false,
  onFiltersChange,
  onBasemapChange,
}: Props) {
  const toggleInArray = <T,>(arr: T[], v: T): T[] =>
    arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v];

  function handleMetric(e: ChangeEvent<HTMLSelectElement>) {
    onFiltersChange({ ...filters, metric: e.target.value });
  }

  function handleDateFrom(e: ChangeEvent<HTMLInputElement>) {
    onFiltersChange({ ...filters, dateFrom: e.target.value });
  }

  function handleDateTo(e: ChangeEvent<HTMLInputElement>) {
    onFiltersChange({ ...filters, dateTo: e.target.value });
  }

  function resetDateRange() {
    onFiltersChange({
      ...filters,
      dateFrom: metadata.min_crash_date ?? "",
      dateTo: metadata.max_crash_date ?? "",
    });
  }

  function toggleCrashType(t: CrashType) {
    onFiltersChange({ ...filters, crashTypes: toggleInArray(filters.crashTypes, t) });
  }

  const minD = metadata.min_crash_date ?? "";
  const maxD = metadata.max_crash_date ?? "";
  const metricsById = new Map(metadata.metrics.map((m) => [m.id, m] as const));
  const groupedMetrics = METRIC_GROUPS.map((group) => ({
    label: group.label,
    metrics: group.ids
      .map((id) => metricsById.get(id))
      .filter((m): m is Metadata["metrics"][number] => Boolean(m)),
  })).filter((group) => group.metrics.length > 0);

  return (
    <div className="filter-bar" role="region" aria-label="Map filters">
      <div className="filter-bar-inner">
        <div className="filter-row">
          <label className="filter-field filter-field-metric">
            <span className="label-text">Primary metric</span>
            <select value={filters.metric} onChange={handleMetric}>
              {groupedMetrics.map((group) => (
                <optgroup key={group.label} label={group.label}>
                  {group.metrics.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label}
                    </option>
                  ))}
                </optgroup>
              ))}
            </select>
          </label>

          <div className="filter-field filter-field-dates">
            <span className="label-text">Crash date range</span>
            <div className="date-range-row">
              <label className="inline-date">
                <span className="sr-only">From</span>
                <input
                  type="date"
                  value={filters.dateFrom}
                  min={minD || undefined}
                  max={maxD || undefined}
                  onChange={handleDateFrom}
                />
              </label>
              <span className="date-sep">to</span>
              <label className="inline-date">
                <span className="sr-only">To</span>
                <input
                  type="date"
                  value={filters.dateTo}
                  min={minD || undefined}
                  max={maxD || undefined}
                  onChange={handleDateTo}
                />
              </label>
              <button type="button" className="link-button" onClick={resetDateRange}>
                Reset
              </button>
            </div>
            {dateRangeInvalid && (
              <p className="field-hint field-hint-error">
                End date must be on or after start date. Date filter ignored until fixed.
              </p>
            )}
          </div>

          <label className="filter-field filter-field-basemap">
            <span className="label-text">Basemap</span>
            <select value={basemapId} onChange={(e) => onBasemapChange(e.target.value)}>
              {BASEMAPS.map((b) => (
                <option key={b.id} value={b.id}>
                  {b.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="filter-row filter-row-secondary">
          <label className="checkbox-line">
            <input
              type="checkbox"
              checked={filters.nonmotoristInvolved}
              onChange={(e) =>
                onFiltersChange({ ...filters, nonmotoristInvolved: e.target.checked })
              }
            />
            <span>Pedestrian or cyclist involved</span>
          </label>

          <div className="filter-field filter-field-types">
            <span className="label-text">Crash type</span>
            <div className="checkbox-row">
              {(Object.keys(CRASH_TYPE_LABELS) as CrashType[]).map((t) => (
                <label key={t}>
                  <input
                    type="checkbox"
                    checked={filters.crashTypes.includes(t)}
                    onChange={() => toggleCrashType(t)}
                  />
                  {CRASH_TYPE_LABELS[t]}
                </label>
              ))}
              <span className="field-hint-inline">(none selected = all)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { SearchEntry } from "../buildSearchIndex";
import { dashboardContent } from "../content/dashboard";
import { colorCss } from "../geoColors";
import { levelLabel } from "../geoSelection";
import { computeMetricValue, rateMetrics } from "../metrics";
import { formatCurrency, formatMetric, formatNumber } from "../format";
import { lookupSummary, type SummaryCache } from "../summaryCache";
import type { MetricDef, SelectedGeo, SummaryFeature } from "../types";
import { GeoSearchBar } from "./GeoSearchBar";

interface Props {
  selections: SelectedGeo[];
  summaryCache: SummaryCache;
  metrics: MetricDef[];
  selectionColors: Map<string, [number, number, number]>;
  pulseKey: string | null;
  searchIndex: SearchEntry[];
  onRemove: (key: string) => void;
  onAdd: (entry: SearchEntry) => void;
}

export function ComparisonDashboard({
  selections,
  summaryCache,
  metrics,
  selectionColors,
  pulseKey,
  searchIndex,
  onRemove,
  onAdd,
}: Props) {
  const rateMetricList = useMemo(() => rateMetrics(metrics), [metrics]);

  const rows = useMemo(() => {
    return selections.map((sel) => {
      const feature = lookupSummary(summaryCache, sel.level, sel.geoid);
      return { sel, feature };
    });
  }, [selections, summaryCache]);

  const selectedKeys = useMemo(() => new Set(selections.map((s) => s.key)), [selections]);

  return (
    <section className="dashboard" id="comparison-dashboard" aria-label="Geography comparison">
      <div className="dashboard-inner">
        <header className="dashboard-header">
          <h2>{dashboardContent.title}</h2>
          <p>{dashboardContent.intro}</p>
          <p className="dashboard-filters-note">{dashboardContent.mapFiltersNote}</p>
        </header>

        <div className="dashboard-toolbar">
          <GeoSearchBar
            index={searchIndex}
            selectedKeys={selectedKeys}
            onSelect={onAdd}
          />
        </div>

        <div className="dashboard-chips" role="list" aria-label="Selected geographies">
          {selections.map((sel) => {
            const rgb = selectionColors.get(sel.key) ?? [120, 120, 120];
            const pulse = pulseKey === sel.key;
            return (
              <span
                key={sel.key}
                role="listitem"
                className={`dashboard-chip${pulse ? " is-pulse" : ""}`}
                style={{ borderColor: colorCss(rgb), backgroundColor: colorCss(rgb, 0.12) }}
              >
                <span
                  className="dashboard-chip-swatch"
                  style={{ backgroundColor: colorCss(rgb) }}
                  aria-hidden
                />
                <span className="dashboard-chip-text">
                  <span className="dashboard-chip-name">{sel.name}</span>
                  <span className="dashboard-chip-level">{levelLabel(sel.level)}</span>
                </span>
                <button
                  type="button"
                  className="dashboard-chip-remove"
                  aria-label={`Remove ${sel.name}`}
                  onClick={() => onRemove(sel.key)}
                >
                  ×
                </button>
              </span>
            );
          })}
        </div>

        <h3 className="dashboard-subheading">{dashboardContent.contextHeading}</h3>
        <div className="dashboard-context-wrap">
          <table className="dashboard-context-table">
            <thead>
              <tr>
                <th>Geography</th>
                <th>Population</th>
                <th>Crashes</th>
                <th>Comprehensive cost</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ sel, feature }) => (
                <tr key={sel.key}>
                  <td>
                    <span
                      className="dashboard-context-swatch"
                      style={{
                        backgroundColor: colorCss(
                          selectionColors.get(sel.key) ?? [120, 120, 120],
                        ),
                      }}
                    />
                    {sel.name}
                  </td>
                  <td>{formatNumber(feature?.population ?? null)}</td>
                  <td>{formatNumber(feature?.n_crashes ?? null)}</td>
                  <td>{formatCurrency(feature?.sum_cost_total ?? null)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <h3 className="dashboard-subheading">{dashboardContent.chartsHeading}</h3>
        <div className="dashboard-charts">
          {rateMetricList.map((metric) => (
            <MetricChart
              key={metric.id}
              metric={metric}
              rows={rows}
              selectionColors={selectionColors}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

function MetricChart({
  metric,
  rows,
  selectionColors,
}: {
  metric: MetricDef;
  rows: Array<{ sel: SelectedGeo; feature: SummaryFeature | undefined }>;
  selectionColors: Map<string, [number, number, number]>;
}) {
  const chartData = rows
    .map(({ sel, feature }) => {
      const value = feature ? computeMetricValue(metric, feature) : null;
      return {
        key: sel.key,
        name: sel.name,
        value: value ?? 0,
        hasValue: value !== null && value !== undefined && !Number.isNaN(value),
        fill: colorCss(selectionColors.get(sel.key) ?? [120, 120, 120]),
      };
    })
    .sort((a, b) => b.value - a.value);

  const barHeight = 36;
  const height = Math.max(120, chartData.length * barHeight + 48);

  return (
    <div className="dashboard-chart-card">
      <h4 className="dashboard-chart-title">{metric.label}</h4>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          layout="vertical"
          data={chartData}
          margin={{ top: 4, right: 16, left: 8, bottom: 4 }}
        >
          <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e7e5e4" />
          <XAxis
            type="number"
            tickFormatter={(v) => formatMetric(v, metric)}
            tick={{ fontSize: 11, fill: "#78716c" }}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={140}
            tick={{ fontSize: 11, fill: "#44403c" }}
          />
          <Tooltip
            formatter={(value, _name, item) => {
              const row = item?.payload as { hasValue?: boolean } | undefined;
              if (!row?.hasValue) return "—";
              return formatMetric(Number(value), metric);
            }}
          />
          <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={28}>
            {chartData.map((entry) => (
              <Cell
                key={entry.key}
                fill={entry.fill}
                fillOpacity={entry.hasValue ? 1 : 0.25}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

import type { MetricDef, SummaryFeature } from "./types";

const NUMERATOR_BY_METRIC_ID: Record<string, string> = {
  comprehensive_cost_total: "sum_cost_total",
  crashes_total: "n_crashes",
  fatalities_total: "sum_fatalities_person",
  injuries_total: "sum_injuries_person",
  medical_cost_total: "sum_cost_medical",
  congestion_cost_total: "sum_cost_congestion",
  property_damage_cost_total: "sum_cost_propdamage",
  total_economic_cost_total: "sum_cost_total_economic",
  qalys_cost_total: "sum_cost_qalys",
  comprehensive_cost_per_capita: "sum_cost_total",
  fatalities_per_capita: "sum_fatalities_person",
  injuries_per_capita: "sum_injuries_person",
  medical_cost_per_capita: "sum_cost_medical",
  congestion_cost_per_capita: "sum_cost_congestion",
  property_damage_cost_per_capita: "sum_cost_propdamage",
  total_economic_cost_per_capita: "sum_cost_total_economic",
  qalys_cost_per_capita: "sum_cost_qalys",
  vehicles_per_person: "vehicles_per_person",
  pct_households_no_vehicle: "pct_hh_no_vehicle",
};

/** Mirror of backend compute_metric_value for dashboard charts. */
export function computeMetricValue(
  metric: MetricDef,
  row: SummaryFeature | Record<string, unknown>,
): number | null {
  const numeratorKey = NUMERATOR_BY_METRIC_ID[metric.id];
  if (!numeratorKey) return null;

  const raw = row[numeratorKey];
  if (raw === null || raw === undefined) return null;
  if (typeof raw === "number" && Number.isNaN(raw)) return null;

  if (!metric.denominator) {
    return typeof raw === "number" ? raw : Number(raw);
  }

  const denom = row[metric.denominator];
  if (denom === null || denom === undefined || denom === 0) return null;
  if (typeof denom === "number" && Number.isNaN(denom)) return null;

  let value = Number(raw) / Number(denom);
  if (metric.rate_per != null) value *= metric.rate_per;
  return value;
}

/** Per-capita rate metrics suitable for cross-level comparison charts. */
export function isRateMetric(metric: MetricDef): boolean {
  return metric.denominator === "population";
}

export function rateMetrics(metrics: MetricDef[]): MetricDef[] {
  return metrics.filter(isRateMetric);
}

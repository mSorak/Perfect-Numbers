"""Pre-defined `primary_metric` registry.

Each metric is a SQL aggregate column name (`numerator_sql`) on the per-geography
row, optionally divided by `denominator` (`population` for per-capita crash
metrics). Census-only metrics (`vehicles_per_person`, `pct_hh_no_vehicle`) are
joined from prepared GeoJSON in :mod:`main` and are not produced by DuckDB.

Aggregate columns (see :mod:`data`):

    n_crashes, n_fatal, n_injury, n_property_damage
    sum_fatalities_person, sum_injuries_person
    sum_cost_total, sum_cost_medical, … sum_cost_cong_propdamage,
    sum_cost_total_economic, sum_cost_qalys
    sum_occupants, sum_nonmotorists, sum_vehicles
    population, vehicles_per_person, pct_hh_no_vehicle  (joined)
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDef:
    id: str
    label: str
    numerator_sql: str
    format: str  # "currency" | "number" | "rate" | "percent"
    denominator: str | None = None  # None | "population"
    rate_per: float | None = None  # e.g. 100_000 for "per 100k"
    description: str = ""


METRICS: list[MetricDef] = [
    # Totals (crash-aggregated)
    MetricDef(
        id="comprehensive_cost_total",
        label="Total comprehensive cost (2025 USD)",
        numerator_sql="sum_cost_total",
        format="currency",
        description="Sum of crash-level comprehensive costs.",
    ),
    MetricDef(
        id="crashes_total",
        label="Total crashes",
        numerator_sql="n_crashes",
        format="number",
    ),
    MetricDef(
        id="fatalities_total",
        label="Fatalities (person counts)",
        numerator_sql="sum_fatalities_person",
        format="number",
        description="Sum of occupant and non-motorist police injury status = fatal (code 1).",
    ),
    MetricDef(
        id="injuries_total",
        label="Injuries (person counts)",
        numerator_sql="sum_injuries_person",
        format="number",
        description="Sum of occupant and non-motorist injury status codes 2–5.",
    ),
    MetricDef(
        id="medical_cost_total",
        label="Medical costs (2025 USD)",
        numerator_sql="sum_cost_medical",
        format="currency",
    ),
    MetricDef(
        id="congestion_cost_total",
        label="Congestion costs (2025 USD)",
        numerator_sql="sum_cost_congestion",
        format="currency",
    ),
    MetricDef(
        id="property_damage_cost_total",
        label="Property damage costs (2025 USD)",
        numerator_sql="sum_cost_propdamage",
        format="currency",
    ),
    MetricDef(
        id="total_economic_cost_total",
        label="Total economic costs (2025 USD)",
        numerator_sql="sum_cost_total_economic",
        format="currency",
    ),
    MetricDef(
        id="qalys_cost_total",
        label="Cost of life years lost — QALYs (2025 USD)",
        numerator_sql="sum_cost_qalys",
        format="currency",
    ),
    # Per capita (crash sums / population)
    MetricDef(
        id="comprehensive_cost_per_capita",
        label="Total comprehensive cost per capita (2025 USD)",
        numerator_sql="sum_cost_total",
        format="currency",
        denominator="population",
    ),
    MetricDef(
        id="fatalities_per_capita",
        label="Fatalities per capita (person counts)",
        numerator_sql="sum_fatalities_person",
        format="number",
        denominator="population",
    ),
    MetricDef(
        id="injuries_per_capita",
        label="Injuries per capita (person counts)",
        numerator_sql="sum_injuries_person",
        format="number",
        denominator="population",
    ),
    MetricDef(
        id="medical_cost_per_capita",
        label="Medical costs per capita (2025 USD)",
        numerator_sql="sum_cost_medical",
        format="currency",
        denominator="population",
    ),
    MetricDef(
        id="congestion_cost_per_capita",
        label="Congestion costs per capita (2025 USD)",
        numerator_sql="sum_cost_congestion",
        format="currency",
        denominator="population",
    ),
    MetricDef(
        id="property_damage_cost_per_capita",
        label="Property damage costs per capita (2025 USD)",
        numerator_sql="sum_cost_propdamage",
        format="currency",
        denominator="population",
    ),
    MetricDef(
        id="total_economic_cost_per_capita",
        label="Total economic costs per capita (2025 USD)",
        numerator_sql="sum_cost_total_economic",
        format="currency",
        denominator="population",
    ),
    MetricDef(
        id="qalys_cost_per_capita",
        label="Cost of life years lost (QALYs) per capita (2025 USD)",
        numerator_sql="sum_cost_qalys",
        format="currency",
        denominator="population",
    ),
    # Census context (NHGIS ACS, not crash-derived)
    MetricDef(
        id="vehicles_per_person",
        label="Vehicles per person (census estimate)",
        numerator_sql="vehicles_per_person",
        format="number",
        description="ACS B08201 vehicle stock estimate divided by total population.",
    ),
    MetricDef(
        id="pct_households_no_vehicle",
        label="Percent of households with no vehicle (census)",
        numerator_sql="pct_hh_no_vehicle",
        format="percent",
        description="ACS B08201: percent of households reporting zero vehicles available.",
    ),
]


METRICS_BY_ID = {m.id: m for m in METRICS}

DEFAULT_METRIC_ID = "comprehensive_cost_per_capita"


def compute_metric_value(metric: MetricDef, row: dict) -> float | None:
    """Apply a metric definition to an aggregated row (Python-side)."""
    num = row.get(metric.numerator_sql)
    if num is None:
        return None
    if isinstance(num, float) and num != num:
        return None
    if metric.denominator is None:
        return float(num)
    denom = row.get(metric.denominator)
    if denom in (None, 0) or (isinstance(denom, float) and denom != denom):
        return None
    value = float(num) / float(denom)
    if metric.rate_per is not None:
        value *= metric.rate_per
    return value

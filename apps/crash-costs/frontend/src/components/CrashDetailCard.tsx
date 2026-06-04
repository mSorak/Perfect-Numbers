import type { CrashPoint, MetricDef } from "../types";
import { formatCurrency, formatMetric, formatNumber } from "../format";

interface Props {
  crash: CrashPoint;
  metric: MetricDef | undefined;
  onClose: () => void;
}

const TYPE_LABELS: Record<string, string> = {
  fatal: "Fatal",
  injury: "Injury",
  property_damage: "Property damage",
};

function crashDateTimeLabel(p: CrashPoint): string {
  const raw = p.crash_date;
  let datePart: string;
  if (raw && String(raw).trim()) {
    const s = String(raw).trim();
    datePart = s.includes("T") ? s.split("T")[0]! : s.split(" ")[0]!;
  } else {
    datePart = `${p.crash_year}-${String(p.crash_month).padStart(2, "0")}`;
  }
  if (p.crash_hour != null && p.crash_hour >= 0) {
    return `${datePart}, ${String(p.crash_hour).padStart(2, "0")}:00`;
  }
  return datePart;
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

export function CrashDetailCard({ crash, metric, onClose }: Props) {
  const occ = crash.n_occupant_records ?? 0;
  const nm = crash.n_nonmotorist_records ?? 0;
  const veh = crash.n_vehicle_records ?? 0;
  const involved = occ + nm;
  const congProp =
    crash.cost_congestion != null || crash.cost_propdamage != null
      ? (crash.cost_congestion ?? 0) + (crash.cost_propdamage ?? 0)
      : null;

  return (
    <aside className="crash-detail-card" aria-label="Crash detail">
      <div className="crash-detail-header">
        <h2>Crash {crash.report_number}</h2>
        <button type="button" className="crash-detail-close" onClick={onClose} aria-label="Close">
          ×
        </button>
      </div>
      <dl className="crash-detail-grid">
        <div>
          <dt>Date & time</dt>
          <dd>{crashDateTimeLabel(crash)}</dd>
        </div>
        <div>
          <dt>Type</dt>
          <dd>{TYPE_LABELS[crash.crash_type] ?? crash.crash_type}</dd>
        </div>
        <div className="crash-detail-wide">
          <dt>Involvement</dt>
          <dd>
            {involved} people directly affected ({occ} occupants, {nm} pedestrians/cyclists),{" "}
            {veh} vehicles
          </dd>
        </div>
        <div>
          <dt>Fatalities | Injuries</dt>
          <dd>
            {formatNumber(crash.n_fatalities_person)} | {formatNumber(crash.n_injuries_person)}
          </dd>
        </div>
        {metric && (
          <div>
            <dt>{metric.label}</dt>
            <dd>{formatMetric(crashMetricValue(crash, metric), metric)}</dd>
          </div>
        )}
        <div>
          <dt>Medical cost</dt>
          <dd>{formatCurrency(crash.cost_medical)}</dd>
        </div>
        <div>
          <dt>Congestion + property</dt>
          <dd>{congProp === null ? "—" : formatCurrency(congProp)}</dd>
        </div>
        <div>
          <dt>Total economic</dt>
          <dd>{formatCurrency(crash.cost_total_economic)}</dd>
        </div>
        <div>
          <dt>QALYs cost</dt>
          <dd>{formatCurrency(crash.cost_qalys)}</dd>
        </div>
        <div>
          <dt>Comprehensive</dt>
          <dd>{formatCurrency(crash.cost_total)}</dd>
        </div>
        <div>
          <dt>Tract</dt>
          <dd>{crash.tract_name ?? crash.GEOID_tract ?? "—"}</dd>
        </div>
      </dl>
    </aside>
  );
}

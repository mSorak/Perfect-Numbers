import type { MetricDef } from "../types";
import type { Scale } from "../colorScale";
import { formatMetric } from "../format";
import { CRASH_TYPE_COLORS } from "../config";

interface Props {
  metric: MetricDef | undefined;
  scale: Scale | null;
  showCrashLegend: boolean;
}

export function Legend({ metric, scale, showCrashLegend }: Props) {
  return (
    <div className="panel legend-panel">
      <h2>{metric?.label ?? "Primary metric"}</h2>
      {scale ? (
        <>
          <div className="legend-ramp">
            {scale.colors.map((c, i) => (
              <div
                key={i}
                style={{ flex: 1, background: `rgb(${c[0]},${c[1]},${c[2]})` }}
              />
            ))}
          </div>
          <div className="legend-scale">
            <span>{formatMetric(scale.min, metric)}</span>
            <span>{formatMetric(scale.max, metric)}</span>
          </div>
        </>
      ) : (
        <div style={{ color: "var(--text-muted)" }}>No data to scale.</div>
      )}

      {metric?.description && (
        <p style={{ marginTop: 8, color: "var(--text-muted)", fontSize: 12 }}>
          {metric.description}
        </p>
      )}

      {showCrashLegend && (
        <div style={{ marginTop: 10, borderTop: "1px solid #eee", paddingTop: 8 }}>
          <div className="label-text" style={{ textTransform: "none", color: "var(--text-muted)" }}>
            Individual crashes (size ∝ total cost)
          </div>
          <div style={{ display: "flex", gap: 12, marginTop: 6, fontSize: 12 }}>
            <span>
              <Swatch color={CRASH_TYPE_COLORS.fatal} /> Fatal
            </span>
            <span>
              <Swatch color={CRASH_TYPE_COLORS.injury} /> Injury
            </span>
            <span>
              <Swatch color={CRASH_TYPE_COLORS.property_damage} /> Property
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

function Swatch({ color }: { color: [number, number, number] }) {
  const fill = `rgb(${color[0]},${color[1]},${color[2]})`;
  const common = { width: 14, height: 14, verticalAlign: "middle" as const, marginRight: 2 };
  return (
    <svg {...common} viewBox="0 0 32 32">
      <circle cx="16" cy="16" r="10" fill={fill} stroke="#111" strokeWidth="2" />
    </svg>
  );
}

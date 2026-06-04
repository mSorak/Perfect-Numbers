import type { Level } from "../types";

interface Props {
  zoom: number;
  level: Level;
  summaryFeatureCount: number;
  crashesVisible: boolean;
  crashCount: number;
  loading: boolean;
}

const LEVEL_LABELS: Record<Level, string> = {
  county: "County",
  place: "Census Place / CDP",
  tract: "Census Tract",
};

export function StatusPanel({
  zoom,
  level,
  summaryFeatureCount,
  crashesVisible,
  crashCount,
  loading,
}: Props) {
  return (
    <div className="panel status-panel">
      <h2>Map state</h2>
      <div className="kv">
        <span>Zoom</span>
        <span>{zoom.toFixed(2)}</span>
      </div>
      <div className="kv">
        <span>Level</span>
        <span>{LEVEL_LABELS[level]}</span>
      </div>
      <div className="kv">
        <span>Features</span>
        <span>{summaryFeatureCount}</span>
      </div>
      <div className="kv">
        <span>Crashes in view</span>
        <span>{crashesVisible ? crashCount.toLocaleString() : "—"}</span>
      </div>
      {loading && <div style={{ fontSize: 12, color: "var(--text-muted)" }}>Loading…</div>}
    </div>
  );
}

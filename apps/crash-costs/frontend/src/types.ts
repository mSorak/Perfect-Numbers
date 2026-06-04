export type Level = "county" | "place" | "tract";
export type GeoLevel = Level | "state";
export type CrashType = "fatal" | "injury" | "property_damage";

export interface SelectedGeo {
  key: string;
  level: GeoLevel;
  geoid: string;
  name: string;
}

export interface MetricDef {
  id: string;
  label: string;
  format: "currency" | "number" | "rate" | "percent";
  denominator: string | null;
  rate_per: number | null;
  description: string;
}

export interface Metadata {
  years: number[];
  months: number[];
  crash_types: CrashType[];
  cost_components: string[];
  min_crash_date: string | null;
  max_crash_date: string | null;
  metrics: MetricDef[];
  default_metric: string;
  levels: Level[];
}

export interface SummaryFeature {
  geoid: string;
  value: number | null;
  n_crashes: number;
  n_fatal: number;
  n_injury: number;
  n_property_damage: number;
  sum_fatalities_person: number | null;
  sum_injuries_person: number | null;
  sum_cost_total: number | null;
  sum_cost_medical: number | null;
  sum_cost_ems: number | null;
  sum_cost_congestion: number | null;
  sum_cost_propdamage: number | null;
  sum_cost_cong_propdamage: number | null;
  sum_cost_total_economic: number | null;
  sum_cost_qalys: number | null;
  sum_occupants: number | null;
  sum_nonmotorists: number | null;
  sum_vehicles: number | null;
  population: number | null;
  vehicles_per_person: number | null;
  pct_hh_no_vehicle: number | null;
  [key: string]: unknown;
}

export interface SummaryResponse {
  level: GeoLevel;
  metric: string;
  filters: {
    years: number[];
    months: number[];
    crash_types: CrashType[];
    date_from: string | null;
    date_to: string | null;
    nonmotorist: boolean;
  };
  features: SummaryFeature[];
}

export interface CrashPoint {
  report_number: string;
  lat: number;
  lon: number;
  crash_type: CrashType;
  severity_code: number;
  crash_year: number;
  crash_month: number;
  crash_hour: number | null;
  crash_date: string | null;
  n_occupant_records: number | null;
  n_nonmotorist_records: number | null;
  n_vehicle_records: number | null;
  n_fatalities_person: number | null;
  n_injuries_person: number | null;
  cost_total: number | null;
  cost_medical: number | null;
  cost_congestion: number | null;
  cost_propdamage: number | null;
  cost_total_economic: number | null;
  cost_qalys: number | null;
  GEOID_tract: string | null;
  tract_name: string | null;
}

export interface CrashesResponse {
  count: number;
  limit: number;
  points: CrashPoint[];
}

export interface Filters {
  dateFrom: string;
  dateTo: string;
  crashTypes: CrashType[];
  nonmotoristInvolved: boolean;
  metric: string;
}

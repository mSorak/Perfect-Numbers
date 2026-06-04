import type { MetricDef } from "./types";

const currencyFmt = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  maximumFractionDigits: 0,
});

const numberFmt = new Intl.NumberFormat("en-US");
const decimalFmt = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 });

export function formatMetric(value: number | null | undefined, metric: MetricDef | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  if (!metric) return numberFmt.format(value);
  switch (metric.format) {
    case "currency":
      return currencyFmt.format(value);
    case "rate":
      return `${decimalFmt.format(value)} / ${metric.rate_per ?? 1}`;
    case "percent":
      return `${decimalFmt.format(value)}%`;
    case "number":
    default:
      return numberFmt.format(value);
  }
}

export function formatCurrency(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return currencyFmt.format(v);
}

export function formatNumber(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return numberFmt.format(v);
}

export function formatPerCapita(sum: number | null, pop: number | null, per = 1): string {
  if (sum === null || pop === null || !pop) return "—";
  return decimalFmt.format((sum / pop) * per);
}

/** Total divided by population, shown as currency (per person). */
export function formatPerCapitaCurrency(sum: number | null, pop: number | null): string {
  if (sum === null || pop === null || !pop) return "—";
  return currencyFmt.format(sum / pop);
}

import type { CrashType, Filters } from "./types";

export interface FilterArgs {
  dateFrom?: string;
  dateTo?: string;
  crashTypes: CrashType[];
  nonmotoristInvolved: boolean;
}

/** Stable key for effect dependencies. */
export function filterArgsKey(args: FilterArgs): string {
  return JSON.stringify({
    dateFrom: args.dateFrom ?? "",
    dateTo: args.dateTo ?? "",
    crashTypes: [...args.crashTypes].sort(),
    nonmotoristInvolved: args.nonmotoristInvolved,
  });
}

export function buildFilterArgs(filters: Filters): FilterArgs {
  const from = filters.dateFrom?.trim() ?? "";
  const to = filters.dateTo?.trim() ?? "";
  const hasRange = Boolean(from && to);
  const rangeValid = !hasRange || from <= to;

  return {
    dateFrom: hasRange && rangeValid ? from : undefined,
    dateTo: hasRange && rangeValid ? to : undefined,
    crashTypes: filters.crashTypes,
    nonmotoristInvolved: filters.nonmotoristInvolved,
  };
}

export function isDateRangeInvalid(filters: Filters): boolean {
  const from = filters.dateFrom?.trim() ?? "";
  const to = filters.dateTo?.trim() ?? "";
  return Boolean(from && to && from > to);
}

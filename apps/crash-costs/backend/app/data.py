"""DuckDB-backed data access for the crash-cost API.

A single persistent in-memory DuckDB connection registers the prepared
parquet file as a view. Queries compose a WHERE clause from filters and a
GROUP BY on the level's GEOID column.

All numerics aggregated in SQL; per-capita / per-crash metric math happens
in :mod:`metrics` after joining with the per-feature population from the
prepared GeoJSON.
"""

from __future__ import annotations

import json
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import duckdb

from .config import CRASHES_PARQUET, GEO_CACHE, META_JSON

LEVEL_GEOID = {
    "county": "GEOID_county",
    "place": "GEOID_place",
    "tract": "GEOID_tract",
}

VALID_CRASH_TYPES = {"fatal", "injury", "property_damage"}


_connection: duckdb.DuckDBPyConnection | None = None

# A single DuckDBPyConnection is NOT safe for concurrent queries from multiple
# threads. FastAPI runs sync endpoints in a threadpool and the frontend fires
# several summary/crashes requests at once, so we serialize the execute+fetch
# pair behind this lock. Queries are tens of ms, so the throughput cost is
# negligible compared to the connection corruption (and worker crashes) that
# unsynchronized concurrent access causes.
_query_lock = threading.Lock()


def _parquet_path_sql_literal(path: Path | str) -> str:
    """Single-quoted SQL literal; forward slashes for Windows paths in DuckDB."""
    p = Path(path).resolve().as_posix().replace("'", "''")
    return f"'{p}'"


def get_connection() -> duckdb.DuckDBPyConnection:
    global _connection
    if _connection is None:
        if not CRASHES_PARQUET.exists():
            raise FileNotFoundError(
                f"{CRASHES_PARQUET} not found. Run `python prepare_data.py` first."
            )
        con = duckdb.connect(database=":memory:")
        # Prepared ? params are not allowed on CREATE VIEW + read_parquet in current DuckDB.
        pq = _parquet_path_sql_literal(CRASHES_PARQUET)
        con.execute(f"CREATE VIEW crashes AS SELECT * FROM read_parquet({pq})")
        _connection = con
    return _connection


def run_query(sql: str, params: list[Any]) -> tuple[list[str], list[tuple]]:
    """Execute a query and fetch all rows atomically under the shared lock.

    Returns (column_names, rows). Holding the lock across execute + fetchall is
    required: ``con.execute`` stores the active result on the connection, so a
    second thread's execute would clobber it mid-fetch.
    """
    con = get_connection()
    with _query_lock:
        rel = con.execute(sql, params)
        cols = [d[0] for d in rel.description]
        rows = rel.fetchall()
    return cols, rows


@lru_cache(maxsize=1)
def load_meta() -> dict[str, Any]:
    if not META_JSON.exists():
        return {"years": [], "months": [], "crash_types": [], "cost_components": []}
    return json.loads(META_JSON.read_text())


@lru_cache(maxsize=3)
def load_geojson_raw(level: str) -> str:
    path = GEO_CACHE / f"{level}.geojson"
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run `python prepare_data.py` first.")
    return path.read_text()


def _build_where(
    years: Iterable[int] | None,
    months: Iterable[int] | None,
    crash_types: Iterable[str] | None,
    date_from: str | None = None,
    date_to: str | None = None,
    nonmotorist_only: bool = False,
) -> tuple[str, list[Any]]:
    clauses: list[str] = []
    params: list[Any] = []

    if date_from and date_to:
        clauses.append("CAST(crash_date AS DATE) BETWEEN CAST(? AS DATE) AND CAST(? AS DATE)")
        params.extend([date_from, date_to])
    else:
        years = list(years) if years else []
        if years:
            clauses.append(f"crash_year IN ({','.join(['?'] * len(years))})")
            params.extend(int(y) for y in years)

        months = list(months) if months else []
        if months:
            clauses.append(f"crash_month IN ({','.join(['?'] * len(months))})")
            params.extend(int(m) for m in months)

    crash_types = [c for c in (crash_types or []) if c in VALID_CRASH_TYPES]
    if crash_types:
        clauses.append(f"crash_type IN ({','.join(['?'] * len(crash_types))})")
        params.extend(crash_types)

    if nonmotorist_only:
        clauses.append("nonmotorist = TRUE")

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    return where, params


AGG_SELECT = """
    SELECT
        {geo_col} AS geoid,
        COUNT(*) AS n_crashes,
        SUM(CASE WHEN severity_code = 1 THEN 1 ELSE 0 END) AS n_fatal,
        SUM(CASE WHEN severity_code = 2 THEN 1 ELSE 0 END) AS n_injury,
        SUM(CASE WHEN severity_code = 3 THEN 1 ELSE 0 END) AS n_property_damage,
        SUM(cost_total) AS sum_cost_total,
        SUM(cost_medical) AS sum_cost_medical,
        SUM(cost_ems) AS sum_cost_ems,
        SUM(cost_marketprod) AS sum_cost_marketprod,
        SUM(cost_householdprod) AS sum_cost_householdprod,
        SUM(cost_insuranceadmin) AS sum_cost_insuranceadmin,
        SUM(cost_workplacecosts) AS sum_cost_workplacecosts,
        SUM(cost_legalcosts) AS sum_cost_legalcosts,
        SUM(cost_congestion) AS sum_cost_congestion,
        SUM(cost_propdamage) AS sum_cost_propdamage,
        SUM(COALESCE(cost_congestion, 0) + COALESCE(cost_propdamage, 0)) AS sum_cost_cong_propdamage,
        SUM(cost_total_economic) AS sum_cost_total_economic,
        SUM(cost_qalys) AS sum_cost_qalys,
        SUM(cost_totalcomp) AS sum_cost_totalcomp,
        SUM(n_occupant_records) AS sum_occupants,
        SUM(n_nonmotorist_records) AS sum_nonmotorists,
        SUM(n_vehicle_records) AS sum_vehicles,
        SUM(n_fatalities_person) AS sum_fatalities_person,
        SUM(n_injuries_person) AS sum_injuries_person
    FROM crashes
    {where}
    GROUP BY {geo_col}
"""

STATE_AGG_SELECT = """
    SELECT
        COUNT(*) AS n_crashes,
        SUM(CASE WHEN severity_code = 1 THEN 1 ELSE 0 END) AS n_fatal,
        SUM(CASE WHEN severity_code = 2 THEN 1 ELSE 0 END) AS n_injury,
        SUM(CASE WHEN severity_code = 3 THEN 1 ELSE 0 END) AS n_property_damage,
        SUM(cost_total) AS sum_cost_total,
        SUM(cost_medical) AS sum_cost_medical,
        SUM(cost_ems) AS sum_cost_ems,
        SUM(cost_marketprod) AS sum_cost_marketprod,
        SUM(cost_householdprod) AS sum_cost_householdprod,
        SUM(cost_insuranceadmin) AS sum_cost_insuranceadmin,
        SUM(cost_workplacecosts) AS sum_cost_workplacecosts,
        SUM(cost_legalcosts) AS sum_cost_legalcosts,
        SUM(cost_congestion) AS sum_cost_congestion,
        SUM(cost_propdamage) AS sum_cost_propdamage,
        SUM(COALESCE(cost_congestion, 0) + COALESCE(cost_propdamage, 0)) AS sum_cost_cong_propdamage,
        SUM(cost_total_economic) AS sum_cost_total_economic,
        SUM(cost_qalys) AS sum_cost_qalys,
        SUM(cost_totalcomp) AS sum_cost_totalcomp,
        SUM(n_occupant_records) AS sum_occupants,
        SUM(n_nonmotorist_records) AS sum_nonmotorists,
        SUM(n_vehicle_records) AS sum_vehicles,
        SUM(n_fatalities_person) AS sum_fatalities_person,
        SUM(n_injuries_person) AS sum_injuries_person
    FROM crashes
    {where}
"""

MARYLAND_STATE_GEOID = "24"


def aggregate_state(
    years: Iterable[int] | None = None,
    months: Iterable[int] | None = None,
    crash_types: Iterable[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    nonmotorist_only: bool = False,
) -> dict[str, Any] | None:
    """Single-row aggregate for all of Maryland (no geographic GROUP BY)."""
    where, params = _build_where(years, months, crash_types, date_from, date_to, nonmotorist_only)
    sql = STATE_AGG_SELECT.format(where=where)
    cols, rows = run_query(sql, params)
    if not rows:
        return None
    rec = dict(zip(cols, rows[0]))
    rec["geoid"] = MARYLAND_STATE_GEOID
    return rec


def aggregate_by_geo(
    level: str,
    years: Iterable[int] | None = None,
    months: Iterable[int] | None = None,
    crash_types: Iterable[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    nonmotorist_only: bool = False,
) -> list[dict[str, Any]]:
    if level not in LEVEL_GEOID:
        raise ValueError(f"unknown level: {level}")

    where, params = _build_where(years, months, crash_types, date_from, date_to, nonmotorist_only)
    sql = AGG_SELECT.format(geo_col=LEVEL_GEOID[level], where=where)
    cols, rows = run_query(sql, params)
    out: list[dict[str, Any]] = []
    for row in rows:
        rec = dict(zip(cols, row))
        if rec["geoid"] is None:
            continue
        out.append(rec)
    return out


def fetch_crashes_in_bbox(
    west: float,
    south: float,
    east: float,
    north: float,
    years: Iterable[int] | None = None,
    months: Iterable[int] | None = None,
    crash_types: Iterable[str] | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    nonmotorist_only: bool = False,
    limit: int = 50_000,
) -> list[dict[str, Any]]:
    where, params = _build_where(years, months, crash_types, date_from, date_to, nonmotorist_only)
    extra = "lon BETWEEN ? AND ? AND lat BETWEEN ? AND ?"
    where_full = (where + " AND " + extra) if where else ("WHERE " + extra)
    params = [*params, west, east, south, north]

    sql = f"""
        SELECT
            report_number,
            lat, lon,
            crash_type, severity_code,
            crash_year, crash_month, crash_hour,
            CAST(crash_date AS VARCHAR) AS crash_date,
            n_occupant_records,
            n_nonmotorist_records,
            n_vehicle_records,
            n_fatalities_person,
            n_injuries_person,
            cost_total,
            cost_medical,
            cost_congestion,
            cost_propdamage,
            cost_total_economic,
            cost_qalys,
            GEOID_tract,
            tract_name
        FROM crashes
        {where_full}
        LIMIT ?
    """
    params.append(int(limit))
    cols, rows = run_query(sql, params)
    return [dict(zip(cols, row)) for row in rows]

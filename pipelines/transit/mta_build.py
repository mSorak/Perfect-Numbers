"""Staging for MTA ridership: iMAP stop ridership, CX dashboard (Power BI) route/mode tables, NTD monthly."""

import pandas as pd

from pndata.powerbi import decode_dsr


def stop_ridership(con, ctx):
    p = (ctx.raw("md_imap_transit/mta_bus_stops") / "features.geojson").as_posix()
    snap = ctx.raw_inputs["md_imap_transit/mta_bus_stops"]["snapshot_id"]
    return f"""SELECT Stop_ID::VARCHAR AS stop_id, stop_name, Routes_Served AS routes_served,
                      Rider_On::DOUBLE AS boardings, Rider_Off::DOUBLE AS alightings, Rider_Total::DOUBLE AS boardings_alightings,
                      Stop_Ridership_Rank::INT AS ridership_rank, Shelter AS shelter, County AS county, Mode AS mode,
                      '{snap}' AS source_snapshot_id, geom AS geometry
               FROM ST_Read('{p}')"""


def _pbi(ctx, entity: str) -> pd.DataFrame:
    cols, rows = decode_dsr(ctx.raw(f"mta_cx_powerbi/{entity}") / "querydata.json")
    return pd.DataFrame(rows, columns=cols)


def mta_route(con, ctx):
    df = _pbi(ctx, "dim_route")
    modes = _pbi(ctx, "dim_mode")[["mode_id", "mode_name"]]
    df = df.merge(modes, on="mode_id", how="left")
    for c in ("route_id", "route_id_gtfs", "route_short_name", "line_abbr_trapeze"):
        df[c] = df[c].astype("string")
    return df[["route_id", "route_short_name", "route_long_name", "mode_id", "mode_name", "route_type",
               "route_id_gtfs", "line_abbr_trapeze", "location"]]


def ridership_route_month(con, ctx):
    df = _pbi(ctx, "route_ridership")
    df["route_id"] = df["route_id"].astype("string").fillna("UNASSIGNED")
    df["month"] = pd.to_datetime(df["month_start"]).dt.date
    df["source_snapshot_id"] = ctx.raw_inputs["mta_cx_powerbi/route_ridership"]["snapshot_id"]
    return df[["route_id", "mode_id", "month", "riders", "average_daily_riders", "average_weekday_riders",
               "average_saturday_riders", "average_sunday_or_holiday_riders", "source_snapshot_id"]]


def ntd_monthly(con, ctx):
    p = (ctx.raw("fta_ntd/monthly_ridership_md") / "8bui-9xvu.csv").as_posix()
    return f"""SELECT ntd_id, agency, mode, tos AS type_of_service, _3_mode AS mode_group,
                      strptime(left(date, 10), '%Y-%m-%d')::DATE AS month,
                      TRY_CAST(upt AS BIGINT) AS unlinked_trips, TRY_CAST(vrm AS BIGINT) AS vehicle_revenue_miles,
                      TRY_CAST(vrh AS BIGINT) AS vehicle_revenue_hours, TRY_CAST(voms AS INTEGER) AS vehicles_operated_max,
                      uza_name, state
               FROM read_csv('{p}', all_varchar=true, header=true)"""

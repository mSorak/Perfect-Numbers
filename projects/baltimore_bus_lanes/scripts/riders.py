"""Estimated weekday bus riders passing each Baltimore City street segment (MTA local bus).

ESTIMATES, not published counts. Two versions (see ../README.md, "Riders by segment"):

riders_v1  load profile. For each route pattern (route × shape × direction) running on the sample weekday:
           1. allocate each stop's average weekday boardings/alightings (transit.stop_ridership, all routes) to the
              patterns serving that stop in proportion to their scheduled trips;
           2. no alighting at a pattern's first stop and no boarding at its last; scale alightings so they equal
              boardings; load after stop k = cumulative (ons − offs), floored at 0;
           3. scale each route so its stop-based boardings equal its CX average weekday riders over the last
              12 months (transit.mta_ridership_route_month);
           4. credit each inter-stop link's load to the street segments between those stops along the shape.
exposure_v1 upper bound. Σ over patterns of route riders × (pattern trips ÷ route trips): assumes every rider
           rides the whole route.

Circulator riders are not estimated (no route or stop counts exist).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import shapely

import pndata as pn
from pndata.geo import match_lines_to_segments, to_gdf

METHOD = "riders_v1"
WEEKDAY = "2026-10-14"
MONTHS = 12


def _patterns(con) -> pd.DataFrame:
    return con.sql(f"""
        SELECT t.route_id, t.shape_id, coalesce(t.direction_id, -1) AS direction_id, count(*) AS n_trips,
               min(t.trip_id) AS rep_trip
        FROM transit.gtfs_trip t JOIN transit.gtfs_service_date s USING (service_id)
        WHERE s.date = DATE '{WEEKDAY}'
        GROUP BY ALL""").df()


def _route_riders(con) -> pd.DataFrame:
    return con.sql(f"""
        WITH latest AS (SELECT max(month) AS m FROM transit.mta_ridership_route_month)
        SELECT r.route_id_gtfs AS route_id, avg(rm.average_weekday_riders) AS route_riders,
               min(rm.month) AS first_month, max(rm.month) AS last_month
        FROM transit.mta_ridership_route_month rm JOIN transit.mta_route r USING (route_id), latest
        WHERE rm.month > latest.m - INTERVAL {MONTHS} MONTH AND r.route_id_gtfs IS NOT NULL
        GROUP BY 1""").df()


def estimate(con=None) -> tuple[pd.DataFrame, dict]:
    """Return (per-segment estimates, diagnostics)."""
    con = con or pn.connect()
    pats = _patterns(con)
    con.register("_pats", pats)
    seq = con.sql("""SELECT p.route_id, p.shape_id, p.direction_id, st.stop_id, st.stop_sequence
                     FROM _pats p JOIN transit.gtfs_stop_time st ON st.trip_id = p.rep_trip
                     ORDER BY 1, 2, 3, 5""").df()
    sr = con.sql("SELECT stop_id, boardings, alightings FROM transit.stop_ridership").df()
    rr = _route_riders(con)

    key = ["route_id", "shape_id", "direction_id"]
    seq = seq.merge(pats[key + ["n_trips"]], on=key)
    seq["k"] = seq.groupby(key).cumcount()
    seq["n_stops"] = seq.groupby(key)["k"].transform("size")
    seq = seq.merge(sr, on="stop_id", how="left").fillna({"boardings": 0.0, "alightings": 0.0})
    seq["share"] = seq["n_trips"] / seq.groupby("stop_id")["n_trips"].transform("sum")
    seq["ons"] = np.where(seq["k"] == seq["n_stops"] - 1, 0.0, seq["boardings"] * seq["share"])
    seq["offs"] = np.where(seq["k"] == 0, 0.0, seq["alightings"] * seq["share"])
    g = seq.groupby(key)
    tot_on, tot_off = g["ons"].transform("sum"), g["offs"].transform("sum")
    seq["offs"] = np.where(tot_off > 0, seq["offs"] * tot_on / tot_off.where(tot_off > 0, 1), 0.0)

    # route scaling to CX riders
    route_ons = seq.groupby("route_id")["ons"].sum().rename("stop_based_ons").reset_index()
    scale = route_ons.merge(rr, on="route_id", how="left")
    scale["factor"] = scale["route_riders"] / scale["stop_based_ons"].where(scale["stop_based_ons"] > 0)
    seq = seq.merge(scale[["route_id", "factor"]], on="route_id", how="left")
    seq["load"] = (seq["ons"] - seq["offs"]).groupby([seq[c] for c in key]).cumsum().clip(lower=0) * seq["factor"]

    # stop positions along each shape
    shapes = to_gdf(con, "SELECT shape_id, geometry FROM transit.gtfs_shape WHERE shape_id IN (SELECT shape_id FROM _pats)")
    stops = to_gdf(con, "SELECT stop_id, geometry FROM transit.gtfs_stop")
    sg = shapes.set_index("shape_id").geometry
    st_geom = stops.set_index("stop_id").geometry
    merged = shapely.line_merge(sg.loc[seq["shape_id"]].to_numpy())
    seq["pos"] = shapely.line_locate_point(merged, st_geom.reindex(seq["stop_id"]).to_numpy(), normalized=True)

    # segment matches (same parameters as transit.bus_segment_service)
    segs = to_gdf(con, """SELECT segment_id, geometry FROM traffic.street_segment
                          WHERE feature_status = 'A' AND coalesce(subtype_code, '') <> 'STRALY' AND length_m > 5""")
    m = match_lines_to_segments(segs, shapes.rename(columns={"shape_id": "line_id"}), buffer_m=10, min_share=0.6,
                                max_angle=30).rename(columns={"line_id": "shape_id"})

    rows = []
    for (route_id, shape_id, direction_id), s in seq.groupby(key, sort=False):
        ms = m[m["shape_id"] == shape_id]
        if ms.empty or s["factor"].isna().all():
            continue
        pos = np.maximum.accumulate(s["pos"].to_numpy())       # monotone along the trip
        link = np.searchsorted(pos, ms["position"].to_numpy(), side="right") - 1
        valid = (link >= 0) & (link < len(s) - 1)               # before the first or after the last stop: no riders
        load = np.where(valid, s["load"].to_numpy()[np.clip(link, 0, len(s) - 1)], 0.0)
        rows.append(pd.DataFrame({"segment_id": ms["segment_id"].to_numpy(), "route_id": route_id,
                                  "same_direction": ms["same_direction"].to_numpy(), "load": load,
                                  "n_trips": s["n_trips"].iloc[0], "shape_id": shape_id}))
    seg = pd.concat(rows, ignore_index=True)
    # a segment can match a shape twice (loops); keep one per pattern
    seg = seg.drop_duplicates(["segment_id", "shape_id", "same_direction"])

    route_trips = pats.groupby("route_id")["n_trips"].sum().rename("route_trips")
    seg = seg.join(route_trips, on="route_id").merge(rr[["route_id", "route_riders"]], on="route_id", how="left")
    seg["exposure"] = seg["route_riders"] * seg["n_trips"] / seg["route_trips"]

    out = seg.groupby("segment_id").apply(lambda d: pd.Series({
        "riders_v1_with": d.loc[d["same_direction"], "load"].sum(),
        "riders_v1_against": d.loc[~d["same_direction"], "load"].sum(),
        "exposure_v1": d["exposure"].sum(),
    }), include_groups=False).reset_index()
    out["riders_v1_both"] = out["riders_v1_with"] + out["riders_v1_against"]
    out["riders_v1_max_direction"] = out[["riders_v1_with", "riders_v1_against"]].max(axis=1)

    diag = {
        "method": METHOD, "weekday": WEEKDAY,
        "route_riders_window": f"{rr['first_month'].min():%Y-%m} to {rr['last_month'].max():%Y-%m}",
        "stop_ridership_season": "Summer 2024 (iMAP)",
        "n_patterns": len(pats), "n_routes_scaled": int(scale["factor"].notna().sum()),
        "routes_without_cx_riders": sorted(scale.loc[scale["factor"].isna(), "route_id"].astype(str)),
        "scale_factor_median": float(scale["factor"].median()),
        "scale_factor_p10_p90": [float(scale["factor"].quantile(.1)), float(scale["factor"].quantile(.9))],
        "total_route_riders": float(rr.loc[rr["route_id"].isin(pats["route_id"]), "route_riders"].sum()),
    }
    return out, diag


if __name__ == "__main__":
    import json
    est, d = estimate()
    print(json.dumps(d, indent=1, default=str))
    print(est.describe().T)

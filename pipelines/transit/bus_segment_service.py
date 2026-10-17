"""Bus service on Baltimore City street segments, by operator, day type and time band (or clock hour).

Method (documented in the cards):
1. Street segments = active, non-alley city centerline segments.
2. Each GTFS shape used on the representative service dates is matched to the segments it runs ALONG
   (pndata.geo.match_lines_to_segments: ≥60% of the segment within 10 m of the shape AND bearing within 30°).
3. Each scheduled trip passes the segment at a time interpolated linearly between the trip's first departure
   and last arrival, by the segment's position along the shape.
4. Passes are counted per segment × operator × day type × time band (or hour) × direction relative to the
   segment's digitized direction ("with" / "against").

Operators: MTA local bus (transit.gtfs_*) and the Charm City Circulator (transit.ccc_gtfs_*).
"""

import pandas as pd

from pndata.geo import match_lines_to_segments, to_gdf

BANDS = [  # (name, start_hour, end_hour)
    ("early", 4, 6), ("am_peak", 6, 9), ("midday", 9, 15), ("pm_peak", 15, 19), ("evening", 19, 24), ("night", 24, 28),
]
FEEDS = {"MTA": "transit.gtfs_", "Circulator": "transit.ccc_gtfs_"}  # operator -> table prefix


def _params(ctx):
    p = ctx.card.get("parameters", {})
    return (p.get("service_dates", {"weekday": "2026-10-14", "saturday": "2026-10-17", "sunday": "2026-10-18"}),
            p.get("buffer_m", 10), p.get("min_share", 0.6), p.get("max_angle", 30))


def _segments(con):
    return to_gdf(con, """SELECT segment_id, geometry FROM traffic.street_segment
                          WHERE feature_status = 'A' AND coalesce(subtype_code, '') <> 'STRALY' AND length_m > 5""")


def segment_matches(con, ctx, prefix: str = "transit.gtfs_", segs=None):
    """Shape ↔ segment matches for one feed (shared with the summary mart)."""
    dates, buffer_m, min_share, max_angle = _params(ctx)
    date_list = ", ".join(f"DATE '{d}'" for d in dates.values())
    segs = _segments(con) if segs is None else segs
    shapes = to_gdf(con, f"""SELECT shape_id AS line_id, geometry FROM {prefix}shape
                             WHERE shape_id IN (SELECT DISTINCT t.shape_id FROM {prefix}trip t
                                 JOIN {prefix}service_date s USING (service_id) WHERE s.date IN ({date_list}))""")
    return match_lines_to_segments(segs, shapes, buffer_m=buffer_m, min_share=min_share, max_angle=max_angle)


def passes_sql(con, ctx) -> str:
    """Register matches and dates; return SQL for one row per scheduled pass:
    (operator, day_type, segment_id, route_short_name, same_direction, pass_s)."""
    dates, *_ = _params(ctx)
    segs = _segments(con)
    con.register("_dates", pd.DataFrame({"day_type": list(dates), "date": pd.to_datetime(list(dates.values())).date}))
    parts = []
    for i, (operator, prefix) in enumerate(FEEDS.items()):
        m = segment_matches(con, ctx, prefix, segs).rename(columns={"line_id": "shape_id"})
        con.register(f"_match{i}", m)
        parts.append(f"""
        SELECT '{operator}' AS operator, d.day_type, m.segment_id, r.route_short_name, m.same_direction,
               sp.t0 + m.position * (sp.t1 - sp.t0) AS pass_s
        FROM {prefix}trip t
        JOIN {prefix}service_date s USING (service_id)
        JOIN _dates d ON d.date = s.date
        JOIN (SELECT trip_id, min(departure_s) AS t0, max(arrival_s) AS t1
              FROM {prefix}stop_time GROUP BY trip_id) sp USING (trip_id)
        JOIN _match{i} m USING (shape_id)
        JOIN {prefix}route r USING (route_id)""")
    return "\nUNION ALL\n".join(parts)


def build(con, ctx):
    passes = passes_sql(con, ctx)
    con.register("_bands", pd.DataFrame(BANDS, columns=["time_band", "start_h", "end_h"]))
    return f"""
    WITH passes AS ({passes}),
    banded AS (
        SELECT p.*, b.time_band, b.end_h - b.start_h AS band_hours
        FROM passes p JOIN _bands b ON p.pass_s >= b.start_h * 3600 AND p.pass_s < b.end_h * 3600)
    SELECT segment_id, operator, day_type, time_band, any_value(band_hours) AS band_hours,
           count(*)                                        AS n_bus_passes,
           count(*) FILTER (WHERE same_direction)          AS n_passes_with,
           count(*) FILTER (WHERE NOT same_direction)      AS n_passes_against,
           greatest(count(*) FILTER (WHERE same_direction), count(*) FILTER (WHERE NOT same_direction))
               / any_value(band_hours)                     AS buses_per_hour_max_direction,
           count(*) / any_value(band_hours)                AS buses_per_hour_both_directions,
           count(DISTINCT route_short_name)                AS n_routes,
           list(DISTINCT route_short_name ORDER BY route_short_name) AS routes
    FROM banded
    GROUP BY segment_id, operator, day_type, time_band
    """


def build_hour(con, ctx):
    """Passes per segment × operator × day type × clock hour (hour 0–27 after service-day midnight)."""
    passes = passes_sql(con, ctx)
    return f"""
    WITH passes AS ({passes})
    SELECT segment_id, operator, day_type, floor(pass_s / 3600)::INT AS hour,
           count(*)                                   AS n_bus_passes,
           count(*) FILTER (WHERE same_direction)     AS n_passes_with,
           count(*) FILTER (WHERE NOT same_direction) AS n_passes_against,
           list(DISTINCT route_short_name ORDER BY route_short_name) AS routes
    FROM passes
    WHERE pass_s >= 0 AND pass_s < 28 * 3600
    GROUP BY ALL
    """

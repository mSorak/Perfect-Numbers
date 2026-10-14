"""Bus service on Baltimore City street segments, by day type and time band.

Method (documented in the card):
1. Street segments = active, non-alley city centerline segments.
2. Each GTFS shape used on the representative service dates is matched to the segments it runs ALONG
   (pndata.geo.match_lines_to_segments: ≥60% of the segment within 15 m of the shape AND bearing within 30°).
3. Each scheduled trip passes the segment at a time interpolated linearly between the trip's first departure
   and last arrival, by the segment's position along the shape.
4. Passes are counted per segment × day type × time band × direction relative to the segment's digitized
   direction ("with" / "against").
"""

import pandas as pd

from pndata.geo import match_lines_to_segments, to_gdf

BANDS = [  # (name, start_hour, end_hour)
    ("early", 4, 6), ("am_peak", 6, 9), ("midday", 9, 15), ("pm_peak", 15, 19), ("evening", 19, 24), ("night", 24, 28),
]


def _params(ctx):
    p = ctx.card.get("parameters", {})
    return (p.get("service_dates", {"weekday": "2026-10-14", "saturday": "2026-10-17", "sunday": "2026-10-18"}),
            p.get("buffer_m", 10), p.get("min_share", 0.6), p.get("max_angle", 30))


def segment_matches(con, ctx):
    """Shape ↔ segment matches (shared with the summary mart)."""
    dates, buffer_m, min_share, max_angle = _params(ctx)
    date_list = ", ".join(f"DATE '{d}'" for d in dates.values())
    segs = to_gdf(con, """SELECT segment_id, geometry FROM traffic.street_segment
                          WHERE feature_status = 'A' AND coalesce(subtype_code, '') <> 'STRALY' AND length_m > 5""")
    shapes = to_gdf(con, f"""SELECT shape_id AS line_id, geometry FROM transit.gtfs_shape
                             WHERE shape_id IN (SELECT DISTINCT t.shape_id FROM transit.gtfs_trip t
                                 JOIN transit.gtfs_service_date s USING (service_id) WHERE s.date IN ({date_list}))""")
    return match_lines_to_segments(segs, shapes, buffer_m=buffer_m, min_share=min_share, max_angle=max_angle)


def build(con, ctx):
    dates, *_ = _params(ctx)
    m = segment_matches(con, ctx).rename(columns={"line_id": "shape_id"})
    con.register("_match", m)
    con.register("_dates", pd.DataFrame({"day_type": list(dates), "date": pd.to_datetime(list(dates.values())).date}))
    con.register("_bands", pd.DataFrame(BANDS, columns=["time_band", "start_h", "end_h"]))
    return """
    WITH trips AS (
        SELECT d.day_type, t.trip_id, t.route_id, t.shape_id, t.direction_id
        FROM transit.gtfs_trip t
        JOIN transit.gtfs_service_date s USING (service_id)
        JOIN _dates d ON d.date = s.date),
    span AS (
        SELECT trip_id, min(departure_s) AS t0, max(arrival_s) AS t1 FROM transit.gtfs_stop_time GROUP BY trip_id),
    passes AS (
        SELECT tr.day_type, m.segment_id, tr.route_id, m.same_direction,
               sp.t0 + m.position * (sp.t1 - sp.t0) AS pass_s
        FROM trips tr JOIN span sp USING (trip_id) JOIN _match m USING (shape_id)),
    banded AS (
        SELECT p.*, b.time_band, b.end_h - b.start_h AS band_hours
        FROM passes p JOIN _bands b ON p.pass_s >= b.start_h * 3600 AND p.pass_s < b.end_h * 3600)
    SELECT segment_id, day_type, time_band, any_value(band_hours) AS band_hours,
           count(*)                                        AS n_bus_passes,
           count(*) FILTER (WHERE same_direction)          AS n_passes_with,
           count(*) FILTER (WHERE NOT same_direction)      AS n_passes_against,
           greatest(count(*) FILTER (WHERE same_direction), count(*) FILTER (WHERE NOT same_direction))
               / any_value(band_hours)                     AS buses_per_hour_max_direction,
           count(*) / any_value(band_hours)                AS buses_per_hour_both_directions,
           count(DISTINCT route_id)                        AS n_routes,
           list(DISTINCT r.route_short_name ORDER BY r.route_short_name) AS routes
    FROM banded JOIN transit.gtfs_route r USING (route_id)
    GROUP BY segment_id, day_type, time_band
    """

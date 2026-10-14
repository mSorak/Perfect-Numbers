"""One row per Baltimore City street segment carrying scheduled MTA bus service, with jurisdiction,
existing bus/bike facilities, stop activity and route-ridership exposure. Built for mapping and ranking."""

import pandas as pd

from pndata.geo import match_lines_to_segments, to_gdf


def build(con, ctx):
    p = ctx.card.get("parameters", {})
    stop_snap_m = p.get("stop_snap_m", 30)
    months = p.get("ridership_months", 12)

    segs = to_gdf(con, """SELECT segment_id, geometry FROM traffic.street_segment
                          WHERE segment_id IN (SELECT DISTINCT segment_id FROM transit.bus_segment_service)""")

    # Jurisdiction: SHA inventory sections running along the segment (none → local city street)
    sha = to_gdf(con, """SELECT section_id AS line_id, maintainer_group, geometry FROM traffic.road_jurisdiction
                         WHERE county_geoid = '24510'""")
    j = match_lines_to_segments(segs, sha, buffer_m=10, min_share=0.5, max_angle=30)
    j = j.merge(sha[["line_id", "maintainer_group"]], on="line_id").sort_values("share", ascending=False)
    j = j.drop_duplicates("segment_id")[["segment_id", "maintainer_group"]]

    bike = to_gdf(con, """SELECT facility_id AS line_id, facility_type, status, geometry FROM traffic.bike_facility""")
    b = match_lines_to_segments(segs, bike, buffer_m=12, min_share=0.5, max_angle=30)
    b = b.merge(bike[["line_id", "facility_type", "status"]], on="line_id").drop_duplicates("segment_id")

    lanes = to_gdf(con, """SELECT osm_way_id AS line_id, bus_lane_side, geometry FROM transit.bus_lane_existing""")
    bl = match_lines_to_segments(segs, lanes, buffer_m=12, min_share=0.5, max_angle=30)
    bl = bl.merge(lanes[["line_id", "bus_lane_side"]], on="line_id").drop_duplicates("segment_id")

    # Stop activity: each stop snapped to the nearest bus-served segment within stop_snap_m
    stops = to_gdf(con, """SELECT stop_id, boardings, alightings, geometry FROM transit.stop_ridership""")
    near = stops.sjoin_nearest(segs[["segment_id", "geometry"]], max_distance=stop_snap_m, how="inner")
    near = near.drop_duplicates("stop_id")
    act = near.groupby("segment_id").agg(n_stops=("stop_id", "count"), stop_boardings=("boardings", "sum"),
                                         stop_alightings=("alightings", "sum")).reset_index()

    for name, df in {"_j": j, "_bike": b[["segment_id", "facility_type", "status"]],
                     "_lane": bl[["segment_id", "bus_lane_side"]], "_act": act}.items():
        con.register(name, df)

    return f"""
    WITH latest AS (SELECT max(month) AS m FROM transit.mta_ridership_route_month),
    route_riders AS (   -- average weekday riders per GTFS route over the last N months
        SELECT r.route_id_gtfs AS route_id, avg(rm.average_weekday_riders) AS avg_weekday_riders
        FROM transit.mta_ridership_route_month rm JOIN transit.mta_route r USING (route_id), latest
        WHERE rm.month > latest.m - INTERVAL {months} MONTH AND r.route_id_gtfs IS NOT NULL
        GROUP BY 1),
    seg_routes AS (
        SELECT DISTINCT s.segment_id, gr.route_id
        FROM transit.bus_segment_service s, unnest(s.routes) AS u(route_short_name)
        JOIN transit.gtfs_route gr ON gr.route_short_name = u.route_short_name
        WHERE s.day_type = 'weekday'),
    exposure AS (
        SELECT segment_id, sum(rr.avg_weekday_riders) AS route_weekday_riders_exposure
        FROM seg_routes JOIN route_riders rr USING (route_id) GROUP BY 1),
    wk AS (
        SELECT segment_id,
               sum(n_bus_passes)                                            AS weekday_bus_passes,
               max(buses_per_hour_max_direction) FILTER (WHERE time_band = 'am_peak') AS am_peak_buses_per_hour,
               max(buses_per_hour_max_direction) FILTER (WHERE time_band = 'pm_peak') AS pm_peak_buses_per_hour,
               max(buses_per_hour_max_direction) FILTER (WHERE time_band = 'midday')  AS midday_buses_per_hour,
               list_sort(list_distinct(flatten(list(routes))))              AS weekday_routes
        FROM transit.bus_segment_service WHERE day_type = 'weekday' GROUP BY 1)
    SELECT st.segment_id, st.street_name, st.sha_functional_class,
           st.sha_route_id, st.length_m,
           CASE WHEN j.maintainer_group IS NULL OR j.maintainer_group = 'City/municipal' THEN 'Baltimore City'
                ELSE j.maintainer_group END                                  AS controller,
           j.maintainer_group IS NOT NULL                                   AS on_sha_inventory,
           coalesce(wk.weekday_bus_passes, 0)                               AS weekday_bus_passes,
           coalesce(wk.am_peak_buses_per_hour, 0)                           AS am_peak_buses_per_hour,
           coalesce(wk.pm_peak_buses_per_hour, 0)                           AS pm_peak_buses_per_hour,
           coalesce(wk.midday_buses_per_hour, 0)                            AS midday_buses_per_hour,
           len(wk.weekday_routes)                                           AS n_weekday_routes,
           array_to_string(wk.weekday_routes, ', ')                         AS weekday_routes,
           coalesce(a.n_stops, 0)                                           AS n_stops,
           coalesce(a.stop_boardings, 0)                                    AS stop_boardings,
           coalesce(a.stop_alightings, 0)                                   AS stop_alightings,
           e.route_weekday_riders_exposure,
           (lane.bus_lane_side IS NOT NULL OR bike.facility_type = 'Shared Bus-Bike Lane') AS has_bus_lane,
           CASE WHEN lane.bus_lane_side IS NOT NULL AND bike.facility_type = 'Shared Bus-Bike Lane' THEN 'BCDOT+OSM'
                WHEN bike.facility_type = 'Shared Bus-Bike Lane' THEN 'BCDOT'
                WHEN lane.bus_lane_side IS NOT NULL THEN 'OSM' END          AS bus_lane_source,
           lane.bus_lane_side IS NOT NULL                                   AS has_bus_lane_osm,
           lane.bus_lane_side                                               AS bus_lane_side_osm,
           bike.facility_type                                               AS bike_facility_type,
           bike.status                                                      AS bike_facility_status,
           st.geometry
    FROM traffic.street_segment st
    JOIN wk USING (segment_id)
    LEFT JOIN _j j USING (segment_id)
    LEFT JOIN _act a USING (segment_id)
    LEFT JOIN exposure e USING (segment_id)
    LEFT JOIN _lane lane USING (segment_id)
    LEFT JOIN _bike bike USING (segment_id)
    """

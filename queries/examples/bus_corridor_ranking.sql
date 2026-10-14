-- Question: Which Baltimore City streets carry the most buses in the AM peak, and which of them
--           already have a bus lane?
-- Method: length-weighted average of busier-direction AM peak buses/hour along each street; streets
--         with at least 0.5 km of bus-served length; segments under 40 m (hub driveways) excluded.
-- Datasets: transit.bus_segment_summary (weekday, GTFS feed in transit.gtfs_feed)
SELECT
    street_name,
    any_value(controller)                                                   AS controller,
    round(sum(length_m) / 1000, 2)                                          AS served_km,
    round(sum(am_peak_buses_per_hour * length_m) / sum(length_m), 1)        AS am_peak_buses_per_hour_lw,
    round(max(am_peak_buses_per_hour), 1)                                   AS am_peak_buses_per_hour_max,
    max(n_weekday_routes)                                                   AS max_routes_on_a_segment,
    round(sum(stop_boardings))                                              AS stop_boardings,
    round(100.0 * coalesce(sum(length_m) FILTER (WHERE has_bus_lane), 0) / sum(length_m)) AS pct_length_with_bus_lane
FROM transit.bus_segment_summary
WHERE length_m >= 40
GROUP BY street_name
HAVING sum(length_m) >= 500
ORDER BY am_peak_buses_per_hour_lw DESC
LIMIT 25;

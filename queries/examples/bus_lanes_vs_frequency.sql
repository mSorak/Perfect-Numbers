-- Question: how much high-frequency bus street has a bus lane, and does adding the Circulator change the picture?
-- Window: scheduled service, Wednesday 2026-10-14 (MTA local-bus + Charm City Circulator GTFS);
--         lanes = BCDOT 2021 inventory ∪ BCDOT bike layer ∪ OSM (2026-10-17). Segments under 50 m excluded (hub stubs).
SELECT CASE WHEN peak_hour_buses_per_hour_all >= 20 THEN '20+'
            WHEN peak_hour_buses_per_hour_all >= 12 THEN '12–19'
            WHEN peak_hour_buses_per_hour_all >= 8  THEN '8–11'
            ELSE 'under 8' END                                              AS peak_hour_buses_all_operators,
       round(sum(length_m) / 1000, 1)                                       AS street_km,
       round(sum(length_m) FILTER (WHERE has_bus_lane) / 1000, 1)           AS km_with_bus_lane,
       round(100 * sum(length_m) FILTER (WHERE has_bus_lane) / sum(length_m)) AS pct_with_lane,
       round(sum(length_m) FILTER (WHERE circulator_weekday_passes > 0) / 1000, 1) AS km_with_circulator
FROM transit.bus_segment_summary
WHERE length_m >= 50
GROUP BY 1
ORDER BY min(peak_hour_buses_per_hour_all) DESC;

-- Question: Which city-controlled street segments have 20+ buses per hour (busier direction) in either
--           weekday peak but no bus lane?
-- Datasets: transit.bus_segment_summary
SELECT segment_id, street_name, round(length_m) AS length_m,
       round(greatest(am_peak_buses_per_hour, pm_peak_buses_per_hour), 1) AS peak_buses_per_hour,
       n_weekday_routes, weekday_routes, bike_facility_type
FROM transit.bus_segment_summary
WHERE controller = 'Baltimore City'
  AND NOT has_bus_lane
  AND greatest(am_peak_buses_per_hour, pm_peak_buses_per_hour) >= 20
  AND length_m >= 40
ORDER BY peak_buses_per_hour DESC;

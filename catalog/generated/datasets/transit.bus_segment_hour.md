# `transit.bus_segment_hour` — Scheduled bus passes on Baltimore City street segments, by operator and clock hour

Hourly version of transit.bus_segment_service: scheduled bus passes per street segment, operator (MTA local bus, Charm City Circulator), representative day type and clock hour, by direction. Same matching and pass-time method. Use it for the busiest single hour (the "peak hour"); combine operators by summing directions before taking the max.

- **Grain:** one row per segment × operator × day type × hour with at least one pass
- **Primary key:** segment_id, operator, day_type, hour
- **Layer / access mode:** mart / derived
- **Source:** derived
- **Depends on:** traffic.street_segment, transit.gtfs_shape, transit.gtfs_trip, transit.gtfs_stop_time, transit.gtfs_route, transit.gtfs_service_date, transit.ccc_gtfs_shape, transit.ccc_gtfs_trip, transit.ccc_gtfs_stop_time, transit.ccc_gtfs_route, transit.ccc_gtfs_service_date
- **Card:** `catalog/datasets/transit/bus_segment_hour.yml`
- **Current build:** 20261017T193048Z · 515,327 rows · git f6eab64
- **Inputs:** {'datasets': {'traffic.street_segment': '20261014T020027Z', 'transit.gtfs_shape': '20261014T020040Z', 'transit.gtfs_trip': '20261014T020040Z', 'transit.gtfs_stop_time': '20261014T020040Z', 'transit.gtfs_route': '20261014T020040Z', 'transit.gtfs_service_date': '20261014T020041Z', 'transit.ccc_gtfs_shape': '20261017T192526Z', 'transit.ccc_gtfs_trip': '20261017T192526Z', 'transit.ccc_gtfs_stop_time': '20261017T192526Z', 'transit.ccc_gtfs_route': '20261017T192525Z', 'transit.ccc_gtfs_service_date': '20261017T192527Z', 'transit.bus_segment_service': '20261017T192952Z'}, 'raw': {}}

## Columns

| Column | Type | Description |
|---|---|---|
| `segment_id` | bigint | traffic.street_segment.segment_id. |
| `operator` | varchar | MTA (local bus feed) or Circulator (Charm City Circulator feed). |
| `day_type` | varchar | weekday, saturday or sunday (representative dates in parameters). |
| `hour` | integer | Clock hour after service-day midnight (0–27; 24–27 = after midnight). 7 = 7:00–7:59 am. |
| `n_bus_passes` | bigint | Scheduled bus passes in the band, both directions. |
| `n_passes_with` | bigint | Passes travelling in the segment's digitized direction. |
| `n_passes_against` | bigint | Passes travelling against the segment's digitized direction. |
| `routes` | varchar[] | Route short names passing in the band. |

## Parameters

```yaml
service_dates:
  weekday: '2026-10-14'
  saturday: '2026-10-17'
  sunday: '2026-10-18'
buffer_m: 10
min_share: 0.6
max_angle: 30
```

## Caveats

- Pass times are interpolated linearly along each trip; on long routes the band assignment for a segment can be off by up to a band boundary.
- 2026-10-14: Matcher QA (360 weekday shapes with >500 m in the city): matched segment length ÷ in-city shape length has median 1.04 and 5th–95th percentile 0.96–1.25 at a 10 m buffer. The excess is mostly divided roads, where both carriageways are credited with buses from both directions; per-segment intensity is unaffected but corridor kilometres are slightly overstated. 14 shapes match under 90% of their in-city length (off-street terminals and loops).
- MTA local bus and the Charm City Circulator only: MTA commuter bus, Light Rail, Metro, the Harbor Connector and university shuttles are not included.
- 2026-10-17: Saturday 2026-10-17 was the Baltimore Running Festival; the Circulator suspended Orange, Purple and Banner 9 am–4 pm and MTA detoured routes. Neither GTFS shows it, so Saturday rows describe the regular schedule, not that day.
- 2026-10-17: The Circulator feed schedules 16 extra Orange Route trips 8–11 pm every day (no direction_id), although BCDOT publishes Mon–Thu service ending at 8 pm. They affect only the evening band.

# `transit.stop_ridership` — MTA bus stop boardings and alightings (seasonal average)

Average weekday boardings and alightings per MTA bus stop, as published on Maryland iMAP. A seasonal snapshot (Summer 2024 at the 2026-10 pull), summed across all routes serving the stop.

- **Grain:** one row per bus stop
- **Primary key:** stop_id
- **Layer / access mode:** staging / mirror
- **Source:** md_imap_transit
- **Depends on:** raw:md_imap_transit/mta_bus_stops
- **Card:** `catalog/datasets/transit/stop_ridership.yml`
- **Current build:** 20261014T020043Z · 4,449 rows · git d8c1e6e
- **Inputs:** {'datasets': {}, 'raw': {'md_imap_transit/mta_bus_stops': '20261014T0139Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `stop_id` | varchar | MTA stop ID (matches transit.gtfs_stop.stop_id). |
| `stop_name` | varchar | Stop name. |
| `routes_served` | varchar | Routes serving the stop, as published. |
| `boardings` | double | Average weekday boardings (season per caveats). |
| `alightings` | double | Average weekday alightings. |
| `boardings_alightings` | double | Boardings + alightings. |
| `ridership_rank` | integer | Rank by total activity. |
| `shelter` | varchar | Shelter present (as published). |
| `county` | varchar | County name as published. |
| `mode` | varchar | Mode. |
| `source_snapshot_id` | varchar | Raw snapshot id. |
| `geometry` | geometry | Point, OGC:CRS84. |

## Caveats

- Seasonal average, not route-specific; the layer described Summer 2024 weekday ridership at the 2026-10 pull.

## License and citation

```yaml
terms: public
redistribution: attribution
citation: MDOT MTA via Maryland iMAP, MTA Bus Stops, retrieved {retrieved_at}
```

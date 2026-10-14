# `traffic.aadt_segment` — MDOT SHA traffic-count segments (AADT network), statewide

Road segments on MDOT SHA's AADT network with route, functional class, lanes and geometry. Volumes by year are in `traffic.aadt_segment_year` (join on segment_id). Covers state, interstate and many county roads statewide; local streets are mostly absent.

- **Grain:** one row per AADT segment (in the source snapshot)
- **Primary key:** segment_id
- **Layer / access mode:** staging / mirror
- **Source:** mdot_sha_aadt
- **Depends on:** raw:mdot_sha_aadt/aadt_segment, ref.county_codes
- **Card:** `catalog/datasets/traffic/aadt_segment.yml`
- **Current build:** 20261014T210804Z · 10,013 rows · git c2a0ea2
- **Inputs:** {'datasets': {'ref.county_codes': '20261014T210156Z'}, 'raw': {'mdot_sha_aadt/aadt_segment': '20261014T1932Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `segment_id` | varchar | Source GlobalID. |
| `location_id` | varchar | Count station ID (shared by several segments). |
| `county_geoid` | varchar | County FIPS via ref.county_codes. |
| `mdot_county_code` | integer | MDOT alphabetical county code (not FIPS). |
| `municipality` | varchar | Municipality, if any. |
| `road_name` | varchar | Road name (e.g. JONES FALLS EXPWY). |
| `id_prefix` | varchar | Route prefix: IS interstate, US, MD, CO county, MU municipal, … |
| `route_number` | varchar | Route number (I-83 = IS 83). |
| `route_id_rh` | varchar | SHA route ID. |
| `road_section` | varchar | Section description as published. |
| `begin_mp` | double | Begin milepoint. |
| `end_mp` | double | End milepoint. |
| `station_desc` | varchar | Count station description. |
| `rural_urban` | varchar | Rural/urban code. |
| `f_system` | integer | HPMS functional system code (1 interstate … 7 local). |
| `f_system_desc` | varchar | Functional system label. |
| `main_line` | varchar | Main line flag. |
| `num_lanes` | integer | Through lanes (latest release). |
| `counted_factored_latest` | varchar | C counted / F factored, for the latest year only. |
| `latest_year` | integer | Year the release's unsuffixed AADT column represents (inferred, see traffic.aadt_segment_year.year_method). |
| `length_m` | double | Segment length in metres (EPSG:26985). |
| `source_snapshot_id` | varchar | Raw snapshot this row came from. |
| `geometry` | geometry | LineString, OGC:CRS84. |

## Caveats

- 2026-10-14: segment_id is the source GlobalID, which is stable only within a snapshot; LOCATION_ID (the count station) is shared by several segments. Compare releases by route + milepoints, not by segment_id.
- 2026-10-14: num_lanes and counted_factored_latest describe the latest release year only.

## License and citation

```yaml
terms: public
redistribution: attribution
citation: MDOT SHA, Annual Average Daily Traffic (FeatureServer), retrieved {retrieved_at}
```

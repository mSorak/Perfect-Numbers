# `traffic.aadt_segment_year` — MDOT SHA AADT by segment and year, with VMT

Annual average daily traffic (AADT) and weekday traffic (AAWDT) per AADT segment and year, long format with an explicit year, plus vehicle-miles travelled. VMT = AADT × segment length; annual VMT uses the calendar year's days. Segment attributes and geometry: `traffic.aadt_segment`.

- **Grain:** one row per segment × year with a published, non-zero AADT
- **Primary key:** segment_id, year
- **Layer / access mode:** staging / mirror
- **Source:** mdot_sha_aadt
- **Depends on:** raw:mdot_sha_aadt/aadt_segment
- **Card:** `catalog/datasets/traffic/aadt_segment_year.yml`
- **Current build:** 20261014T193425Z · 97,538 rows · git 839fb53
- **Inputs:** {'datasets': {}, 'raw': {'mdot_sha_aadt/aadt_segment': '20261014T1932Z'}}
- **Coverage:** 2016 → 2025

## Columns

| Column | Type | Description |
|---|---|---|
| `segment_id` | varchar | Joins traffic.aadt_segment.segment_id (same snapshot). |
| `year` | integer | Calendar year the volume describes. |
| `aadt` | bigint | Annual average daily traffic, vehicles/day (both directions). |
| `aawdt` | bigint | Annual average weekday traffic, vehicles/day. |
| `is_latest_column` | boolean | True if from the release's unsuffixed (newest) column. |
| `year_method` | varchar | How the year was assigned. |
| `length_m` | double | Segment length in metres (EPSG:26985). |
| `daily_vmt` | double | AADT × length in miles: vehicle-miles per average day. |
| `annual_vmt` | double | daily_vmt × days in the year. |
| `source_snapshot_id` | varchar | Raw snapshot this row came from. |

## Caveats

- 2026-10-14: History years use today's segment geometry and lengths. Where a road was re-segmented, older years are as MDOT re-published them, not as originally counted.
- 2026-10-14: In the 2026-10 snapshot the unsuffixed AADT column is 2025 (newest suffixed column is AADT_2024). Confirmed by Matt per HANDOFF; re-check the rule on every new release.
- 2026-10-14: Most years are factored estimates, not counts; only the latest year's counted/factored flag is published (traffic.aadt_segment.counted_factored_latest).

## License and citation

```yaml
terms: public
redistribution: attribution
citation: MDOT SHA, Annual Average Daily Traffic (FeatureServer), retrieved {retrieved_at}
```

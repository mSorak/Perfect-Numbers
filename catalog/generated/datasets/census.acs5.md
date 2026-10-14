# `census.acs5` — American Community Survey 5-year estimates (Census API), long format

ACS 5-year estimates with margins of error for Maryland geographies (state, county, place, tract), one row per geography × variable. Add tables by listing them in the census_api source card (groups) and running `pn fetch census_api`. Currently: B01003 total population, ACS 2020–2024.

- **Grain:** one row per geography × vintage × variable
- **Primary key:** geoid, geo_level, vintage, variable
- **Layer / access mode:** staging / mirror
- **Source:** census_api
- **Depends on:** raw:census_api/acs5_2024
- **Card:** `catalog/datasets/census/acs5.yml`
- **Current build:** 20261014T210727Z · 2,036 rows · git c2a0ea2
- **Inputs:** {'datasets': {}, 'raw': {'census_api/acs5_2024': '20261014T2106Z'}}

## Columns

| Column | Type | Description |
|---|---|---|
| `geoid` | varchar | Census GEOID (state 24, county 24027, place 2404000, tract 24027601100). |
| `geo_level` | varchar | state, county, place or tract. |
| `name` | varchar | Census geography name. |
| `vintage` | bigint | End year of the 5-year period (2024 = 2020–2024). |
| `survey` | varchar | acs5. |
| `vintage_label` | varchar | e.g. ACS 2020–2024 5-year. |
| `table_id` | varchar | Table (group) ID, e.g. B01003. |
| `variable` | varchar | Variable ID without suffix, e.g. B01003_001. |
| `label` | varchar | Census variable label. |
| `estimate` | double | Estimate; null where Census publishes a jam value. |
| `moe` | double | 90% margin of error; null where not applicable. |
| `annotation` | varchar | Census annotation for the estimate, if any. |
| `source_snapshot_id` | varchar | Raw snapshot. |
| `geoid_vintage` | integer | Geography vintage (2020 census geographies). |

## Caveats

- 2026-10-14: Estimates are 5-year period estimates (e.g. 2020–2024), not single-year values; state the vintage label with every number. Sum MOEs with the acs_sum_moe metric, never by adding.

## License and citation

```yaml
terms: public domain
redistribution: allowed
citation: U.S. Census Bureau, American Community Survey {vintage_label}, table {table_id},
  via the Census Data API, retrieved {retrieved_at}
```

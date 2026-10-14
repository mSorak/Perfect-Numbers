# `ref.acrs_injury_to_mais` — ACRS injury status → NHTSA unit-cost injury level (map v1)

Maps the ACRS person injury status (KABCO scale) to the injury level used by NHTSA's 2019 unit costs (ref.nhtsa_unit_cost_2019). Map v1 is the one used by the published crash-cost model (method 2026.1).

- **Grain:** one row per map version × ACRS injury code
- **Primary key:** map_version, acrs_injury_code
- **Layer / access mode:** seed / derived
- **Source:** derived
- **Depends on:** seed:ref_acrs_injury_to_mais.csv
- **Card:** `catalog/datasets/ref/acrs_injury_to_mais.yml`
- **Current build:** 20261014T210200Z · 5 rows · git c2a0ea2
- **Inputs:** {'datasets': {}, 'raw': {}}

## Columns

| Column | Type | Description |
|---|---|---|
| `map_version` | varchar | Mapping version (v1 = method 2026.1). |
| `acrs_injury_code` | varchar | ACRS InjuryStatus code, zero-padded text ('01'–'05'). |
| `acrs_injury_desc` | varchar | ACRS label. |
| `kabco` | varchar | KABCO letter. |
| `injury_level` | varchar | NHTSA unit-cost level (Fatal, MAIS0–MAIS5). |

## Caveats

- 2026-10-14: A KABCO → MAIS map is an approximation; v1 maps A (suspected serious) to MAIS4, which is on the high side of published translators. Changing it is a new map_version and a new cost method_version.
- 2026-10-14: ACRS persons with no injury status (e.g. 8,089 occupants in 2025H1) are not mapped here; crash.report_cost documents how they are treated.

## License and citation

```yaml
terms: modelling choice (Matt, crash-cost model 2026)
redistribution: allowed
```

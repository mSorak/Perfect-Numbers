# `ref.nhtsa_unit_cost_2019` — NHTSA comprehensive unit costs of police-reported crashes, 2019 dollars (Table 1-10)

Per-person unit costs by injury level (MAIS0–MAIS5, Fatal) and per-damaged-vehicle costs for property-damage-only crashes (PDOVehicle), split into cost components, in 2019 dollars. From Blincoe et al., "The Economic and Societal Impact of Motor Vehicle Crashes, 2019 (Revised)", NHTSA DOT HS 813 403 (2023), Table 1-10. Long format; filter cost_component = 'total_comprehensive' for the headline unit cost.

- **Grain:** one row per injury level × cost component (including subtotal and total rows)
- **Primary key:** injury_level, cost_component
- **Layer / access mode:** seed / derived
- **Source:** derived
- **Depends on:** seed:ref_nhtsa_unit_cost_2019.csv
- **Card:** `catalog/datasets/ref/nhtsa_unit_cost_2019.yml`
- **Current build:** 20261014T193754Z · 112 rows · git 839fb53
- **Inputs:** {'datasets': {}, 'raw': {}}

## Columns

| Column | Type | Description |
|---|---|---|
| `injury_level` | varchar | PDOVehicle (per damaged vehicle), MAIS0–MAIS5 or Fatal (per person). |
| `cost_component` | varchar | medical, ems, market_productivity, household_productivity, insurance_admin, workplace, legal, congestion, property_damage, quality_of_life, subtotals, total_economic, total_comprehensive. |
| `component_group` | varchar | economic_person, economic_other, quality_of_life, subtotal or total. |
| `unit_cost_usd2019` | bigint | Unit cost in 2019 dollars. |

## Caveats

- 2026-10-14: Transcribed from 2026\crash_costs\tables_from_report.xlsx, sheet police_unit_costs_comp (sha256 40b476a2…2d22), as used by the published crash-cost model. Not re-checked against the PDF.
- 2026-10-14: Subtotal and total rows are included (component_group 'subtotal' / 'total'); never sum across all rows of an injury level.

## License and citation

```yaml
terms: public domain (US government report)
redistribution: allowed
citation: Blincoe et al. (2023), NHTSA DOT HS 813 403, Table 1-10
```

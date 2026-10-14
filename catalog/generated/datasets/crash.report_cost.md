# `crash.report_cost` — Estimated societal cost of each Maryland crash report (method 2026.1)

Comprehensive societal cost per ACRS crash report using NHTSA's 2019 unit costs (Blincoe et al. 2023, Table 1-10), by component, in 2025 dollars. Method 2026.1 reproduces the published Perfect Numbers crash-cost model: property-damage-only crashes cost (vehicles × PDOVehicle); injury and fatal crashes cost Σ persons × the unit cost of their injury level (ACRS → MAIS map v1). Headline column: total_comprehensive_usd2025.

- **Grain:** one row per crash report
- **Primary key:** report_number
- **Layer / access mode:** mart / derived
- **Source:** derived
- **Depends on:** crash.acrs_report, crash.acrs_vehicle, crash.acrs_person, ref.nhtsa_unit_cost_2019, ref.acrs_injury_to_mais, econ.cpi_u
- **Card:** `catalog/datasets/crash/report_cost.yml`
- **Current build:** 20261014T210200Z · 287,019 rows · git c2a0ea2
- **Inputs:** {'datasets': {'crash.acrs_report': '20261014T210156Z', 'crash.acrs_vehicle': '20261014T210159Z', 'crash.acrs_person': '20261014T210157Z', 'ref.nhtsa_unit_cost_2019': '20261014T210200Z', 'ref.acrs_injury_to_mais': '20261014T210200Z', 'econ.cpi_u': '20261014T210200Z'}, 'raw': {}}
- **Coverage:** 2024-01-01 → 2026-09-30

## Columns

| Column | Type | Description |
|---|---|---|
| `report_number` | varchar | ACRS report number (crash.acrs_report). |
| `crash_date` | date | Crash date. |
| `crash_year` | bigint | Crash year. |
| `county_geoid` | varchar | County FIPS (ACRS Crash County). |
| `severity_code` | integer | 1 fatal, 2 injury, 3 property damage only. |
| `severity` | varchar | Severity label. |
| `n_vehicles` | bigint | Vehicles on the report. |
| `n_persons` | bigint | Persons on the report (occupants + non-motorists). |
| `n_persons_no_injury_status` | bigint | Persons with no injury status (costed at zero). |
| `n_fatal` | bigint | Persons killed. |
| `n_serious_injury` | bigint | Persons with suspected serious injury (code 02). |
| `medical_usd2025` | double | Medical cost component, 2025 dollars. |
| `ems_usd2025` | double | Emergency medical services. |
| `market_productivity_usd2025` | double | Lost market productivity. |
| `household_productivity_usd2025` | double | Lost household productivity. |
| `insurance_admin_usd2025` | double | Insurance administration. |
| `workplace_usd2025` | double | Workplace costs. |
| `legal_usd2025` | double | Legal costs. |
| `congestion_usd2025` | double | Congestion costs. |
| `property_damage_usd2025` | double | Property damage. |
| `total_economic_usd2025` | double | Total economic cost. |
| `quality_of_life_usd2025` | double | Quality-of-life (QALY) cost. |
| `total_comprehensive_usd2025` | double | Comprehensive cost = economic + quality of life. Headline figure. |
| `method_version` | varchar | Cost method version (2026.1). |
| `injury_map_version` | varchar | ACRS → MAIS map version. |
| `deflator` | double | Multiplier applied to 2019 unit costs. |
| `deflator_method` | varchar | How the multiplier was set. |
| `source_period` | varchar | Snapshot period of the report. |

## Parameters

```yaml
usd_year: 2025
deflator:
  use_legacy_factor: true
  legacy_factor: 1.26
  from: '2019-06-01'
  to: '2025-06-01'
```

## Caveats

- 2026-10-14: Costs are 2019 unit costs × 1.26 (June 2019 → June 2025, as published). CPI-U NSA gives 1.2593, about 0.06% lower; a CPI-based variant would be a new method version.
- 2026-10-14: Persons with no injury status are costed at zero, and injury crashes are costed only through their persons (no PDOVehicle cost for their vehicles), exactly as in the published model.
- 2026-10-14: Parity: built from the legacy half-year exports, this method matches crash_cost_eval.csv row for row (tests/test_crash_parity.py). This dataset reads the current monthly pulls, so its 2024–2025 totals differ slightly from the published ones.

## License and citation

```yaml
terms: derived from MDSP ACRS and NHTSA
redistribution: attribution
citation: Perfect Numbers crash-cost model 2026.1 (MDSP ACRS; NHTSA DOT HS 813 403)
```

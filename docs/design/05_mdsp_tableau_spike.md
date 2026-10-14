# Spike: MDSP Tableau row-level export without a browser

Date: 2026-10-14 · Time spent: about 1.5 h of the 4 h box · Plan item: `03_proposal.md` §10 Phase 2 item 3; `HANDOFF.md` Phase 2 item 2.

**Verdict: use the API route. Playwright is not needed.** A guest session on `analytics.mdsp.org` (view `PublicCrash2/PublicCrash`) can download every tab's row-level data over plain HTTP:
- all 8 logical tables;
- all fields;
- no row cap observed;
- from one session, in the same CSV format the Download button produces.

A full month of all 8 tables takes about 33 s. A sketch connector that does this is in [`examples/tableau_public_connector_sketch.py`](examples/tableau_public_connector_sketch.py). It was run for 2025-09; its output was byte-identical to the hand-driven probes.

All probe responses are in the session scratchpad, not in `raw/`. Nothing was written to the data root.

## How a guest session starts (all routes need this)

1. `GET /t/Public/views/PublicCrash2/PublicCrash?:embed=y&Crash Date Begin=…&Crash Date End=…` sets cookies.
   - Server 2026.2 no longer puts `tsConfig` in this HTML.
2. `POST /vizql/t/Public/w/PublicCrash2/v/PublicCrash/startSession/viewing?<same params>` returns `tsConfig` as JSON.
   - It includes `sessionid`, `allow_export_data: true`, `allow_view_underlying: true` and `is_guest: true`.
   - Required headers: `Tableau-Viz-Location`, `Tableau-Viz-Path`.
3. `POST …/bootstrapSession/sessions/{sid}` builds the dashboard.
   - You must pass `tsConfig.showParams` back. Otherwise the URL date parameters are ignored, and you silently get the default window (2026 YTD).
4. Commands are `POST …/sessions/{sid}/commands/{tabdoc|tabsrv}/{name}`. Exported files are `GET …/tempfile/sessions/{sid}?key=…`.

The dashboard's "hidden tabs" are not worksheets. They are the 8 **logical tables** of the workbook's relationship data model. `tabdoc/api-get-worksheet-logical-table-ids` lists them from the `Crash Map` worksheet:

| Caption | Logical table ID prefix | Card entity |
|---|---|---|
| Reports | `Reports_Restricted_…` | reports |
| Vehicles | `Vehicles_Restricted_…` | vehicles |
| Occupants | `Occupants_…` | occupants |
| NonMotorists | `NonMotorists_…` | nonmotorists |
| Contributing Circumstances | `Public_AllContribs_…` | contribs |
| Vehicle Areas Damaged | `Vehicles_Damage_…` | damage |
| Vehicle Sequence Of Events | `Vehicles_SequenceOfEvents_…` | sequence |
| NonMotorist SafetyEquipment | `NonMotorists_SafetyEquipment_…` | nmsafetyequip |

The IDs end in GUIDs, so look them up by caption on every run.

## Routes tried

| # | Route | Works? | Returns | Cap |
|---|---|---|---|---|
| 1 | **`tabsrv/export-view-data-underlying-to-csv-server`** with `viewDataTableId=<logical table>`, `columns=<all column uniqueNames>`, `showAliases=true` | **Yes. Recommended.** | The exact file the UI's "Download > Data > tab > Show all fields" produces: UTF-8 with BOM, M/D/YYYY dates, aliased values (Yes/No, "Property Damage Crashes"), 9-decimal lat/long, blank nulls. The result key arrives in a `doc:export-file-notification-event`, not in the command return. | **None seen.** 2025H2 in one call: 53,568 reports, 222,448 damage rows (15 s). |
| 2 | `tabdoc/api-get-worksheet-underlying-logical-table-data` (the Embedding/Extensions API call), `includeAllColumns=true` | Yes, but capped | JSON with two copies of the table. `showDataTable` holds raw values (ISO dates, `true/false`, `%null%`, full-precision lat/long, CrashPoint as WKT). `showDataFormattedTable` holds display values (lat/long rounded to 5 places). | **Hard 10,000 rows** (`topN: 10000`). `maxRows` is ignored. A month exceeds it for 5 of 8 tables. Daily windows stay under it (largest table, Damage, peaks at about 1,650/day) but take about 11 min per month. |
| 3 | Route 1 with `showDataTableId` or `logicalTableId` instead of `viewDataTableId` | Wrong output | The joined relationship result projected onto the table's columns. Every table gets the same row count (113,289 for 2025-09), with duplicates and nulls. | — |
| 4 | Route 1 with `columns=[]` | Partial | Only the default visible fields (22 of 72 for Reports, 3 of 6 for Sequence). | — |
| 5 | `tabsrv/export-crosstab-to-csvserver` (Download > Crosstab) per worksheet | Not useful | UTF-16 TSV of the worksheet's layout. The Crash Map has about 2 lines per report and only the map's fields; the other sheets are aggregates. | — |
| 6 | Per-sheet `.csv` (`/views/PublicCrash2/CrashMap.csv`, `County.csv`, `Reports.csv`, …) | No | 404. Only `PublicCrash` is a published view (`tabs_allowed: false`). | — |
| 7 | `PublicCrash.csv`, `PublicCrash?:format=csv`, plus `:underlying`, `:summary=false`, `:showAll`, `:refresh` | Summary only | The county × severity reconciliation table the card already uses (66 rows for 2025-09). The extra flags are ignored. `.xlsx` redirects. | — |

## Validation (2025-09 and 2025H2)

- **Routes 1 and 2 agree exactly.** For 2025-09, route 1 (one monthly call per table) matched route 2 (30 daily windows) on row counts and keys for every table:
  - Reports 8,610
  - Vehicles 15,945
  - Occupants 19,229
  - NonMotorists 426
  - Contribs 14,621
  - Damage 35,827
  - Sequence 18,192
  - NMSafetyEquip 439
- **Reconciliation endpoint:** the sum of distinct reports for 2025-09 is 8,610, an exact match.
- **Against the legacy 2025H2 UI files in `raw/`:**
  - The column sets are identical. Column order differs, which is fine: `pn intake` detects entities by header subset and staging selects by name.
  - Occupants and NonMotorists gain `Reportnumber` and `Crash Severity Description`, which come from the Reports side of the relationship.
  - Counts differ slightly, consistent with revisions since the 2026-03-28 export: Reports 53,416 then, 53,568 now.
  - For Sept 2025: 32 reports were added and 14 withdrawn.
- **Orphans:** zero in all 7 child tables for 2025H2 when exported in one session. The legacy 2025H2 batch needed the `legacy_mixed_session` waiver for exactly this problem.
- **Data window:** the workbook only serves crashes from **2024-01-01**. The parameter minimum is 45292 (an Excel-style date serial for that day); a window starting 2023-12-25 returns 2024-01-01 onward. 2019–2023 remain in the separate `PublicCrashData` workbook, as the card says.
- **Sequence has exact duplicate rows:** 143 in 2025-09, the same in both routes. They are upstream, not a route artefact. Staging should decide how to key that table.

## Recommendation and next steps

1. **Adopt route 1 as the `tableau_public` connector for `mdsp_acrs`.**
   - Use monthly windows, all 8 tables, one session per window.
   - Keep each file verbatim in `raw/` and hand it to the existing `pn intake` checks: header signature, keys, orphans, same session, reconciliation.
   - The card's "greyed-out Data" worry does not apply here. That was a UI limit, not a server one.
2. Wire it as `pn fetch mdsp_acrs --period 2026-09`. The connector writes into `inbox/mdsp_acrs/` (or a workdir), then the intake path runs.
   - Record the per-window metadata in the manifest: logical table IDs, server version, `workbookLastPublishedAt`, session id hash.
3. **Card updates once the first all-tabs batch is taken in.** Add `header_signature` and `key` for the four new tabs, and drop `required: false`. Suggested signatures:
   - contribs `[ReportNumber Contribs, Contribs Code]`
   - damage `[VehicleID Damage, DamageLocation Veh]`
   - sequence `[VehicleID Sequence, SequenceOrder Veh]`
   - nmsafetyequip `[PersonID NMSafetyEquip, SafetyEquipmentCode NM]`
4. Re-pull 2025H2 in one session to retire the `legacy_mixed_session` waiver, then pull 2026-01 onward.
   - Proposal §10 asks for exactly this. It takes about 2.5 min per half-year.
5. **Keep Playwright as the documented fallback only.**

## Risks

- **Undocumented internal endpoints.** Command and parameter names (`viewDataTableId`, `showAliases`, `columns`, the notification shape) can change when MDSP upgrades Tableau Server (now 2026.2.0). The connector should fail loudly; the sketch checks permissions, missing tables, a missing result key and the BOM. `pn intake` then catches schema drift.
  - If a parameter is renamed, the server's validation errors name what is missing (`missing: show-aliases`). That is how these were found, so a fix should take minutes.
- **Workbook or parameter renames.** For example `PublicCrash` → `PublicCrash2`, or `[Parameters].[Parameter 1]`/`[Parameter 2]` = Begin/End. These live in the card config, not in code.
- **Politeness.** One session per month, about 33 s, with sequential calls; the guest idle timeout is 60 min. Don't parallelise.
- **The parameter calls are slow.** Each `set-parameter-value` takes about 9 s because the dashboard re-renders. Booting a fresh session per window with the dates in the URL costs about the same.
- **Terms.** These are the same data and the same export the public UI offers to guests; no authentication is bypassed. Cite MDSP and the retrieval date, as the card already says.

## Reproduce

The probe scripts are in the session scratchpad and are not committed. The sketch connector contains the full call sequence. To run it for one month into a scratch folder, see its `fetch(cfg, workdir)` docstring and the card config block at the top of the file.

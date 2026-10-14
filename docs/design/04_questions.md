# Questions for Matt

Status: **answered 2026-10-13**. Matt's answers are in `answers.md` and summarized in `03_proposal.md` §0.2. Only A5 (time budget) is still open; the default assumption stands until you say otherwise.

Each question has a **default**, and the proposal (`03_proposal.md`) is written against those defaults. Answer only where you disagree, or where a question is marked *(needs you)*. The most time-sensitive questions come first.

---

## A. Priorities, timing and budget

**A1. What are your next 3–6 months of pieces?** *(needs you)*
This sets the order of the Phase 2 backlog. Candidates I can see:
- November 3 general-election results and legislative turnover (building on `mta_overview/work`).
- The promised Eastern Silver Spring opinion piece.
- ReVision Zero #3.
- MTA follow-ups through the 2027 session.
- The Baltimore traffic-violence × crime analysis.
- Purple Line catchments.
- The rental market piece.

*Default:* Phase 1 (the crash slice) first, then the SBE/legislature work and AADT/FARS.

**A2. Election-night or near-election coverage on Nov 3?**
If yes, the SBE results and candidates loader moves into Phase 1, which means about 3 weeks. SBE's `GG26_*` CSVs update during the canvass, so they need repeated snapshots.
*Default:* no. The loader is built after certification.

**A3. Standard geographic scope.**
*Default:*
- MD sub-county geography in Phase 1. DC and VA are added when a regional piece needs them (Purple Line, DC pedestrian deaths).
- National data only as small attribute tables for rankings: state and county populations, plus tract population and land area for density percentiles. No national shapes.

**A4. Are baseball and math pieces in scope?**
*Default:* no. They stay in their project folders, under the same conventions. A `sports` domain can be added later.

**A5. Time budget.** *(needs you)*
How many hours a week can you give this during setup, and how much monthly upkeep is acceptable afterwards? This is the main input to "solo-sized".
*Default assumption:*
- About 4–6 hours a week of your time for 4–6 weeks. Agents do most of the building; you review and decide.
- Then 1–2 hours a month.

---

## B. Machine, storage and cloud

**B1. OneDrive.** *(needs you)*
Is OneDrive deliberately your backup and sync, or just where the folder happened to live? Do you use more than one computer? Can the data root live at `C:\Users\Matt\pn-data\`, outside OneDrive?
- Only the four append-only layers (raw, API cache, documents, data packs) would be backed up.
- Backup is a one-way, never-deleting copy into a OneDrive archive folder now, and R2 later.

*Default:* yes. I'd also suggest moving the git repo out of OneDrive, with GitHub as its backup. That also takes the app's `.venv` and `node_modules` out of OneDrive.

**B2. Is the laptop usually on and awake?**
This affects scheduled refreshes, which come in Phase 3 via Task Scheduler.
*Default:* refreshes are run by hand (`pn refresh --due`) until you say otherwise.

**B3. Cloud appetite.**
*Default:* no cloud until Phase 3. Then Cloudflare R2 for backup and remote reads: at ≈10–25 GB, that is **$0–0.25 a month** after the 10 GB free tier. MotherDuck only if you want hosted SQL from anywhere.

---

## C. Git, repo and what's public

**C1. What should the git setup become?** *(needs you)*
Today there are four pieces:
- the OneDrive working repo, on branch `drop-blog-posts`, with one unpushed commit (`3d29916`) adding ~8 GB of data. It can't be pushed: GitHub rejects files over 100 MB.
- the `source/Perfect-Numbers` clone, which is what pushes to GitHub.
- a separate `mSorak/md_crash_costs` repo nested in `2026/crash_costs/.git`.
- three diverged copies of the crash app.

Options:
1. **(Recommended)** One working repo that publishes to GitHub. Data stays out of git, enforced by a root `.gitignore`. The hub lives in this repo's `data/` folder. Deployable apps keep their own small repos.
2. A separate `pn-data` repo for the hub.
3. Status quo.

*Default:* option 1. The proposal outlines a non-destructive cleanup: keep every file on disk and rewrite only the unpushed local commit. Exact steps follow your choice. **I have not changed any git state.**

**C2. Retire the `source/Perfect-Numbers` clone once the working repo can push?**
It holds a 2.9 GB stale data copy: 0.8 GB of crash exports, including the bad 395 KB H2-2025 vehicle file, and 2.1 GB of national census shapes.
*Default:* yes, after you confirm.

**C3. What should the public repo promise about data?**
The README says each post's folder holds "code, data, and markdown". With raw data out of git, the proposal keeps that promise through **data packs**: licence-cleared outputs per post, committed if under ~50 MB, or attached to a GitHub release.
*Default:* yes. Exclude sources whose terms don't allow redistribution (Zillow is likely one).

---

## D. How you work with data and AI

**D1. Transformation tooling.** *(needs you; proposal §6.6)*
- **Recommended:** YAML dataset cards as the source of truth, plus a small SQL runner (`pn build`) inside the hub package.
- **Alternative:** dbt-core + dbt-duckdb from day one. More standard, more familiar to agents, more plumbing.

Cards stay dbt-compatible, so switching later is mechanical.
*Default:* cards + runner.

**D2. Should AI agents be allowed to *write* to the hub?**
*Default:*
- They read freely and write only through `pn`, which enforces manifests and checks.
- `raw/` is read-only.
- No `--force` past a failed check without you.

**D3. Which AI tools will you use over the next year?**
Claude Code, Claude Desktop, Codex, Cursor, Gemini CLI, local models?
*Default:*
- `AGENTS.md` is canonical, and `CLAUDE.md` imports it.
- A read-only DuckDB MCP server and Claude skills wait until Phase 3, unless you use Claude Desktop heavily.

**D4. Pinning policy for analyses.**
*Default:*
- Projects float on current data while exploring.
- `pn pin` when drafting starts.
- `pn pack` at publication.

---

## E. Specific datasets

**E1. MDSP crash exports.** *(needs you)*
The dashboard is a public Tableau Server (`analytics.mdsp.org`, workbook `PublicCrash2`). Row-level tables come only from the UI's "Download → Data", but a `.csv` endpoint returns county × severity report counts for any date range, which lets intake reconcile your export automatically. The old Maryland Open Data crash tables are retired.

1. **Your recipe.** Is it "select the map → Download → Data → one tab per table, show all fields"?
2. **Extra tables.** The data model also has contributing-circumstances, damage, sequence-of-events and non-motorist safety-equipment tables. Do you want any of them?
3. **Automation.** Is a Playwright job that does the same public export (monthly, polite, off-hours) acceptable once Phase 2 arrives?
4. **Bulk access.** Do you want to ask MSP or MDOT's Highway Safety Office for bulk access, or file a Maryland Public Information Act request?

*Default until automation:*
- Keep your half-year cadence.
- Each time, export **the new half-year and the previous half-year, all four tables in one session**. Reports get revised, and mixing sessions caused issue #9.
- Pull only the four tables you use today.

**E2. Crash cost methodology.**
No newer NHTSA unit-cost edition exists. USDOT's 2026 benefit-cost guidance publishes KABCO crash values that map directly onto ACRS injury codes:
- VSL: $14.2M (2025 dollars);
- per injury level, 2024 dollars, unconfirmed against the PDF: K ≈ $13.7M, A ≈ $1.30M, B ≈ $256K, C ≈ $122K, O ≈ $5.5K.

Do you plan changes, such as medical CPI, a KABCO variant, or annual vs two-year per-capita figures?
*Default:*
- Method 2026.1 reproduces the published model exactly (June 2019 → June 2025 CPI-U).
- Future versions are separate and logged. The KABCO variant is an optional sensitivity check.

**E3. Data you've wanted but haven't gotten?**
Examples: speed/red-light camera citations (MoCo quarterly totals; Baltimore citation-level), MVA registrations/EVs, parcels and assessments, county permits, campaign finance, WMATA station time series, LODES commute flows.
*Default:* none added until a piece needs them.

**E4. Documents.**
Should the hub manage a document library: a catalog entry, the original file, and extracted text, with OCR on demand (e.g. the scanned HoCo Chamber questionnaires)?
*Default:* yes, lightweight, in Phase 2 when documents get reused.

**E5. Field data (photos, video, GPX).**
*Default:* stays in project folders. GPX is personal location data and is excluded from git.

---

## F. Publishing and integrity

**F1. Reproducibility standard.**
*Default:* every published piece gets a data pack, registered outputs (`pn.publish`), and chart IDs with versions. Old posts get retroactive packs where feasible: post 9 fully; posts 5, 7 and 10 partially.

**F2. Correction policy when sources revise.**
Crash reports, LAUS and Zillow all revise history. When a refresh changes a published number, what should happen?
*Default:*
- `pn status` lists packs whose inputs have since been revised beyond a threshold (e.g. >2%).
- You decide case by case whether to add an update note.
- Packs are never rewritten.

**F3. Raw retention.**
High-churn sources would grow without limits: weekly NIBRS, monthly Zillow, daily `legislation.json` during session.
*Default:*
- Skip unchanged snapshots.
- Compress raw text.
- Per-source retention, e.g. weekly snapshots thinned to monthly after 90 days.
- Anything referenced by a pack or pin is kept forever.

**F4. Issues in published posts surfaced by the audit (`01` §6).**
Whether and how to correct them is your call.

1. **US-29 chart `Mv21f`.**
   - The footnote correctly discloses that 2023 traffic is paired with 2019–26 deaths. The problem is the unit in the column label, "Deaths per 100 Million VMT".
   - The values shown (0.042 and 0.119) are 7 years of deaths ÷ one year of VMT in millions.
   - Correctly scaled (2023 VMT × ~7.08 years), they would be ≈0.59 and ≈1.68.
   - The ≈2.8× ratio between counties, which is the argument, is unaffected.
2. **US-29 passengers.** The processing notebook labels FARS passengers as "Non-Motorist". Whether the published motorist/non-motorist split (HoCo 13/6, MoCo 19/10) changes depends on which passengers fall inside the 400 m buffer. A re-check is worthwhile.
3. **MTA chart `N1hP3`.**
   - Post 10 embeds the chart's first version: its stored caption and the email image say "Jan. 2025".
   - A second version with January 2026 totals was published on 2026-08-31, before the post went out.
   - Web readers now see the Jan 2026 numbers under a Jan 2025 caption; email readers saw Jan 2025.
   - The text's claim holds in both versions.
4. **MoCo unemployment chart `uUKYy`.** It mixes the not-seasonally-adjusted county series with seasonally adjusted MD and US series.

*Default:* the proposal adds the safeguards (metric library, publish review, chart registry). Corrections are yours to decide.

---

## G. Secrets

**G1. One user-level key file.**
OK to keep all API keys in `%USERPROFILE%\.config\pn\.env` (outside the repo), and to rotate the IPUMS key? That key currently lives in two project folders, and `purple_line/ISSUES_LOG.md` (O6) says it was once pasted into a project doc.
*Default:* yes. Also get keys for:
- the Census API (now **required**);
- BLS;
- optionally FRED, api.data.gov, HUD, Open States/LegiScan and WMATA, when needed.

---

## Resolved without you (from the audit)

**The crash app uses the corrected data.** `crash_cost_app/data_cache/` was rebuilt on 2026-06-12, after the fixed H2-2025 Vehicles file and `crash_cost_eval.csv` (both 2026-06-06). Post 9 (2026-06-13) therefore used corrected data. The remaining caveat is issue #9: the 194 vehicle report numbers with no matching report.

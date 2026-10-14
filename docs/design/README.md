# Data hub — design folder

Status: **proposal v3** (2026-10-13): Matt's answers (`answers.md`) incorporated; v2 was revised after an independent review pass. Nothing outside this folder has been changed.

This folder holds the investigation of the existing data work and the proposal for a central, AI-legible data hub for *Perfect Numbers*.

## Reading order

| File | What it is | Read if you have… |
|---|---|---|
| [`03_proposal.md`](03_proposal.md) §0 | One-screen summary of the design | 2 minutes |
| [`04_questions.md`](04_questions.md) + [`answers.md`](answers.md) | The questions and Matt's answers (decisions summarized in `03` §0.2) | 10 minutes |
| [`03_proposal.md`](03_proposal.md) | Full design: drivers, architecture, workflows, technology choices and alternatives, quality standards, roadmap | 45 minutes |
| [`01_investigation.md`](01_investigation.md) | Evidence: posts → projects → datasets, duplication, verified integrity issues, practices worth keeping, requirements R1–R15 | 30 minutes |
| [`02_source_landscape.md`](02_source_landscape.md) | How to get each source systematically: endpoints, auth, cadence, verified status | as a reference |
| [`appendix_dataset_register.csv`](appendix_dataset_register.csv) | Existing datasets plus proposed additions → proposed ID, route, access mode, disposition, phase (66 rows) | as a reference |
| [`examples/`](examples/) | Concrete drafts of the standards: `AGENTS.md`, a dataset card, source cards, a raw manifest, a project manifest, metric definitions | to see what "good" looks like |

## Method notes

- **Scope.** Every folder under `2025/`, `2026/`, `data/` and `source/` was audited read-only. All 10 published posts were read, together with their 15 Datawrapper charts and source CSVs. External sources and tooling were researched on 2026-10-12.
- **Verification.** Every bug or discrepancy reported in `01` §6 was re-checked by hand. Load-bearing external facts were spot-checked directly: package versions, DuckLake 1.0, Claude Code's AGENTS.md handling, the Census key requirement, the MDSP Tableau endpoints, MGA `legislation.json`, the SBE CSVs, and the MoCo/BaCo crash feeds.
- **Secrets.** Credential files were located but never opened.

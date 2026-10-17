# Per-piece projects

A *piece* is one blog post or series. The hub holds reusable data; a project folder holds only what is specific to one piece.

## Layout

```
projects/<slug>/
  project.yml   # what the piece uses and produces (below)
  README.md     # question, decisions, status
  scripts/      # piece-specific analysis code (optional; notebooks also fine)
  outputs/      # maps, charts and tables for the draft (small files only; no data extracts)
```

`<slug>` is snake_case and stable (`baltimore_bus_lanes`). Drafts, photos and interview notes stay outside git.

## project.yml

```yaml
project: baltimore_bus_lanes
title: One-line title
uses:            # hub dataset IDs read by this piece (rule 1: query by ID, never copy files)
  - transit.bus_segment_summary
params:          # analysis choices that change numbers (service dates, thresholds, method versions)
  service_date_weekday: '2026-10-14'
pins:            # optional: build IDs a published number depends on, so it can be reproduced
  transit.bus_segment_service: 20261014T020219Z
outputs:         # what the piece publishes, with the window/vintage each one states
  - path: outputs/weekday_peak_bph.png
    window: GTFS weekday 2026-10-14
```

Pin builds once a number is final; until then, read the current build.

## README.md

Three short sections:
- **Question.** What the piece asks, in plain words.
- **Decisions.** Method choices and their reasons, dated. Estimated figures are labelled as estimates and carry a method version (e.g. `riders_v1`).
- **Status.** What is built, what is drafted, what is open.

## Where code goes

- **Reusable data becomes a hub dataset.** A new source gets a source card and `pn fetch`; tables get dataset cards, tests and `pn catalog` (intake standard: `docs/design/03_proposal.md` §5.3). If a second piece could use it, it belongs in the hub.
- **Piece-specific analysis lives in the project folder:** one-off joins, estimates for a single argument, map styling. Scripts read the hub with `pndata` (`pn.connect()`, `pn.read`, `pn.read_geo`) and write only to `outputs/`.
- Outputs state their time window and vintage (rule 4).

## Sessions and branches

Each piece gets its own agent session on its own branch (`claude/<slug>` or similar). Hub changes made for a piece (new sources, marts) are committed on that branch and merged to `main` with Matt's OK. Don't edit another piece's project folder or datasets another session owns.

# Crash Cost App — Design & Architecture Proposal

Status: **planning** (no code changes implied by this document yet).
Scope: how to publish the existing crash-cost map as an interactive, public web
page with a paired comparison dashboard, deployed cheaply and with minimal
ongoing maintenance.

This builds on the existing app described in [`README.md`](./README.md) and the
analysis methodology in [`../README.md`](../README.md). It does **not** propose
rewriting the working FastAPI + DuckDB + MapLibre/deck.gl stack.

---

## 1. TL;DR

- **Keep the current architecture** (static frontend + FastAPI/DuckDB API). It is
  already well-factored; the goal is to *publish* it, not rebuild it.
- **Deploy as a single Docker image to Fly.io** (scale-to-zero). One image, one
  deploy command, near-$0 when idle. FastAPI already serves the built frontend,
  so the whole app is one container.
- **Page layout:** map as the hero, a **sticky global filter bar** shared by map
  and dashboard, a **comparison dashboard of small-multiple rate charts** below,
  and a **Methodology & Sources** tab.
- **Add URL-encoded state** so any view is shareable (also closes the README's
  "no URL state" gap).
- A *fully static* (no server) variant via DuckDB-WASM remains a sensible future
  migration once the design is locked, but is intentionally **not** done now.

---

## 2. Architecture & deployment

### 2.1 Chosen path: single container on Fly.io

The existing split — geometry (static, cacheable) + parameterized summaries +
bbox crash points (server-aggregated via DuckDB) — is kept as-is. We package it
as one Docker image and run it on Fly.io.

Why Fly.io:

- **Quick:** `flyctl launch` reads a Dockerfile and gives a public
  `https://<app>.fly.dev` URL with automatic TLS.
- **Cheap:** scales to zero; the free allowance comfortably covers a low-traffic
  personal tool.
- **Simple:** one image, no separate static-host wiring (FastAPI serves
  `frontend/dist/` when present — see `app/main.py`).
- **Low maintenance:** no database service to run; data is baked into the image.

Accepted trade-off: a **few-second cold start** after idle. Fine for this use
case.

### 2.2 What ships in the image

- The FastAPI app (`backend/app/`).
- The built frontend (`frontend/dist/`), copied in at build time.
- `data_cache/` (Parquet + per-level GeoJSON + `meta.json`), baked into the
  image. It is ~15–25 MB and only changes on a data refresh, so image-baked is
  simpler than a mounted volume or object storage.

### 2.3 Repo, CI, and reusable pattern

Push to GitHub; a GitHub Actions workflow builds the frontend, builds the image,
and runs `flyctl deploy`.

Since similar tools are likely in the future, adopt a small reusable layout so
infra is solved once:

```text
your-tools-repo/
  apps/
    crash-costs/
      frontend/        # vite + react + ts
      backend/         # fastapi + duckdb
      Dockerfile       # builds frontend, serves it via fastapi
      fly.toml         # per-app fly config
  .github/workflows/deploy.yml   # deploy per app
```

Copy `apps/<name>/` for each new tool; one Fly account, one workflow.

### 2.4 One-time account setup (Fly.io)

1. Create a Fly.io account; add a card (verification — usage stays in free range).
2. Install `flyctl` and `flyctl auth login`.
3. In the app folder: `flyctl launch` (detects Dockerfile, writes `fly.toml`).
4. Confirm scale-to-zero (`min_machines_running = 0`) and a single small VM.
5. Optional: point a subdomain via your DNS (e.g. Cloudflare) at the Fly app;
   TLS is automatic.

### 2.5 Future option (not now): fully static

A no-server version would query a Parquet file in the browser with
**DuckDB-WASM** (or ship precomputed per-geo/per-month JSON), hosted on
Cloudflare/GitHub Pages for $0 and zero maintenance. Benefit: nothing to keep
alive. Cost: a real rewrite of the aggregation layer and a ~15 MB + WASM
first-load download. Revisit once the dashboard design is final.

---

## 3. Page design

### 3.1 Layout (top → bottom)

1. **Header / hero** — app title (e.g. *"What do Maryland's crashes cost?"*), a
   2–3 sentence explanation of why *comprehensive* cost matters, and one headline
   stat (total 2024–25 comprehensive cost). Slim **sticky nav** with tabs:
   **Map · Methodology & Sources · About**.
2. **Global filter bar (sticky)** — date range, crash type,
   pedestrian/cyclist, primary metric. Drives **both** map and dashboard.
3. **Map section** — the existing map at near-full-viewport height (the
   centerpiece).
4. **Dashboard section** — selected-geography chips, search bar, and the
   small-multiples comparison grid (see §4).
5. **Footer** — NHTSA citation, caveats (from the analysis README), attribution,
   GitHub link.

### 3.2 Visual system

- **Type:** keep **Inter** for UI; add a display face (e.g. **Fraunces** or a
  strong grotesque) for the hero only.
- **Map choropleth:** switch to a perceptually-uniform **sequential warm ramp**
  (amber → crimson) so "more cost = hotter" reads intuitively. Keep existing
  crash-type point colors.
- **Dashboard color = identity, not value.** Each *selected geography* gets one
  stable categorical color used as **both its chip color and its bar color across
  every small-multiple chart** — the key readability decision for comparison.
  **Maryland (default baseline)** gets a neutral anchor color.
- **Map ↔ dashboard linkage:** outline a selected geography's polygon on the map
  in its identity color so a bar ties back to a place.
- **Motion (subtle):** smooth-scroll + a brief highlight pulse on a newly added
  chip; bars animate on filter-driven value changes; `flyTo` when a place is
  chosen from search. **Framer Motion** for chip/scroll polish; charts animate
  themselves.

### 3.3 Charting library

Recommend **Recharts** (declarative React, IDE-friendly, animates bars by
default) for the small-multiples. Alternatives for denser/custom visuals:
**Observable Plot** (concise, great defaults) or **visx** (full d3 control, more
code). Start with Recharts.

---

## 4. Dashboard design

### 4.1 Two distinct modes

- **Geography comparison** (main dashboard): clicking a county/CDP/tract **adds
  it** to the comparison set.
- **Crash detail**: clicking an individual crash point opens a **detail card**,
  *not* a comparison bar — a single crash isn't comparable to area rates. The
  card shows the per-crash breakdown that previously lived in the hover popup.

### 4.2 Comparison view

- **Selected chips at top**, each removable, each in its identity color.
  **Maryland included by default** as the baseline.
- **Add geographies** by (a) clicking the map or (b) a **search bar** restricted
  to counties + CDPs/places (exclude tracts — nobody searches a tract by name).
- **Charts restricted to rate metrics** (per-capita / per-100k) so different
  geographic levels compare fairly. One rate metric = one small-multiple bar
  chart; bars = selected geographies.
- **Context strip of absolute totals** (total crashes, population, total
  comprehensive cost) per geography, so readers see the base the rates rest on.
- **Auto-scroll**: clicking a geography on the map smooth-scrolls to the
  dashboard and pulses the new chip.

### 4.3 Backend additions required

1. **Maryland/state-level aggregate** for the default baseline — a `state` level
   or `/api/summary/state` returning one row (DuckDB `GROUP BY ()`).
2. **Zoom-independent summary lookup.** The dashboard may show a county while the
   map is zoomed to tracts. Frontend caches summaries per `(level, filterArgs)`
   and looks up selected geoids from cache (county = 24 rows, places = a few
   hundred — cheap). Re-fetch when filters change.
3. **URL state.** Encode `?geos=…&metric=…&from=…&to=…&types=…&nm=` so views are
   shareable; also closes the README's "no URL state" gap.

### 4.4 Mobile

Hover does not exist on touch. Plan **tap = popup/select**, with the comparison
dashboard stacking vertically. Decide early since it shapes the click-to-add
interaction.

---

## 5. Suggested build order

1. **Deploy what exists** (Fly.io) → public URL + CI.
2. **URL state + global filter bar** (lift existing filters into shared state +
   URL).
3. **State-level aggregate + summary caching.**
4. **Selection model** (click map / search → selected geographies) + chips +
   auto-scroll.
5. **Comparison dashboard** (rate small-multiples + totals strip).
6. **Crash detail card** + **Methodology tab**.
7. **Visual polish** (palette, hero, motion).

---

## 6. Open decisions

- Display font for the hero.
- Exact choropleth ramp (warm sequential vs. existing quantile).
- Recharts vs. Observable Plot vs. visx for the dashboard.
- Mobile interaction details (tap-to-select affordance).
- Custom domain (yes/no) and which subdomain.

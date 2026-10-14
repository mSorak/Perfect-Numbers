# 0001 — Remake the repo pipeline-first

Date: 2026-10-13 · Status: accepted (Matt, `docs/design/answers.md` §C)

## Context
The old repo mixed blog text, photos, ~8 GB of data (one local commit that GitHub would reject), three diverged copies of the crash-cost app, and a separate clone used for publishing. The genuinely reusable, public-worthy part is the data pipeline.

## Decision
- The repo is the data hub. Its code, catalog and docs live at the root.
- Piece-specific work goes in `projects/<slug>/`, and only when it's worth keeping.
- Separate deployable projects (the crash-cost app, `mSorak/md_crash_costs`) keep their own repos.
- The repo lives on the dev PC outside OneDrive (`C:\Users\Matt\code\perfect-numbers`). Data lives in `PN_DATA_ROOT`, outside git.
- The old OneDrive `Perfect-Numbers` folder becomes a read-only archive; nothing is deleted. Its unpushed commit `3d29916` is never pushed.
- On GitHub, the previous `main` history is preserved under the tag `archive-2024-2026` before the new history replaces `main`.

## Consequences
- The public repo no longer carries blog text or per-post data folders. Published-post data is shared through data packs instead.
- The README's old promise ("code, data, and markdown versions for each post") is retired.

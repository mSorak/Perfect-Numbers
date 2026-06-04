# Deploying crash-costs (Fly.io + GitHub)

This app ships as **one Docker image**: Vite-built static files + FastAPI/DuckDB
+ baked-in `data_cache/`. Fly.io serves it on `https://<app>.fly.dev` with
scale-to-zero.

---

## Prerequisites

1. **Prepared data** on your machine (`data_cache/` — see `data_cache/README.md`).
2. **Fly.io account** and [flyctl](https://fly.io/docs/hands-on/install-flyctl/) installed.
3. **Docker** (optional but useful for a local smoke test before deploy).

---

## 1. Smoke-test the image locally

From this folder (`crash_cost_app` or `apps/crash-costs` after you copy it):

```powershell
docker build -t crash-cost-md .
docker run --rm -p 8080:8080 crash-cost-md
```

Open [http://127.0.0.1:8080](http://127.0.0.1:8080) and confirm the map loads.
Health check: [http://127.0.0.1:8080/api/health](http://127.0.0.1:8080/api/health).

If the build fails on `test -f crashes.parquet`, run `python prepare_data.py`
from `backend/` first.

---

## 2. First Fly.io deploy

```powershell
cd path\to\crash_cost_app   # or apps\crash-costs in the monorepo
fly auth login
fly launch
```

- When prompted, **use the existing `Dockerfile`** (do not generate a new one).
- Pick a region near users (`iad` is pre-set in `fly.toml`; Baltimore/DC area).
- Confirm **scale to zero** (`min_machines_running = 0` is already in `fly.toml`).
- If `fly launch` wants to change `app` name in `fly.toml`, accept or edit to taste.

Deploy (after launch, or for updates):

```powershell
fly deploy
```

`fly deploy` sends your **local** directory to Fly’s builder. Files in
`data_cache/` are included even though they are **not** in git, as long as they
exist on disk when you deploy.

Open the app:

```powershell
fly open
```

---

## 3. Push code to GitHub ([Perfect-Numbers](https://github.com/mSorak/Perfect-Numbers))

Target layout in the monorepo:

```text
Perfect-Numbers/
  apps/
    crash-costs/          # contents of crash_cost_app/
      backend/
      frontend/
      Dockerfile
      fly.toml
      ...
  README.md
  ... (existing post folders)
```

`data_cache/` stays **out of git**; only source code and deploy config are pushed.

### Option A — copy into an existing clone (simplest)

```powershell
# 1. Clone the blog repo (if you do not already have it)
cd $env:USERPROFILE\source\repos   # or wherever you keep clones
git clone https://github.com/mSorak/Perfect-Numbers.git
cd Perfect-Numbers

# 2. Create apps folder and copy the app (exclude generated junk)
mkdir apps -ErrorAction SilentlyContinue
robocopy "C:\Users\Matt\OneDrive\personal\research\Perfect-Numbers\2026\crash_costs\crash_cost_app" `
         ".\apps\crash-costs" /E /XD node_modules dist .venv venv __pycache__ .vite

# 3. Review what will be committed
git status
git add apps/crash-costs
git commit -m "Add Maryland crash-cost interactive map app under apps/crash-costs."
git push origin main
```

Adjust the `robocopy` source path if your working copy lives elsewhere.

### Option B — subtree from your research folder (if Perfect-Numbers is the parent git root)

If `Perfect-Numbers` is already the git root that contains `2026/crash_costs/`:

```powershell
cd C:\Users\Matt\OneDrive\personal\research\Perfect-Numbers
mkdir apps -ErrorAction SilentlyContinue
# Move or copy crash_cost_app → apps/crash-costs, then:
git add apps/crash-costs
git commit -m "Add Maryland crash-cost interactive map app under apps/crash-costs."
git push origin main
```

### After the repo is on GitHub

- **Clone on another machine:** run `prepare_data.py` there (needs parent
  `crash_costs/data/`), then `fly deploy` from `apps/crash-costs`.
- **CI (later):** a GitHub Action can run `fly deploy` only if the workflow
  builds or restores `data_cache/` (artifact, LFS, or regenerate from private
  data). Until then, deploy from your laptop is the reliable path.

---

## 4. Updates

| Change | Action |
|--------|--------|
| Frontend/backend code | `git push`, then `fly deploy` from app folder |
| Source crash CSV / shapes | Re-run `prepare_data.py`, then `fly deploy` |
| Fly VM size / region | Edit `fly.toml`, `fly deploy` |

```powershell
fly logs
fly status
fly scale show
```

---

## 5. Custom domain (optional)

In the Fly dashboard (or `fly certs add your.crashcosts.example`), attach a
hostname and add the DNS record Fly shows (often a CNAME to `<app>.fly.dev`).
TLS is automatic.

---

## 6. Security note

The app has **no authentication**. Suitable for a public research tool; add
rate limiting or auth before exposing sensitive or costly endpoints.

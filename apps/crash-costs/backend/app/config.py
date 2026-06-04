"""Static paths and constants for the backend."""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND_ROOT = HERE.parent
APP_ROOT = BACKEND_ROOT.parent

DATA_CACHE = APP_ROOT / "data_cache"
CRASHES_PARQUET = DATA_CACHE / "crashes.parquet"
GEO_CACHE = DATA_CACHE / "geo"
META_JSON = DATA_CACHE / "meta.json"

FRONTEND_DIST = APP_ROOT / "frontend" / "dist"

# CORS origins allowed when running the Vite dev server on a different port.
DEV_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

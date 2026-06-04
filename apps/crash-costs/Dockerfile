# syntax=docker/dockerfile:1
# Build from this directory (crash_cost_app / apps/crash-costs).
# Requires data_cache/ on the host (run backend/prepare_data.py first).

FROM node:22-alpine AS frontend-build
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/backend

COPY backend/requirements-prod.txt /tmp/requirements-prod.txt
RUN pip install --no-cache-dir -r /tmp/requirements-prod.txt

COPY backend/app ./backend/app
COPY data_cache ./data_cache
COPY --from=frontend-build /build/frontend/dist ./frontend/dist

RUN test -f /app/data_cache/crashes.parquet \
    && test -f /app/data_cache/meta.json \
    && test -d /app/frontend/dist

EXPOSE 8080
WORKDIR /app/backend
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]

"""Connectors: each `fetch(cfg, workdir) -> meta` writes the source's bytes into workdir unchanged."""

from pndata.connectors import arcgis, bls_api, census_api, http_file, powerbi_public, socrata

CONNECTORS = {
    "http_file": http_file.fetch,
    "arcgis": arcgis.fetch,
    "socrata": socrata.fetch,
    "powerbi_public": powerbi_public.fetch,
    "bls_api": bls_api.fetch,
    "census_api": census_api.fetch,
}

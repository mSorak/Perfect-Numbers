"""Connectors: each `fetch(cfg, workdir) -> meta` writes the source's bytes into workdir unchanged."""

from pndata.connectors import arcgis, bls_api, census_api, http_file, powerbi_public, socrata, tableau_public

CONNECTORS = {
    "http_file": http_file.fetch,
    "arcgis": arcgis.fetch,
    "socrata": socrata.fetch,
    "powerbi_public": powerbi_public.fetch,
    "bls_api": bls_api.fetch,
    "census_api": census_api.fetch,
}

# Batch connectors fetch every entity of a source for one period in one session: `fetch(cfg, workdir) -> meta`,
# where meta["tables"][entity]["file"] names each file. `pn fetch` hands the files to `pn intake` checks.
BATCH_CONNECTORS = {
    "tableau_public": tableau_public.fetch,
}

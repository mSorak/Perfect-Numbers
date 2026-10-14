"""Read-side API: an in-memory DuckDB with every dataset as a view (from catalog.sql)."""

from __future__ import annotations

import duckdb

from pndata.config import data_root

SESSION_SETUP = "INSTALL spatial; LOAD spatial; SET geometry_always_xy = true;"


def new_connection() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(SESSION_SETUP)
    con.execute(f"SET temp_directory = '{(data_root() / 'tmp').as_posix()}'")
    return con


def connect() -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB with all current datasets as views. Never holds a database file open."""
    con = new_connection()
    catalog_sql = data_root() / "catalog.sql"
    if catalog_sql.exists():
        con.execute(catalog_sql.read_text(encoding="utf-8"))
    return con


def read(dataset_id: str, where: str | None = None):
    """Return a dataset (optionally filtered) as a pandas DataFrame."""
    sql = f"FROM {dataset_id}" + (f" WHERE {where}" if where else "")
    return connect().sql(sql).df()


def read_geo(dataset_id: str, where: str | None = None, geometry: str = "geometry"):
    """Return a dataset as a GeoDataFrame (requires geopandas)."""
    import geopandas as gpd
    from shapely import wkb
    con = connect()
    sql = f"SELECT * REPLACE (ST_AsWKB({geometry}) AS {geometry}) FROM {dataset_id}" + (f" WHERE {where}" if where else "")
    df = con.sql(sql).df()
    df[geometry] = df[geometry].apply(lambda b: wkb.loads(bytes(b)) if b is not None else None)
    return gpd.GeoDataFrame(df, geometry=geometry, crs="OGC:CRS84")

"""Perfect Numbers data hub."""

__version__ = "0.1.0"


def connect():
    from pndata.db import connect as _connect
    return _connect()


def read(dataset_id: str, where: str | None = None):
    from pndata.db import read as _read
    return _read(dataset_id, where)


def read_geo(dataset_id: str, where: str | None = None, geometry: str = "geometry"):
    from pndata.db import read_geo as _read_geo
    return _read_geo(dataset_id, where, geometry)


def describe(dataset_id: str) -> str:
    from pndata.config import GENERATED_DIR
    page = GENERATED_DIR / "datasets" / f"{dataset_id}.md"
    text = page.read_text(encoding="utf-8") if page.exists() else f"No generated page for {dataset_id}; run `pn catalog`."
    print(text)
    return text

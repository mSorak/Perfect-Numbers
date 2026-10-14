"""Locations and secrets: the one place that knows where data, cards and keys live."""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_DIR = REPO_ROOT / "catalog"
DATASETS_DIR = CATALOG_DIR / "datasets"
SOURCES_DIR = CATALOG_DIR / "sources"
SEEDS_DIR = CATALOG_DIR / "seeds"
MANIFEST_FILE = CATALOG_DIR / "manifests" / "raw_manifest.jsonl"
GENERATED_DIR = CATALOG_DIR / "generated"

DEFAULT_DATA_ROOT = Path.home() / "pn-data"
KEYS_FILE = Path.home() / ".config" / "pn" / ".env"
DATA_ROOT_LAYERS = ("inbox", "raw", "cache/api", "docs", "packs", "staging", "marts", "tmp")
USER_AGENT = "pndata/0.1 (Perfect Numbers data hub; https://github.com/mSorak/Perfect-Numbers)"


def data_root() -> Path:
    return Path(os.environ.get("PN_DATA_ROOT", DEFAULT_DATA_ROOT))


def load_keys(path: Path = KEYS_FILE) -> dict[str, str]:
    """Read KEY=value lines; blank values are treated as missing."""
    keys: dict[str, str] = {}
    if not path.exists():
        return keys
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        if value:
            keys[name.strip()] = value
    return keys


def get_key(name: str, required: bool = True) -> str | None:
    """Return a key from the environment or the keys file; never log the value."""
    value = os.environ.get(name) or load_keys().get(name)
    if not value and required:
        raise KeyError(f"{name} is not set; add it to {KEYS_FILE}")
    return value

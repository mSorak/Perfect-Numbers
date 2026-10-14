"""Where builds live: <layer>/<domain>/<dataset>/build=<id>.parquet plus _current.json."""

from __future__ import annotations

import json
from pathlib import Path

from pndata.cards import layer_dir
from pndata.config import data_root


def dataset_dir(card: dict) -> Path:
    domain, name = card["id"].split(".", 1)
    return data_root() / layer_dir(card) / domain / name


def current_build(card: dict) -> dict | None:
    p = dataset_dir(card) / "_current.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def build_file(card: dict, build_id: str) -> Path:
    return dataset_dir(card) / f"build={build_id}.parquet"


def posix(p: Path) -> str:
    return Path(p).as_posix()

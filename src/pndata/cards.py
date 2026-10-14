"""Load dataset cards (catalog/datasets/**.yml) and source cards (catalog/sources/*.yml)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from pndata.config import DATASETS_DIR, SOURCES_DIR


@lru_cache(maxsize=None)
def dataset_cards() -> dict[str, dict]:
    cards = {}
    for p in sorted(DATASETS_DIR.rglob("*.yml")):
        card = yaml.safe_load(p.read_text(encoding="utf-8"))
        card["_path"] = p
        if card["id"] in cards:
            raise ValueError(f"duplicate dataset id {card['id']}")
        cards[card["id"]] = card
    return cards


@lru_cache(maxsize=None)
def source_cards() -> dict[str, dict]:
    cards = {}
    for p in sorted(SOURCES_DIR.glob("*.yml")):
        card = yaml.safe_load(p.read_text(encoding="utf-8"))
        card["_path"] = p
        cards[card["source_id"]] = card
    return cards


def dataset(dataset_id: str) -> dict:
    try:
        return dataset_cards()[dataset_id]
    except KeyError:
        raise KeyError(f"no dataset card for {dataset_id!r}") from None


def dataset_deps(card: dict) -> list[str]:
    return [d for d in card.get("depends_on", []) if not d.startswith(("raw:", "seed:"))]


def layer_dir(card: dict) -> str:
    return {"staging": "staging", "mart": "marts", "seed": "staging"}[card.get("layer", "staging")]


def resolve_glob(pattern: str) -> list[str]:
    """Expand ids like 'geo.*_display' against known cards."""
    import fnmatch
    return [i for i in dataset_cards() if fnmatch.fnmatch(i, pattern)] if "*" in pattern else [pattern]


def card_path_rel(card: dict) -> str:
    return Path(card["_path"]).as_posix()

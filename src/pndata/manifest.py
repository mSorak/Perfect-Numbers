"""Raw snapshots: immutable folders under raw/ plus one committed manifest line per snapshot."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pndata import __version__
from pndata.config import MANIFEST_FILE, REPO_ROOT, data_root

SECRET_PARAMS = {"key", "api_key", "apikey", "token", "registrationkey", "app_token", "$$app_token"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def snapshot_id(when: datetime | None = None, period: str | None = None) -> str:
    sid = (when or utc_now()).strftime("%Y%m%dT%H%MZ")
    return f"{sid}__{period}" if period else sid


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def redact(params: dict | None) -> dict | None:
    if not params:
        return params
    return {k: ("<redacted>" if k.lower() in SECRET_PARAMS else v) for k, v in params.items()}


def git_sha() -> str | None:
    try:
        return subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None


def read_manifest() -> list[dict]:
    if not MANIFEST_FILE.exists():
        return []
    return [json.loads(line) for line in MANIFEST_FILE.read_text(encoding="utf-8").splitlines() if line.strip()]


def latest_snapshot(source_id: str, entity: str) -> dict | None:
    """Latest snapshot recorded in the committed manifest (not by scanning folders)."""
    rows = [r for r in read_manifest() if r["source_id"] == source_id and r["entity"] == entity]
    return max(rows, key=lambda r: r["retrieved_at"]) if rows else None


def snapshot_dir(record: dict) -> Path:
    return data_root() / record["path"]


def commit_snapshot(workdir: Path, source_id: str, entity: str, meta: dict,
                    period: str | None = None) -> dict | None:
    """Hash files in workdir; skip if identical to the latest snapshot; else move into raw/ read-only."""
    files = sorted(p for p in workdir.rglob("*") if p.is_file())
    if not files:
        raise RuntimeError(f"{source_id}/{entity}: fetch produced no files")
    file_info = [{"name": p.relative_to(workdir).as_posix(), "bytes": p.stat().st_size,
                  "sha256": sha256_file(p)} for p in files]
    # Files starting with "_" are request/response metadata (may be volatile) and don't count as a change.
    data_files = [f for f in file_info if not Path(f["name"]).name.startswith("_")] or file_info
    combined = hashlib.sha256("".join(f["name"] + f["sha256"] for f in data_files).encode()).hexdigest()

    prev = latest_snapshot(source_id, entity)
    if prev and prev.get("sha256") == combined and (period is None or prev.get("period") == period):
        shutil.rmtree(workdir, ignore_errors=True)
        return None

    sid = snapshot_id(period=period)
    rel = Path("raw") / source_id / entity / sid
    dest = data_root() / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(workdir), str(dest))
    for p in dest.rglob("*"):
        if p.is_file():
            os.chmod(p, stat.S_IREAD)  # read-only attribute on Windows

    record = {
        "snapshot_id": sid, "source_id": source_id, "entity": entity, "path": rel.as_posix(),
        "retrieved_at": utc_now().isoformat(timespec="seconds"), "sha256": combined,
        "files": file_info, "period": period, "pn_version": __version__, "fetch_code_sha": git_sha(),
        **meta,
    }
    if "request" in record and isinstance(record["request"], dict):
        record["request"] = {**record["request"], "params": redact(record["request"].get("params"))}
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, default=str) + "\n")
    return record

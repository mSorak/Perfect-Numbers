"""`pn intake` on synthetic files in a temporary data root (the real manifest is never touched)."""

import json
import os
import stat
from datetime import date, datetime, timezone

import pytest

import pndata.manifest as manifest
from pndata.intake import IntakeError, detect_entity, intake, parse_period

SOURCE = {
    "source_id": "test_src",
    "entities": {
        "reports": {"header_signature": ["Reportnumber", "Crashdate"], "key": ["Reportnumber"],
                    "date_column": "Crashdate", "date_format": "%m/%d/%Y"},
        "vehicles": {"header_signature": ["ReportNumber Veh", "VehicleID"], "key": ["ReportNumber Veh", "VehicleID"],
                     "parent": {"entity": "reports", "key": "ReportNumber Veh", "parent_key": "Reportnumber",
                                "max_orphan_pct": 0.0}},
        "extra": {"required": False},
    },
    "intake": {"same_session_hours": 12,
               "waivers": {"legacy_mixed_session": {"waives": ["same_session", "orphans"]}}},
}


@pytest.fixture
def root(tmp_path, monkeypatch):
    monkeypatch.setenv("PN_DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setattr(manifest, "MANIFEST_FILE", tmp_path / "manifest.jsonl")
    for layer in ("inbox/test_src", "raw", "tmp"):
        (tmp_path / "data" / layer).mkdir(parents=True)
    return tmp_path


def write(path, text, mtime=None):
    path.write_text("﻿" + text, encoding="utf-8")
    if mtime:
        ts = mtime.timestamp()
        os.utime(path, (ts, ts))
    return path


def batch(root, veh_extra="", veh_time=None, dates=("3/18/2025", "6/30/2025")):
    t = datetime(2026, 3, 28, 17, 0, tzinfo=timezone.utc)
    inbox = root / "data" / "inbox" / "test_src"
    r = write(inbox / "Reports_a.csv", f"Reportnumber,Crashdate\nA1,{dates[0]}\nA2,{dates[1]}\n", t)
    v = write(inbox / "Vehicles_a.csv", f"ReportNumber Veh,VehicleID\nA1,v1\nA1,v2\nA2,v3\n{veh_extra}", veh_time or t)
    return r, v


def test_parse_period():
    assert parse_period("2025H2") == (date(2025, 7, 1), date(2025, 12, 31))
    assert parse_period("2025Q4") == (date(2025, 10, 1), date(2025, 12, 31))
    assert parse_period("2024-02") == (date(2024, 2, 1), date(2024, 2, 29))
    with pytest.raises(ValueError):
        parse_period("H2-2025")


def test_detect_entity():
    assert detect_entity(["x", "VehicleID", "ReportNumber Veh"], SOURCE["entities"]) == "vehicles"
    assert detect_entity(["nope"], SOURCE["entities"]) is None


def test_inbox_intake_moves_and_records(root):
    r, v = batch(root)
    recs = intake(SOURCE, "2025H1", reconcile=False, log=lambda *_: None)
    assert {x["entity"] for x in recs} == {"reports", "vehicles"}
    assert not r.exists() and not v.exists()  # moved out of the inbox
    rep = next(x for x in recs if x["entity"] == "reports")
    assert rep["snapshot_id"] == "20260328T1700Z__2025H1"
    assert rep["retrieved_at_method"] == "file mtime" and rep["rows"] == 2
    f = root / "data" / rep["path"] / "Reports_a.csv"
    assert not os.stat(f).st_mode & stat.S_IWRITE  # read-only
    lines = (root / "manifest.jsonl").read_text().splitlines()
    assert len(lines) == 2 and json.loads(lines[0])["intake_checks"]["key_unique"]["status"] == "pass"


def test_copy_leaves_originals_and_dedups(root):
    r, v = batch(root)
    intake(SOURCE, "2025H1", [r, v], copy=True, reconcile=False, log=lambda *_: None)
    assert r.exists() and v.exists()
    assert intake(SOURCE, "2025H1", [r, v], copy=True, reconcile=False, log=lambda *_: None) == []


def test_orphans_and_mixed_session_fail_then_waive(root):
    late = datetime(2026, 6, 6, 18, 29, tzinfo=timezone.utc)
    r, v = batch(root, veh_extra="ZZ9,v9\n", veh_time=late)
    with pytest.raises(IntakeError, match="orphans.*same_session|same_session.*orphans|vehicles.orphans"):
        intake(SOURCE, "2025H1", [r, v], copy=True, reconcile=False, log=lambda *_: None)
    assert not (root / "manifest.jsonl").exists()  # nothing committed
    recs = intake(SOURCE, "2025H1", [r, v], copy=True, reconcile=False, waivers=["legacy_mixed_session"],
                  waiver_note="test", log=lambda *_: None)
    veh = next(x for x in recs if x["entity"] == "vehicles")
    assert veh["intake_checks"]["orphans"]["status"] == "waived"
    assert veh["snapshot_id"] == "20260606T1829Z__2025H1"


def test_dates_outside_period_fail(root):
    r, v = batch(root, dates=("3/18/2025", "7/1/2025"))
    with pytest.raises(IntakeError, match="dates_in_period"):
        intake(SOURCE, "2025H1", [r, v], copy=True, reconcile=False, log=lambda *_: None)


def test_unknown_header_and_missing_entity(root):
    r, _ = batch(root)
    bad = write(root / "data" / "inbox" / "test_src" / "junk.csv", "a,b\n1,2\n")
    with pytest.raises(RuntimeError, match="matches no entity"):
        intake(SOURCE, "2025H1", [r, bad], copy=True, reconcile=False, log=lambda *_: None)
    with pytest.raises(IntakeError, match="entities_present"):
        intake(SOURCE, "2025H1", [r], copy=True, reconcile=False, log=lambda *_: None)

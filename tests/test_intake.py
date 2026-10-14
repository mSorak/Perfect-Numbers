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


def test_explicit_entity_for_non_csv(root):
    z = root / "data" / "inbox" / "test_src" / "bundle.zip"
    z.write_bytes(b"PK\x05\x06" + b"\x00" * 18)
    src = {**SOURCE, "entities": {**SOURCE["entities"], "bundle": {"required": False}}}
    recs = intake(src, "2021", [z], copy=True, entity="bundle", reconcile=False, log=lambda *_: None)
    assert recs[0]["entity"] == "bundle" and recs[0]["intake_checks"]["file"]["status"] == "pass"
    with pytest.raises(ValueError, match="--entity"):
        intake(src, "2021", [z, z], copy=True, entity="bundle", reconcile=False, log=lambda *_: None)


def test_month_helpers():
    from pndata.intake import month_range, trailing_months
    assert month_range("2025-11:2026-02") == ["2025-11", "2025-12", "2026-01", "2026-02"]
    assert month_range("2026-09") == ["2026-09"]
    assert trailing_months(9, date(2026, 11, 7)) == month_range("2026-02:2026-10")
    assert trailing_months(1, date(2026, 1, 7)) == ["2025-12"]


def test_expected_entity_must_match_header(root):
    r, v = batch(root)
    with pytest.raises(RuntimeError, match="connector says vehicles"):
        intake(SOURCE, "2025H1", [r, v], copy=True, reconcile=False,
               expected={r.name: "vehicles"}, log=lambda *_: None)


def test_reordered_rows_are_not_a_new_snapshot(root):
    r, v = batch(root)
    intake(SOURCE, "2025H1", [r, v], copy=True, reconcile=False, log=lambda *_: None)
    r2 = write(root / "Reports_b.csv", "Reportnumber,Crashdate\nA2,6/30/2025\nA1,3/18/2025\n", None)
    v2 = write(root / "Vehicles_b.csv", "VehicleID,ReportNumber Veh\nv3,A2\nv1,A1\nv2,A1\n", None)
    assert intake(SOURCE, "2025H1", [r2, v2], copy=True, reconcile=False, log=lambda *_: None) == []
    r3 = write(root / "Reports_c.csv", "Reportnumber,Crashdate\nA2,6/29/2025\nA1,3/18/2025\n", None)
    recs = intake(SOURCE, "2025H1", [r3, v2], copy=True, reconcile=False, log=lambda *_: None)
    assert [x["entity"] for x in recs] == ["reports"]  # a real change is committed


def test_exact_duplicate_rows_warn_but_conflicts_fail(root):
    r, v = batch(root, veh_extra="A2,v3\n")  # exact repeat of a row
    recs = intake(SOURCE, "2025H1", [r, v], copy=True, reconcile=False, log=lambda *_: None)
    veh = next(x for x in recs if x["entity"] == "vehicles")
    assert veh["intake_checks"]["key_unique"]["status"] == "warn"
    assert veh["intake_checks"]["key_unique"]["value"]["exact_duplicate_rows"] == 1
    bad = write(root / "Reports_x.csv", "Reportnumber,Crashdate\nA1,3/18/2025\nA1,3/19/2025\nA2,6/30/2025\n")
    with pytest.raises(IntakeError, match="reports.key_unique"):  # same key, different date: conflict
        intake(SOURCE, "2025H1", [bad, v], copy=True, reconcile=False, log=lambda *_: None)

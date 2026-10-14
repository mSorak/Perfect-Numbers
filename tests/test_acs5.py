"""census.acs5 parsing on synthetic Census API output (the real fetch needs a working key)."""

import importlib.util
import json

from pndata.config import REPO_ROOT


def _mod():
    spec = importlib.util.spec_from_file_location("acs5", REPO_ROOT / "pipelines" / "census" / "acs5.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_long_format_with_jams(tmp_path):
    (tmp_path / "B01003_variables.json").write_text(json.dumps(
        {"variables": {"B01003_001E": {"label": "Estimate!!Total"}}}))
    (tmp_path / "B01003_county.json").write_text(json.dumps([
        ["NAME", "GEO_ID", "B01003_001E", "B01003_001EA", "B01003_001M", "B01003_001MA", "NAME", "state", "county"],
        ["Howard County, Maryland", "0500000US24027", "336328", None, "-555555555", "*****", "Howard County, Maryland", "24", "027"],
        ["Fake County, Maryland", "0500000US24999", "-666666666", "-", "-222222222", "**", "Fake County, Maryland", "24", "999"],
    ]))
    df = _mod().long_from_snapshot(tmp_path, 2024, "ACS 2020–2024 5-year", "snap")
    howard = df[df.geoid == "24027"].iloc[0]
    assert (howard.variable, howard.estimate, howard.geo_level) == ("B01003_001", 336328, "county")
    assert howard.moe != howard.moe  # NaN: -555555555 means 'controlled, no MOE'
    fake = df[df.geoid == "24999"].iloc[0]
    assert fake.estimate != fake.estimate and fake.annotation == "-"

"""Parity: the hub's crash-cost code, run on the legacy half-year MDSP exports, must reproduce the published
model's output (crash_cost_eval.csv, 2026-04) row for row on every cost column.

Needs the data root and the read-only archive on Matt's PC; skipped elsewhere. Run: uv run pytest -m parity
"""

import importlib.util
from pathlib import Path

import pytest

from pndata.build import BuildContext, attach_dependencies
from pndata.config import REPO_ROOT, data_root
from pndata.db import new_connection

LEGACY_EVAL = Path(r"C:\Users\Matt\OneDrive\personal\research\Perfect-Numbers\2026\crash_costs\data\crash_cost_eval.csv")
COMPONENTS = {  # published column stem → hub component
    "Medical": "medical", "EMS": "ems", "MarketProd": "market_productivity", "HouseholdProd": "household_productivity",
    "InsuranceAdmin": "insurance_admin", "WorkplaceCosts": "workplace", "LegalCosts": "legal",
    "Congestion": "congestion", "PropDamage": "property_damage", "Total_Economic": "total_economic",
    "QALYs": "quality_of_life", "TotalComp": "total_comprehensive",
}

pytestmark = [pytest.mark.parity,
              pytest.mark.skipif(not LEGACY_EVAL.exists() or not (data_root() / "raw" / "mdsp_acrs").exists(),
                                 reason="needs the data root and the legacy archive")]


def _acrs():
    spec = importlib.util.spec_from_file_location("acrs", REPO_ROOT / "pipelines" / "crash" / "acrs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def con():
    acrs = _acrs()
    con = new_connection()
    card = {"id": "parity", "parameters": {"snapshot_grain": "half_year"},
            "depends_on": ["ref.county_codes", "ref.nhtsa_unit_cost_2019", "ref.acrs_injury_to_mais",
                           "geo.county", "geo.tract"]}
    attach_dependencies(con, card)
    ctx = BuildContext(card)
    con.execute(f"CREATE TABLE r AS {acrs.acrs_report_sql(acrs._src(ctx, 'reports'))}")
    con.execute(f"CREATE TABLE v AS {acrs.acrs_vehicle_sql(acrs._src(ctx, 'vehicles'))}")
    con.execute(f"CREATE TABLE p AS {acrs.acrs_person_sql(acrs._src(ctx, 'occupants'), acrs._src(ctx, 'nonmotorists'))}")
    con.execute(f"CREATE TABLE cost AS {acrs.report_cost_sql('r', 'v', 'p', 1.26, 'legacy_factor 1.26', 2025)}")
    con.execute(f"CREATE TABLE g AS {acrs.report_geo_sql('r')}")
    con.execute(f"CREATE TABLE pub AS FROM read_csv('{LEGACY_EVAL.as_posix()}', all_varchar = true)")
    con.execute("CREATE TABLE j AS SELECT * FROM cost c FULL JOIN pub ON pub.Reportnumber = c.report_number")
    return con


def test_snapshots_are_the_legacy_half_years(con):
    periods = [r[0] for r in con.sql("SELECT DISTINCT source_period FROM r ORDER BY 1").fetchall()]
    assert periods == ["2024H1", "2024H2", "2025H1", "2025H2"]


def test_same_reports(con):
    assert con.sql("SELECT count(*) FROM cost").fetchone()[0] == 210_860
    only = con.sql("SELECT count(*) FILTER (WHERE Reportnumber IS NULL), count(*) FILTER (WHERE report_number IS NULL) FROM j").fetchone()
    assert only == (0, 0), f"reports only in hub / only in published: {only}"


@pytest.mark.parametrize("pub, hub", COMPONENTS.items())
def test_component_row_for_row(con, pub, hub):
    bad = con.sql(f"""SELECT count(*), max(abs(c - p)) FROM (
                        SELECT {hub}_usd2025 c, estimated_{pub}_comp_cost_2025usd::DOUBLE p FROM j)
                      WHERE abs(c - p) > 0.005 + 1e-9 * abs(p)""").fetchone()
    assert bad[0] == 0, f"{bad[0]} reports differ on {pub}; max diff {bad[1]}"


def test_published_annual_totals(con):
    got = dict(con.sql("SELECT crash_year, round(sum(total_comprehensive_usd2025) / 1e9, 3) FROM cost GROUP BY 1").fetchall())
    assert got == {2024: 41.044, 2025: 37.339}


def test_inputs_match_published_counts(con):
    """Vehicle and person counts per report, which drive the costs."""
    bad = con.sql("""SELECT count(*) FROM j WHERE n_vehicles <> n_vehicle_records::BIGINT
                     OR n_persons <> n_occupant_records::BIGINT + n_nonmotorist_records::BIGINT""").fetchone()[0]
    assert bad == 0


def test_geography_row_for_row(con):
    """Point-in-polygon county and tract match the published spatial join wherever it assigned one.
    Known, deliberate difference: the published join used shoreline-clipped NHGIS shapes and left crashes on
    water (bridges, tunnels, harbor) unassigned; the hub's TIGER polygons include water and assign them
    (461 reports, $194.8M, 2024-2025). One point sits on a three-tract corner and may pick another tract."""
    got = con.sql("""SELECT
        count(*) FILTER (WHERE pub.GEOID_county IS NOT NULL AND g.county_geoid IS DISTINCT FROM pub.GEOID_county),
        count(*) FILTER (WHERE pub.GEOID_tract IS NOT NULL AND g.tract_geoid IS DISTINCT FROM pub.GEOID_tract),
        count(*) FILTER (WHERE pub.GEOID_county IS NULL AND g.county_geoid IS NOT NULL)
        FROM g JOIN pub ON pub.Reportnumber = g.report_number""").fetchone()
    county_disagree, tract_disagree, water_assigned = got
    assert county_disagree == 0
    assert tract_disagree <= 1, f"{tract_disagree} tracts disagree where the published join assigned one"
    assert water_assigned == 461


def test_howard_2025_numerator(con):
    """Pre-registered exit answer, numerator: Howard County (spatial) 2025 = $1.2995B."""
    b = con.sql("""SELECT round(sum(total_comprehensive_usd2025) / 1e9, 4) FROM cost JOIN g USING (report_number)
                   WHERE g.county_geoid = '24027' AND crash_year = 2025""").fetchone()[0]
    assert b == 1.2995


def test_howard_2025_cost_per_resident(con):
    """Pre-registered exit answer: Howard County 2025 cost per resident ≈ $3,864 ($1.2995B ÷ 336,328,
    ACS 2020–24 5-year B01003). Skipped until census.acs5 is built (needs a working CENSUS_API_KEY)."""
    from pndata.builds import current_build
    from pndata.cards import dataset
    cur = current_build(dataset("census.acs5"))
    if cur is None:
        pytest.skip("census.acs5 not built yet")
    pop = con.sql(f"""SELECT estimate FROM read_parquet('{cur['path']}')
                      WHERE geo_level = 'county' AND geoid = '24027' AND variable = 'B01003_001' AND vintage = 2024""").fetchone()[0]
    assert pop == 336_328
    cost = con.sql("""SELECT sum(total_comprehensive_usd2025) FROM cost JOIN g USING (report_number)
                      WHERE g.county_geoid = '24027' AND crash_year = 2025""").fetchone()[0]
    assert round(cost / pop) == 3864

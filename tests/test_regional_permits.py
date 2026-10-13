"""TDD for regional building permits (PS-TOPICS-04).

Each publisher's feed is normalized to one structure-permit schema: per-source
include/exclude rules drop trade-only and administrative records, a uniform
2016+ window applies, impossible dates are nulled (not trusted), keys are
source-qualified, and only mapped fields survive (no applicant/owner names).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pandas as pd
import pytest

from regional_permits import NORMALIZED_COLUMNS, PermitSource, normalize_permits

TODAY = date(2026, 10, 12)
START = date(2016, 1, 1)


def norm(spec: PermitSource, rows: list[dict]) -> pd.DataFrame:
    return normalize_permits(spec, pd.DataFrame(rows), start=START, today=TODAY)


@pytest.fixture
def spec() -> PermitSource:
    return PermitSource(
        source_id="test.city",
        publisher="Test City",
        platform="arcgis",
        endpoint="https://example.org/arcgis/rest/services/Permits/FeatureServer/0",
        county_fips="53053",
        coverage="City",
        jurisdiction="Test City",
        fields={
            "permit_number": "PNUM",
            "permit_class": "PTYPE",
            "status": "STATUS",
            "applied_date": "APPLIED",
            "issue_date": "ISSUED",
            "valuation": "VALUE",
            "housing_units": "UNITS",
            "address": "ADDR",
            "latitude": "_lat",
            "longitude": "_lon",
        },
        include={"PTYPE": ("New Building", "Alteration", "Demolition")},
        valuation_basis="Declared valuation",
    )


def row(**over) -> dict:
    base = {
        "PNUM": "B1", "PTYPE": "New Building", "STATUS": "Issued",
        "APPLIED": "2020-01-02", "ISSUED": "2020-02-03", "VALUE": "250000",
        "UNITS": "1", "ADDR": "1 Main St", "_lat": 47.25, "_lon": -122.44,
        "APPLICANT_NAME": "Private Person",
    }
    base.update(over)
    return base


def test_output_is_exactly_the_normalized_schema(spec):
    out = norm(spec, [row()])
    assert list(out.columns) == list(NORMALIZED_COLUMNS)
    assert "APPLICANT_NAME" not in out.columns


def test_include_rule_keeps_only_listed_types_after_trimming(spec):
    out = norm(spec, [
        row(PNUM="a", PTYPE="New Building "),
        row(PNUM="b", PTYPE="Mechanical"),
        row(PNUM="c", PTYPE="Demolition"),
    ])
    assert sorted(out["permit_number"]) == ["a", "c"]
    assert set(out["permit_class"]) == {"New Building", "Demolition"}


def test_exclude_rule_drops_listed_types(spec):
    spec = replace(spec, include={},
                           exclude={"PTYPE": ("Mechanical", "Plumbing")})
    out = norm(spec, [row(PNUM="a"), row(PNUM="b", PTYPE="Plumbing"),
                      row(PNUM="c", PTYPE=None)])
    assert sorted(out["permit_number"]) == ["a", "c"]


def test_dates_parse_from_iso_strings_and_epoch_millis(spec):
    out = norm(spec, [
        row(PNUM="iso"),
        row(PNUM="ms", APPLIED=1577923200000, ISSUED=1580688000000),  # 2020-01-02, 2020-02-03
    ])
    by = out.set_index("permit_number")
    assert by.loc["iso", "issue_date"] == date(2020, 2, 3)
    assert by.loc["ms", "issue_date"] == date(2020, 2, 3)
    assert by.loc["ms", "applied_date"] == date(2020, 1, 2)


def test_offset_timestamps_take_the_pacific_calendar_date(spec):
    out = norm(spec, [
        row(PNUM="morning", ISSUED="2020-02-03T08:00:00.000Z"),
        row(PNUM="evening", ISSUED="2020-02-04T03:00:00Z"),  # 7 pm Feb 3 Pacific
        row(PNUM="naive", ISSUED="2020-02-03T00:00:00.000"),
    ])
    assert set(out["issue_date"]) == {date(2020, 2, 3)}


def test_future_and_unparseable_dates_are_nulled(spec):
    out = norm(spec, [
        row(PNUM="future", ISSUED="2914-05-27", APPLIED="2025-01-01"),
        row(PNUM="junk", ISSUED="not a date", APPLIED="2025-01-01"),
    ])
    assert out["issue_date"].isna().all()
    assert len(out) == 2  # still in window by applied date


def test_window_keeps_2016_onward_by_issue_or_applied(spec):
    out = norm(spec, [
        row(PNUM="old", APPLIED="2014-01-01", ISSUED="2015-06-01"),
        row(PNUM="straddle", APPLIED="2015-11-01", ISSUED="2016-01-05"),
        row(PNUM="pending", APPLIED="2026-09-01", ISSUED=None),
        row(PNUM="stale_pending", APPLIED="2015-09-01", ISSUED=None),
    ])
    assert sorted(out["permit_number"]) == ["pending", "straddle"]


def test_keys_are_source_qualified_and_duplicates_dropped(spec):
    out = norm(spec, [row(PNUM="B1"), row(PNUM="B1", ADDR="2 Main St")])
    assert len(out) == 1
    other = replace(spec, source_id="test.county")
    assert norm(other, [row(PNUM="B1")])["permit_key"][0] != out["permit_key"][0]


def test_dedupe_prefers_the_issued_row_regardless_of_fetch_order(spec):
    rows = [row(PNUM="B1", ISSUED=None, APPLIED="2020-01-02", VALUE="1"),
            row(PNUM="B1", ISSUED="2020-03-01", VALUE="999")]
    for ordered in (rows, rows[::-1]):
        out = norm(spec, ordered)
        assert len(out) == 1
        assert out["issue_date"][0] == date(2020, 3, 1) and out["valuation"][0] == 999


def test_digit_strings_are_dates_not_epoch_millis(spec):
    out = norm(spec, [row(PNUM="ymd", ISSUED="20240115")])
    assert out["issue_date"][0] == date(2024, 1, 15)


def test_kept_trade_like_types_are_flagged(spec, caplog):
    spec = replace(spec, include={}, exclude={"PTYPE": ("Mechanical",)})
    with caplog.at_level("WARNING"):
        norm(spec, [row(PNUM="a"), row(PNUM="b", PTYPE="Fire Alarm")])
    assert any("Fire Alarm" in r.getMessage() and "test.city" in r.getMessage()
               for r in caplog.records)


def test_jurisdiction_from_field_with_fallback(spec):
    spec = replace(spec, jurisdiction_field="CITY")
    out = norm(spec, [row(PNUM="a", CITY="Medina "), row(PNUM="b", CITY=None)])
    by = out.set_index("permit_number")
    assert by.loc["a", "jurisdiction"] == "Medina"
    assert by.loc["b", "jurisdiction"] == "Test City"


def test_jurisdiction_labels_relabel_published_values(spec):
    spec = replace(spec, jurisdiction_field="CITY",
                   jurisdiction_labels={"Thurston County": "Unincorporated Thurston County"})
    out = norm(spec, [row(PNUM="a", CITY="Thurston County"), row(PNUM="b", CITY="City of Lacey")])
    assert set(out["jurisdiction"]) == {"Unincorporated Thurston County", "City of Lacey"}


def test_source_context_columns(spec):
    out = norm(spec, [row()]).iloc[0]
    assert out["source_id"] == "test.city"
    assert out["county_fips"] == "53053"
    assert out["county"] == "Pierce"
    assert out["coverage"] == "City"
    assert out["valuation_basis"] == "Declared valuation"
    assert out["valuation"] == 250000.0
    assert out["housing_units"] == 1


def test_no_valuation_basis_means_no_valuation(spec):
    spec = replace(spec, valuation_basis=None)
    out = norm(spec, [row()]).iloc[0]
    assert pd.isna(out["valuation"])
    assert pd.isna(out["valuation_basis"])


def test_unmapped_optional_fields_are_null(spec):
    fields = {k: v for k, v in spec.fields.items() if k not in {"status", "housing_units", "applied_date"}}
    spec = replace(spec, fields=fields)
    out = norm(spec, [row()]).iloc[0]
    assert pd.isna(out["status"]) and pd.isna(out["housing_units"]) and pd.isna(out["applied_date"])


def test_out_of_region_coordinates_are_nulled(spec):
    out = norm(spec, [row(PNUM="ok"), row(PNUM="null_island", _lat=0.0, _lon=0.0)])
    by = out.set_index("permit_number")
    assert by.loc["ok", "latitude"] == 47.25
    assert pd.isna(by.loc["null_island", "latitude"]) and pd.isna(by.loc["null_island", "longitude"])


def test_nothing_left_after_filtering_raises(spec):
    with pytest.raises(ValueError, match="test.city"):
        norm(spec, [row(PTYPE="Mechanical")])


def test_spec_rejects_unknown_platform_and_missing_required_fields(spec):
    with pytest.raises(ValueError, match="platform"):
        replace(spec, platform="ftp")
    with pytest.raises(ValueError, match="issue_date"):
        replace(spec, fields={"permit_number": "P", "permit_class": "T"})


def test_out_fields_cover_only_what_is_used(spec):
    spec = replace(spec, jurisdiction_field="CITY",
                           exclude={"SUB": ("X",)})
    assert set(spec.out_fields) == {"PNUM", "PTYPE", "STATUS", "APPLIED", "ISSUED",
                                    "VALUE", "UNITS", "ADDR", "CITY", "SUB"}


def test_configured_permit_sources_are_valid():
    import city_config as cfg

    ids = [s.source_id for s in cfg.PERMIT_SOURCES]
    assert len(ids) == len(set(ids)) == 9
    assert {s.county_fips for s in cfg.PERMIT_SOURCES} <= set(cfg.REGION_COUNTIES)
    seattle = next(s for s in cfg.PERMIT_SOURCES if s.source_id == "seattle.permits")
    assert seattle.county_fips == "53033"
    trpc = next(s for s in cfg.PERMIT_SOURCES if s.source_id == "trpc.permits")
    assert trpc.valuation_basis is None
    # Trade-only permit types never pass a structure-permit rule.
    for s in cfg.PERMIT_SOURCES:
        for values in s.include.values():
            assert not any("MECH" in v.upper() or "PLUMB" in v.upper() for v in values), s.source_id


# --------------------------------------------------------------------------- #
# Fetch adapters — request only used columns; geometry -> _lat/_lon            #
# --------------------------------------------------------------------------- #
def test_arcgis_fetch_requests_out_fields_and_maps_geometry(spec, monkeypatch):
    import build_warehouse

    calls = {}

    def fake(base_url, where="1=1", out_fields="*", geometry=True, out_sr=4326, ssl_verify=True):
        calls.update(base_url=base_url, where=where, out_fields=out_fields, out_sr=out_sr)
        return [({"PNUM": "B1", "PTYPE": "New Building"}, {"x": -122.44, "y": 47.25}),
                ({"PNUM": "B2", "PTYPE": "Demolition"}, None)]

    monkeypatch.setattr(build_warehouse, "fetch_features", fake)
    df = build_warehouse.fetch_permit_source(spec)
    assert calls["out_fields"].split(",") == list(spec.out_fields)
    assert calls["where"] == spec.server_where and calls["out_sr"] == 4326
    assert df["_lat"][0] == 47.25 and df["_lon"][0] == -122.44
    assert pd.isna(df["_lat"][1])


def test_socrata_fetch_selects_out_fields_and_unpacks_point(spec, monkeypatch):
    import build_warehouse

    spec = replace(spec, platform="socrata",
                           endpoint="data.example.gov/abcd-1234", point_field="geom")
    calls = {}

    def fake(domain, dataset_id, where=None, select=None, **kw):
        calls.update(domain=domain, dataset_id=dataset_id, where=where, select=select)
        return pd.DataFrame([
            {"PNUM": "B1", "geom": {"type": "Point", "coordinates": [-122.2, 47.9]}},
            {"PNUM": "B2", "geom": None},
        ])

    monkeypatch.setattr(build_warehouse, "fetch_socrata", fake)
    df = build_warehouse.fetch_permit_source(spec)
    assert (calls["domain"], calls["dataset_id"]) == ("data.example.gov", "abcd-1234")
    assert calls["select"].split(",") == list(spec.out_fields)
    assert calls["where"] == spec.server_where
    assert df["_lat"][0] == 47.9 and df["_lon"][0] == -122.2
    assert pd.isna(df["_lat"][1])
    assert "geom" not in df.columns


# --------------------------------------------------------------------------- #
# Page queries — county selection filters before aggregating; valuation stays  #
# per publisher; a county with no publisher is empty, never Seattle.           #
# --------------------------------------------------------------------------- #
def run(con, name, county=None):
    from regional_permits import permits_queries

    sql, params = permits_queries(county)[name]
    return con.execute(sql, params).df()


def test_kpis_region_and_county(permits_database):
    region = run(permits_database, "kpis").iloc[0]
    assert region["permits"] == 344
    assert region["publishers"] == 5 and region["jurisdictions"] == 6
    king = run(permits_database, "kpis", "53033").iloc[0]
    assert king["permits"] == 242 and king["publishers"] == 2


def test_monthly_series_is_county_for_region_and_jurisdiction_for_a_county(permits_database):
    region = run(permits_database, "monthly")
    jan = region[region["issue_month"] == pd.Timestamp("2023-01-01")].set_index("series")
    assert jan.loc["King", "permits"] == 132
    king = run(permits_database, "monthly", "53033")
    assert set(king["series"]) == {"Seattle", "Bellevue", "Medina"}


def test_annual_by_jurisdiction(permits_database):
    pierce = run(permits_database, "annual", "53053")
    assert set(zip(pierce["jurisdiction"], pierce["year"])) == {
        ("Unincorporated Pierce County", 2023), ("Tacoma", 2024)}


def test_valuation_is_one_series_per_publisher_never_summed(permits_database):
    val = run(permits_database, "valuation_monthly")
    assert "trpc.permits" not in set(val["source_id"])  # no valuation published
    jan_bellevue = val[(val["source_id"] == "bellevue.permits")
                       & (val["issue_month"] == pd.Timestamp("2023-01-01"))]
    assert len(jan_bellevue) == 1 and jan_bellevue["total_valuation"].iloc[0] == 13e6
    assert val.groupby(["issue_month", "source_id"]).size().max() == 1


def test_publishers_table_discloses_coverage_scope_and_basis(permits_database):
    pubs = run(permits_database, "publishers").set_index("jurisdiction")
    assert pubs.loc["Olympia", "scope"].startswith("Residential")
    assert pd.isna(pubs.loc["Olympia", "valuation_basis"])
    assert pubs.loc["Medina", "publisher_source"] == "bellevue.permits"
    assert pubs.loc["Seattle", "first_month"] == pd.Timestamp("2023-01-01")
    assert pubs.loc["Seattle", "last_month"] == pd.Timestamp("2023-02-01")


def test_by_class_and_map_filter_by_county(permits_database):
    assert set(run(permits_database, "by_class", "53053")["jurisdiction"]) == {
        "Unincorporated Pierce County"}
    assert list(run(permits_database, "map", "53053")["permit_number"]) == ["T1"]
    assert len(run(permits_database, "map")) == 2


def test_county_without_publisher_is_empty_everywhere(permits_database):
    from regional_permits import permits_queries

    for name in permits_queries("53029"):  # Island — no integrated publisher
        df = run(permits_database, name, "53029")
        if name == "kpis":
            assert df.iloc[0]["permits"] is None or pd.isna(df.iloc[0]["permits"])
        else:
            assert df.empty, name


def test_selection_is_parameterized():
    from regional_permits import permits_queries

    for sql, params in permits_queries("53033'; drop table x; --").values():
        assert "drop table" not in sql
        assert params == ("53033'; drop table x; --",)

"""TDD for the regional Weather & Water query builders (PS-TOPICS-02).

Charts read each county's headline station; maps/coverage read every station;
a county with no station in a network resolves to empty (a real gap), never to
Seattle. Selections are parameterized (no SQL injection).
"""

from __future__ import annotations

from regional_water import water_queries
from regional_weather import weather_queries


def run(con, queries, name, county=None):
    sql, params = queries(county)[name]
    return con.execute(sql, params).df()


# --------------------------------------------------------------------------- #
# Weather                                                                      #
# --------------------------------------------------------------------------- #
def test_weather_records_use_headline_not_secondary(weather_database):
    # King's hottest headline day is 85 °F, NOT the 99 °F secondary station.
    records = run(weather_database, weather_queries, "records", "53033")
    hottest = records[records["record_type"] == "Hottest day"].iloc[0]
    assert hottest["value"] == "85 °F"


def test_weather_monthly_normals_one_series_per_selected_county(weather_database):
    normals = run(weather_database, weather_queries, "monthly_normals", "53033")
    assert set(normals["county"]) == {"King"}
    assert set(normals["month_num"]) == {1, 7}


def test_weather_stations_map_includes_non_headline(weather_database):
    # The map shows every station; King has 2 (headline + secondary).
    king = run(weather_database, weather_queries, "stations", "53033")
    assert len(king) == 2
    region = run(weather_database, weather_queries, "stations")
    assert len(region) == 3


def test_weather_coverage_reports_headline_per_county(weather_database):
    cov = run(weather_database, weather_queries, "coverage")
    assert set(cov["county"]) == {"King", "Kitsap"}
    king = cov[cov["county"] == "King"].iloc[0]
    assert king["headline_station"] == "SEATTLE TACOMA AP"
    assert king["station_count"] == 2


def test_weather_missing_county_is_empty(weather_database):
    for name in weather_queries("53029"):  # Island — no station
        assert run(weather_database, weather_queries, name, "53029").empty


# --------------------------------------------------------------------------- #
# Water — per-county network gaps are real                                     #
# --------------------------------------------------------------------------- #
def test_water_river_headline_gage_only(water_database):
    annual = run(water_database, water_queries, "river_annual", "53033")
    assert set(annual["station_name"]) == {"CEDAR RIVER"}  # not the secondary gage


def test_water_river_stations_map_includes_all_gages(water_database):
    king = run(water_database, water_queries, "river_stations", "53033")
    assert len(king) == 2


def test_water_kitsap_has_tide_but_no_river_or_snow(water_database):
    # Kitsap: a tide gauge but no river gage and no snow station — honest gaps.
    assert not run(water_database, water_queries, "tides_annual", "53035").empty
    assert run(water_database, water_queries, "river_annual", "53035").empty
    assert run(water_database, water_queries, "snow_annual_peak", "53035").empty


def test_water_coverage_spans_three_networks(water_database):
    cov = run(water_database, water_queries, "coverage")
    assert set(cov["network"]) == {"River", "Tide", "Snow"}
    # King appears in all three; Kitsap only in Tide.
    kitsap = cov[cov["county"] == "Kitsap"]
    assert set(kitsap["network"]) == {"Tide"}


def test_water_snow_peak_per_water_year(water_database):
    peak = run(water_database, water_queries, "snow_annual_peak", "53033")
    wy2023 = peak[peak["water_year"] == 2023].iloc[0]
    assert wy2023["peak_swe_in"] == 40  # max of 40/30


def test_water_snow_peak_skips_only_the_newest_unfinished_water_year(water_database):
    # WY2024 is the newest year and holds only an October day: charting its
    # "peak" reads as a record drought, so it is skipped. WY2022 also ends before
    # April 1 (a past sensor gap), but it is not the newest year, so it charts.
    peak = run(water_database, water_queries, "snow_annual_peak", "53033")
    assert list(peak["water_year"]) == [2022, 2023]


def test_water_snow_recent_keeps_the_winter_in_progress(water_database):
    # The daily trace is not a peak, so the in-progress winter stays visible.
    recent = run(water_database, water_queries, "snow_recent", "53033")
    assert set(recent["water_year"]) == {2022, 2023, 2024}


# --------------------------------------------------------------------------- #
# Injection safety                                                             #
# --------------------------------------------------------------------------- #
def test_selection_is_parameterized():
    for builder in (weather_queries, water_queries):
        for sql, params in builder("x' OR 1=1 --").values():
            assert "x' OR" not in sql
            assert set(params) == {"x' OR 1=1 --"}

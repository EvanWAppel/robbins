"""Shared pytest fixtures (keep tests DRY)."""

from __future__ import annotations

from collections.abc import Callable

import pytest


@pytest.fixture
def fake_soda_pages() -> Callable[[list[list[dict]]], Callable]:
    """Build a fake ``_soda_get`` that serves pre-canned pages by ``$offset``.

    Usage::

        get = fake_soda_pages([page1_rows, page2_rows, ...])
        monkeypatch.setattr(build_warehouse, "_soda_get", get)

    The returned callable mimics the real ``_soda_get(url, params, app_token)``
    signature and returns the page whose index matches ``$offset / $limit``.
    Requesting an offset past the last page yields ``[]`` (as Socrata does).
    """

    def _factory(pages: list[list[dict]]) -> Callable:
        def _get(url: str, params: dict, app_token: str | None) -> list[dict]:
            limit = params["$limit"]
            offset = params["$offset"]
            idx = offset // limit
            return pages[idx] if idx < len(pages) else []

        return _get

    return _factory


@pytest.fixture
def source_registration():
    """Synthetic source metadata for regional registry validation."""
    return {
        "source_id": "test.permits",
        "topic": "Building Permits",
        "publisher": "Example City",
        "url": "https://example.org/permits",
        "geography_kind": "municipality",
        "coverage": "Example City only",
        "record_grain": "One permit",
        "limitations": "Does not cover the rest of the county.",
    }


@pytest.fixture
def air_database():
    """Synthetic monitor observations spanning counties, days, and pollutants."""
    import duckdb

    con = duckdb.connect()
    con.execute('''create table mart_air_observations (
        county varchar, county_fips varchar, site_id varchar, site varchar,
        latitude double, longitude double, obs_date date, pollutant varchar,
        aqi double, aqi_category varchar)''')
    con.execute('''insert into mart_air_observations values
        ('King', '53033', '530330001', 'Same name', 47.6, -122.3, '2024-01-01', 'PM2.5', 40, 'Good'),
        ('Kitsap', '53035', '530350001', 'Same name', 47.5, -122.6, '2024-01-01', 'PM2.5', 160, 'Unhealthy'),
        ('King', '53033', '530330001', 'Same name', 47.6, -122.3, '2024-01-02', 'PM2.5', 60, 'Moderate'),
        ('Kitsap', '53035', '530350001', 'Same name', 47.5, -122.6, '2024-01-02', 'Ozone', 20, 'Good')''')
    yield con
    con.close()


@pytest.fixture
def weather_database():
    """Synthetic regional weather: two counties, a non-headline station in King."""
    import duckdb

    con = duckdb.connect()
    con.execute('''create table mart_weather_observations (
        obs_date date, station_id varchar, station_name varchar, county varchar,
        county_fips varchar, latitude double, longitude double, is_headline boolean,
        precip_in double, tmax_f double, tmin_f double, snow_in double, snow_depth_in double)''')
    con.execute('''insert into mart_weather_observations values
        ('2023-07-15','USW00024233','SEATTLE TACOMA AP','King','53033',47.44,-122.31,true, 0.0,85,60, 0, 0),
        ('2023-01-10','USW00024233','SEATTLE TACOMA AP','King','53033',47.44,-122.31,true, 0.5,45,35, 0, 0),
        ('2024-01-10','USW00024233','SEATTLE TACOMA AP','King','53033',47.44,-122.31,true, 1.0,40,30, 2.0, 3.0),
        ('2023-07-15','USW00099999','KING SECONDARY','King','53033',47.60,-122.20,false, 0.0,99,62, 0, 0),
        ('2023-07-15','USW00094248','BREMERTON','Kitsap','53035',47.56,-122.62,true, 0.0,80,58, 0, 0),
        ('2024-01-10','USW00094248','BREMERTON','Kitsap','53035',47.56,-122.62,true, 0.8,42,33, 0, 0)''')
    yield con
    con.close()


@pytest.fixture
def water_database():
    """Synthetic regional water: King has all three networks; Kitsap only tides."""
    import duckdb

    con = duckdb.connect()
    con.execute('''create table mart_river_observations (
        obs_date date, site_no varchar, station_name varchar, county varchar,
        county_fips varchar, latitude double, longitude double, is_headline boolean,
        discharge_cfs double)''')
    con.execute('''insert into mart_river_observations values
        ('2023-01-10','12119000','CEDAR RIVER','King','53033',47.48,-122.20,true, 500),
        ('2023-07-15','12119000','CEDAR RIVER','King','53033',47.48,-122.20,true, 120),
        ('2023-01-10','12113000','GREEN RIVER','King','53033',47.31,-122.20,false, 900)''')
    con.execute('''create table mart_tides_observations (
        obs_month date, year integer, month integer, station_id varchar, station_name varchar,
        county varchar, county_fips varchar, latitude double, longitude double,
        is_headline boolean, msl_ft double, mhhw_ft double, mllw_ft double,
        range_ft double, highest_ft double, lowest_ft double)''')
    con.execute('''insert into mart_tides_observations values
        ('2023-01-01',2023,1,'9447130','Seattle','King','53033',47.60,-122.34,true, 7.0,11.4,-0.2,11.6,12.0,-1.0),
        ('2023-01-01',2023,1,'9445958','Bremerton','Kitsap','53035',47.56,-122.62,true, 6.9,11.2,-0.1,11.3,11.9,-0.9)''')
    con.execute('''create table mart_snow_observations (
        obs_date date, water_year integer, station_triplet varchar, station_name varchar,
        county varchar, county_fips varchar, latitude double, longitude double,
        is_headline boolean, swe_in double, snow_depth_in double)''')
    con.execute('''insert into mart_snow_observations values
        -- WY2022's data stops in February (sensor gap): a past winter still charts.
        ('2022-02-01',2022,'791:WA:SNTL','Stampede Pass','King','53033',47.28,-121.34,true, 25, 60),
        ('2023-03-01',2023,'791:WA:SNTL','Stampede Pass','King','53033',47.28,-121.34,true, 40, 90),
        ('2023-04-01',2023,'791:WA:SNTL','Stampede Pass','King','53033',47.28,-121.34,true, 30, 70),
        -- WY2024 has only just begun (no data through April 1): not a full winter.
        ('2023-10-05',2024,'791:WA:SNTL','Stampede Pass','King','53033',47.28,-121.34,true, 0.2, 1)''')
    yield con
    con.close()


@pytest.fixture
def ntd_database():
    """Distinct ferry operators and service types for regional aggregation tests."""
    import duckdb

    con = duckdb.connect()
    con.execute('''create table stg_ntd_ridership (
        agency varchar, agency_label varchar, is_ferry boolean,
        ridership_month date, upt bigint)''')
    con.execute('''insert into stg_ntd_ridership values
        ('Washington State Ferries', 'Washington State Ferries', true, '2024-01-01', 10),
        ('King County', 'King County Metro', true, '2024-01-01', 3),
        ('King County Ferry District', 'King County Water Taxi', true, '2015-01-01', 4),
        ('Kitsap County Public Transportation Benefit Area Authority', 'Kitsap Transit', true, '2024-01-01', 20),
        ('County of Pierce', 'Pierce County Ferry', true, '2024-01-01', 5),
        ('King County', 'King County Metro', false, '2024-01-01', 100)''')
    yield con
    con.close()

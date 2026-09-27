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

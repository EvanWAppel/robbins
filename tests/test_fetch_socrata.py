"""TDD for the Socrata (SODA API) fetch helper — the one net-new piece vs. Elvis."""

from __future__ import annotations

import pandas as pd
import pytest

import build_warehouse as bw


# --------------------------------------------------------------------------- #
# URL builders                                                                 #
# --------------------------------------------------------------------------- #
def test_socrata_resource_url():
    assert (
        bw.socrata_resource_url("data.seattle.gov", "76t5-zqzr")
        == "https://data.seattle.gov/resource/76t5-zqzr.json"
    )


def test_socrata_csv_url():
    assert (
        bw.socrata_csv_url("data.seattle.gov", "76t5-zqzr")
        == "https://data.seattle.gov/api/views/76t5-zqzr/rows.csv?accessType=DOWNLOAD"
    )


def test_socrata_resource_csv_url_plain():
    # No filters: the .csv resource endpoint with just a $limit.
    url = bw.socrata_resource_csv_url("data.seattle.gov", "tazs-3rd5", limit=5)
    assert url == "https://data.seattle.gov/resource/tazs-3rd5.csv?%24limit=5"


def test_socrata_resource_csv_url_encodes_where():
    # $where must be URL-encoded (spaces, quotes, >=) so DuckDB/httpfs can read it.
    url = bw.socrata_resource_csv_url(
        "data.seattle.gov", "tazs-3rd5",
        where="report_date_time >= '2019-01-01'", limit=2_000_000,
    )
    assert url.startswith("https://data.seattle.gov/resource/tazs-3rd5.csv?")
    assert "%24where=" in url            # $where encoded
    assert "%3E%3D" in url               # ">=" encoded
    assert "2019-01-01" in url
    assert "%24limit=2000000" in url


# --------------------------------------------------------------------------- #
# Paging                                                                       #
# --------------------------------------------------------------------------- #
def test_fetch_socrata_single_short_page(monkeypatch, fake_soda_pages):
    rows = [{"permitnum": "1"}, {"permitnum": "2"}]
    monkeypatch.setattr(bw, "_soda_get", fake_soda_pages([rows]))

    df = bw.fetch_socrata("data.seattle.gov", "abcd-1234", page_size=1000)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df["permitnum"]) == ["1", "2"]


def test_fetch_socrata_pages_until_short_page(monkeypatch, fake_soda_pages):
    # Two full pages of 2, then a final short page of 1 → 5 rows total, 3 requests.
    page1 = [{"n": 1}, {"n": 2}]
    page2 = [{"n": 3}, {"n": 4}]
    page3 = [{"n": 5}]
    monkeypatch.setattr(bw, "_soda_get", fake_soda_pages([page1, page2, page3]))

    df = bw.fetch_socrata("d", "id", page_size=2)

    assert list(df["n"]) == [1, 2, 3, 4, 5]


def test_fetch_socrata_exact_multiple_stops_on_empty(monkeypatch, fake_soda_pages):
    # A full final page (len == page_size) forces one more request that returns [].
    page1 = [{"n": 1}, {"n": 2}]
    monkeypatch.setattr(bw, "_soda_get", fake_soda_pages([page1]))  # offset 2 -> []

    df = bw.fetch_socrata("d", "id", page_size=2)

    assert list(df["n"]) == [1, 2]


# --------------------------------------------------------------------------- #
# Zero-row guard (a fetch that returns nothing must raise, not ship empty)     #
# --------------------------------------------------------------------------- #
def test_fetch_socrata_zero_rows_raises(monkeypatch, fake_soda_pages):
    monkeypatch.setattr(bw, "_soda_get", fake_soda_pages([[]]))

    with pytest.raises(ValueError, match="zero rows"):
        bw.fetch_socrata("d", "id", page_size=1000)


# --------------------------------------------------------------------------- #
# SODA query params + app token                                                #
# --------------------------------------------------------------------------- #
def test_fetch_socrata_forwards_query_params(monkeypatch):
    captured = {}

    def spy(url, params, app_token):
        captured.update(params)
        return []  # empty -> raises, but we only care about the params captured

    monkeypatch.setattr(bw, "_soda_get", spy)
    with pytest.raises(ValueError):
        bw.fetch_socrata(
            "d", "id", where="issueddate > '2020-01-01'", select="permitnum",
            order="issueddate", page_size=5000,
        )

    assert captured["$where"] == "issueddate > '2020-01-01'"
    assert captured["$select"] == "permitnum"
    assert captured["$order"] == "issueddate"
    assert captured["$limit"] == 5000
    assert captured["$offset"] == 0


def test_fetch_socrata_defaults_order_to_id_for_stable_paging(monkeypatch):
    captured = {}

    def spy(url, params, app_token):
        captured.update(params)
        return []

    monkeypatch.setattr(bw, "_soda_get", spy)
    with pytest.raises(ValueError):
        bw.fetch_socrata("d", "id")

    # Socrata paging is only stable with an explicit $order; default to :id.
    assert captured["$order"] == ":id"


def test_ingest_csv_loads_rows(tmp_path):
    import duckdb

    csv = tmp_path / "x.csv"
    csv.write_text("a,b\n1,foo\n2,bar\n")
    con = duckdb.connect()
    bw.ingest_csv(con, "sample", str(csv))
    rows = con.execute("select * from raw.sample order by a").fetchall()
    assert rows == [("1", "foo"), ("2", "bar")]  # all_varchar: staging casts later


def test_ingest_csv_zero_rows_raises(tmp_path):
    import duckdb

    csv = tmp_path / "empty.csv"
    csv.write_text("a,b\n")  # header only, no data rows
    con = duckdb.connect()
    with pytest.raises(ValueError, match="zero rows"):
        bw.ingest_csv(con, "empty", str(csv))


# --------------------------------------------------------------------------- #
# ArcGIS geometry transforms (pure)                                            #
# --------------------------------------------------------------------------- #
def test_centroid_point():
    assert bw._centroid({"x": -122.33, "y": 47.6}) == (-122.33, 47.6)


def test_centroid_polygon_ring_averages_vertices():
    # A unit square ring (closed: first == last) → centroid at (0.5, 0.5).
    ring = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
    lon, lat = bw._centroid({"rings": [ring]})
    assert lon == 0.5
    assert lat == 0.5


def test_centroid_none_returns_nones():
    assert bw._centroid(None) == (None, None)
    assert bw._centroid({}) == (None, None)


def test_epoch_to_date_converts_millis():
    # 2020-01-01T00:00:00Z in epoch millis.
    assert bw._epoch_to_date(1_577_836_800_000) == "2020-01-01"


def test_epoch_to_date_none_and_sentinel():
    assert bw._epoch_to_date(None) is None
    # Pre-1990 sentinel (ArcGIS "no date") → None.
    assert bw._epoch_to_date(0) is None


def test_soda_get_sends_app_token_header(monkeypatch):
    captured = {}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return []

    def fake_get(url, params=None, headers=None, timeout=None):
        captured["headers"] = headers or {}
        return FakeResp()

    monkeypatch.setattr(bw.requests, "get", fake_get)

    bw._soda_get("http://x", {"$limit": 1, "$offset": 0}, app_token="Tok123")
    assert captured["headers"].get("X-App-Token") == "Tok123"

    bw._soda_get("http://x", {"$limit": 1, "$offset": 0}, app_token=None)
    assert "X-App-Token" not in captured["headers"]

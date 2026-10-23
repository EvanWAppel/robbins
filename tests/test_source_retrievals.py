"""Source retrieval timestamps: raw.source_retrievals -> staging -> mart -> page."""

from datetime import datetime
from pathlib import Path

import pandas as pd

import app_db
import build_warehouse

ROOT = Path(__file__).resolve().parents[1]


def _retrievals(con) -> pd.DataFrame:
    return con.execute(
        "select source_id, retrieved_at, row_count from raw.source_retrievals order by source_id"
    ).df()


def test_load_raw_records_retrieval(raw_warehouse):
    build_warehouse.load_raw(raw_warehouse, "parks", pd.DataFrame({"name": ["A", "B", "C"]}))
    rows = _retrievals(raw_warehouse)
    assert rows.source_id.tolist() == ["parks"]
    assert rows.row_count.tolist() == [3]
    assert pd.notna(rows.retrieved_at.iloc[0])


def test_reloading_a_source_replaces_its_retrieval(raw_warehouse):
    build_warehouse.load_raw(raw_warehouse, "parks", pd.DataFrame({"name": ["A"]}))
    build_warehouse.load_raw(raw_warehouse, "trees", pd.DataFrame({"id": [1, 2]}))
    build_warehouse.load_raw(raw_warehouse, "parks", pd.DataFrame({"name": ["A", "B"]}))
    rows = _retrievals(raw_warehouse)
    assert rows.source_id.tolist() == ["parks", "trees"]
    assert rows.row_count.tolist() == [2, 2]


def test_retrieved_at_is_the_load_time_in_utc(raw_warehouse):
    before = datetime.now(build_warehouse.UTC).replace(tzinfo=None)
    build_warehouse.load_raw(raw_warehouse, "parks", pd.DataFrame({"name": ["A"]}))
    after = datetime.now(build_warehouse.UTC).replace(tzinfo=None)
    stamp = _retrievals(raw_warehouse).retrieved_at.iloc[0].to_pydatetime()
    assert before <= stamp <= after


def test_ingest_csv_records_retrieval(raw_warehouse, tmp_path):
    csv = tmp_path / "crime.csv"
    csv.write_text("id,offense\n1,theft\n2,burglary\n")
    build_warehouse.ingest_csv(raw_warehouse, "crime", str(csv))
    rows = _retrievals(raw_warehouse)
    assert rows.source_id.tolist() == ["crime"]
    assert rows.row_count.tolist() == [2]


def _render(path: str, refs: dict[str, str]) -> str:
    sql = (ROOT / path).read_text()
    sql = sql.replace("{{ config(materialized='table') }}", "")
    for jinja, table in refs.items():
        sql = sql.replace(jinja, table)
    return sql


def test_staging_and_mart_carry_one_row_per_source(raw_warehouse):
    raw_warehouse.execute("create schema raw")
    raw_warehouse.execute(
        "create table raw.source_retrievals (source_id varchar, retrieved_at timestamp, row_count bigint)"
    )
    raw_warehouse.execute("""insert into raw.source_retrievals values
        ('crime', '2026-10-20 08:00:00', 10),
        ('parks', '2026-10-20 09:00:00', 5)""")
    stg = _render("models/staging/stg_source_retrievals.sql",
                  {"{{ source('raw', 'source_retrievals') }}": "raw.source_retrievals"})
    raw_warehouse.execute(f"create view stg_source_retrievals as {stg}")
    mart = _render("models/marts/mart_source_retrievals.sql",
                   {"{{ ref('stg_source_retrievals') }}": "stg_source_retrievals"})
    rows = raw_warehouse.execute(mart + " order by source_id").df()
    assert rows.columns.tolist() == ["source_id", "retrieved_at", "row_count"]
    assert rows.source_id.tolist() == ["crime", "parks"]
    assert rows.row_count.tolist() == [10, 5]
    assert str(rows.retrieved_at.iloc[1]) == "2026-10-20 09:00:00"


def test_data_coverage_page_shows_retrieval_times(app_test, monkeypatch, coverage_database):
    monkeypatch.setattr(
        app_db, "query",
        lambda sql, params=(): coverage_database.cursor().execute(sql, params).df(),
    )
    app = app_test("views/data_coverage.py").run()
    assert not app.exception
    assert any(h.value == "Source retrievals" for h in app.subheader)
    frames = [df.value for df in app.dataframe]
    retrievals = next(f for f in frames if "retrieved_at" in f.columns)
    assert set(retrievals.source_id) == {"building_permits", "air_quality"}
    assert not any("not yet tracked" in c.value for c in app.caption)

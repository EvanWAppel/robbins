"""PS-SCOPE-02 measurement harness: mart query latency + warehouse size."""

import json

import duckdb
import pytest

import app_db
import benchmark


def test_list_marts_finds_only_mart_tables(synthetic_warehouse):
    con = duckdb.connect(str(synthetic_warehouse), read_only=True)
    assert benchmark.list_marts(con) == ["mart_alpha", "mart_beta"]


def test_run_benchmark_times_every_mart_and_sizes_the_file(synthetic_warehouse):
    report = benchmark.run_benchmark(synthetic_warehouse, repeats=2)

    assert report.size_bytes == synthetic_warehouse.stat().st_size
    assert report.size_bytes > 0
    assert [m.mart for m in report.marts] == ["mart_alpha", "mart_beta"]
    assert [m.rows for m in report.marts] == [10, 1]
    for m in report.marts:
        assert m.repeats == 2
        assert 0 <= m.min_ms <= m.median_ms <= m.max_ms


def test_repeats_must_be_positive(synthetic_warehouse):
    with pytest.raises(ValueError, match="repeats"):
        benchmark.run_benchmark(synthetic_warehouse, repeats=0)


def test_missing_warehouse_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        benchmark.run_benchmark(tmp_path / "nope.duckdb")


def test_warehouse_without_marts_raises(tmp_path):
    path = tmp_path / "empty.duckdb"
    duckdb.connect(str(path)).close()
    with pytest.raises(ValueError, match="no mart"):
        benchmark.run_benchmark(path)


def test_default_db_is_the_app_warehouse():
    assert benchmark.DEFAULT_DB == app_db.DB_PATH


def test_format_report_lists_marts_and_size(synthetic_warehouse):
    text = benchmark.format_report(
        benchmark.run_benchmark(synthetic_warehouse, repeats=1)
    )
    assert "mart_alpha" in text
    assert "mart_beta" in text
    assert "MB" in text


def test_main_writes_json(synthetic_warehouse, tmp_path, capsys):
    out = tmp_path / "bench.json"
    benchmark.main(
        ["--db", str(synthetic_warehouse), "--repeats", "1", "--json", str(out)]
    )
    data = json.loads(out.read_text())
    assert data["size_bytes"] == synthetic_warehouse.stat().st_size
    assert {m["mart"] for m in data["marts"]} == {"mart_alpha", "mart_beta"}
    assert "mart_alpha" in capsys.readouterr().out

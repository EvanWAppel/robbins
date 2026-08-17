"""TDD for the home-grown semantic layer.

``metrics.yml`` is the single definition; ``semantic.py`` loads it and compiles it
to the ``mart_metrics`` dbt model (one definition, many consumers). These tests
cover the pure load / render / compile functions — no database needed.
"""

from __future__ import annotations

import pytest
import yaml

import semantic

SAMPLE = {
    "metrics": [
        {
            "name": "total_permits",
            "label": "Permits",
            "description": "All permits.",
            "mart": "mart_permits_monthly",
            "expression": "sum(permit_count)",
            "unit": "count",
        },
        {
            "name": "good_air",
            "label": "Good air",
            "description": "Share that is good.",
            "mart": "mart_air_category_days",
            "expression": "sum(day_count) filter (where aqi_category = 'Good')",
            "unit": "percent",
        },
    ]
}


def _write(tmp_path, data) -> str:
    p = tmp_path / "metrics.yml"
    p.write_text(yaml.safe_dump(data))
    return str(p)


def test_load_metrics_returns_all(tmp_path):
    metrics = semantic.load_metrics(_write(tmp_path, SAMPLE))
    assert [m["name"] for m in metrics] == ["total_permits", "good_air"]


def test_load_metrics_raises_on_missing_key(tmp_path):
    bad = {"metrics": [{"name": "x", "label": "X"}]}  # missing mart/expression/…
    with pytest.raises(ValueError, match="missing"):
        semantic.load_metrics(_write(tmp_path, bad))


def test_load_metrics_raises_when_empty(tmp_path):
    with pytest.raises(ValueError):
        semantic.load_metrics(_write(tmp_path, {"metrics": []}))


def test_render_metric_row_has_ref_and_expression():
    row = semantic.render_metric_row(SAMPLE["metrics"][0])
    assert "{{ ref('mart_permits_monthly') }}" in row
    assert "'total_permits' as metric_name" in row
    assert "cast(sum(permit_count) as double)" in row


def test_render_escapes_single_quotes_in_metadata():
    # An apostrophe in a label must be doubled so the SQL literal stays valid;
    # the raw expression is trusted and injected verbatim.
    m = {**SAMPLE["metrics"][1], "label": "Seattle's air"}
    row = semantic.render_metric_row(m)
    assert "'Seattle''s air' as label" in row
    assert "aqi_category = 'Good'" in row  # expression untouched


def test_compile_unions_all_metrics():
    sql = semantic.compile_metrics_model(SAMPLE["metrics"])
    assert sql.count("union all") == 1
    assert "order by metric_name" in sql
    assert "config(materialized='table')" in sql
    for name in ("total_permits", "good_air"):
        assert f"'{name}' as metric_name" in sql


def test_compile_empty_raises():
    with pytest.raises(ValueError):
        semantic.compile_metrics_model([])


def test_committed_model_is_in_sync_with_registry():
    """The committed mart_metrics.sql must match what metrics.yml compiles to —
    editing metrics.yml without regenerating should fail here (and in CI)."""
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    expected = semantic.compile_metrics_model(semantic.load_metrics(root / "metrics.yml"))
    actual = (root / "models" / "marts" / "mart_metrics.sql").read_text()
    assert actual == expected, "Out of sync — run: uv run python generate_metrics_model.py"

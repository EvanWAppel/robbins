"""The semantic layer: compile ``metrics.yml`` into the ``mart_metrics`` dbt model.

A small, home-grown semantic layer over the marts. Metrics are declared once in
``metrics.yml`` (name, label, description, source mart, aggregate expression, unit);
``generate_metrics_model.py`` uses the functions here to compile them into
``models/marts/mart_metrics.sql``. That single definition then has many consumers:
dbt builds, tests, and documents the model, and the Streamlit Overview reads metric
values by name. Editing a metric means editing one line of YAML.

Everything here is pure (no database, no dbt) so it is straightforward to test.
"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

log = logging.getLogger(__name__)

REQUIRED_KEYS = ("name", "label", "description", "mart", "expression", "unit")

HEADER = (
    "-- GENERATED from metrics.yml by generate_metrics_model.py — do not edit by hand.\n"
    "-- The semantic layer: each metric is declared once in metrics.yml and compiled\n"
    "-- here, so dbt builds/tests/documents it and the app reads it by name.\n"
    "{{ config(materialized='table') }}\n"
)


def load_metrics(path: str | Path) -> list[dict]:
    """Load and validate the metric registry. Raises loudly on malformed input."""
    data = yaml.safe_load(Path(path).read_text()) or {}
    metrics = data.get("metrics")
    if not metrics:
        raise ValueError(f"No metrics defined in {path}")
    for metric in metrics:
        missing = [k for k in REQUIRED_KEYS if not metric.get(k)]
        if missing:
            raise ValueError(f"Metric {metric.get('name', '?')!r} missing keys: {missing}")
    log.info("Loaded %d metrics from %s", len(metrics), path)
    return metrics


def _sql_str(value: object) -> str:
    """A single-quoted SQL string literal with embedded quotes escaped."""
    return "'" + str(value).replace("'", "''") + "'"


def render_metric_row(metric: dict) -> str:
    """One ``select`` producing a single metric row (name, label, …, value)."""
    return (
        "select\n"
        f"    {_sql_str(metric['name'])} as metric_name,\n"
        f"    {_sql_str(metric['label'])} as label,\n"
        f"    {_sql_str(metric['description'])} as description,\n"
        f"    {_sql_str(metric['unit'])} as unit,\n"
        f"    (select cast({metric['expression']} as double) "
        f"from {{{{ ref('{metric['mart']}') }}}}) as value"
    )


def compile_metrics_model(metrics: list[dict]) -> str:
    """Compile the registry into the full ``mart_metrics`` dbt model SQL."""
    if not metrics:
        raise ValueError("Cannot compile an empty metric set")
    rows = "\nunion all\n".join(render_metric_row(m) for m in metrics)
    return f"{HEADER}\n{rows}\norder by metric_name\n"

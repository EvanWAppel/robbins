"""TDD for the machine-readable marts catalog (agent grounding context)."""

from __future__ import annotations

import json

import catalog

SCHEMA = """
version: 2
models:
  - name: mart_permits_monthly
    description: Permit issuance and valuation per month.
    columns:
      - name: issue_month
        description: Month permits were issued.
      - name: permit_count
        description: Permits issued that month.
  - name: mart_metrics
    description: The semantic layer — one row per headline metric.
    columns:
      - name: metric_name
        description: Stable metric key.
      - name: value
        description: The computed metric value.
"""


def _write(tmp_path, text) -> str:
    p = tmp_path / "schema.yml"
    p.write_text(text)
    return str(p)


def test_load_catalog_tables_and_columns(tmp_path):
    cat = catalog.load_catalog(_write(tmp_path, SCHEMA))
    tables = {t["name"]: t for t in cat["tables"]}
    assert set(tables) == {"mart_permits_monthly", "mart_metrics"}
    assert tables["mart_permits_monthly"]["description"].startswith("Permit issuance")
    cols = [c["name"] for c in tables["mart_permits_monthly"]["columns"]]
    assert cols == ["issue_month", "permit_count"]


def test_prompt_text_grounds_on_names_and_columns(tmp_path):
    cat = catalog.load_catalog(_write(tmp_path, SCHEMA))
    text = catalog.catalog_prompt_text(cat)
    assert "mart_permits_monthly" in text
    assert "permit_count" in text
    assert "Permit issuance and valuation per month." in text


def test_catalog_json_is_stable_and_sorted(tmp_path):
    cat = catalog.load_catalog(_write(tmp_path, SCHEMA))
    js = catalog.catalog_json(cat)
    parsed = json.loads(js)
    # tables sorted by name for a deterministic committed artifact
    assert [t["name"] for t in parsed["tables"]] == ["mart_metrics", "mart_permits_monthly"]
    assert catalog.catalog_json(cat) == js  # deterministic


def test_committed_catalog_is_in_sync_with_schema():
    """catalog/marts.json must match what schema.yml compiles to — edit the docs
    without regenerating and this fails (and CI fails)."""
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    expected = catalog.catalog_json(catalog.load_catalog(root / "models" / "marts" / "schema.yml"))
    actual = (root / "catalog" / "marts.json").read_text()
    assert actual == expected, "Out of sync — run: uv run python generate_catalog.py"

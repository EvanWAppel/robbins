"""A machine-readable catalog of the marts — context an AI agent can ground on.

Built from the committed ``models/marts/schema.yml`` (the same descriptions dbt
documents), so it never drifts from the modeled data. Two consumers:

* ``generate_catalog.py`` writes ``catalog/marts.json`` — a curated, agent-groundable
  artifact that sits next to dbt's ``manifest.json``.
* the Streamlit 'Ask the data' tab renders ``catalog_prompt_text()`` into the LLM
  prompt so generated SQL only references real tables and columns.

Pure functions, no database — easy to test.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml


def load_catalog(marts_schema_path: str | Path) -> dict:
    """Parse a marts ``schema.yml`` into ``{"tables": [{name, description, columns}]}``."""
    data = yaml.safe_load(Path(marts_schema_path).read_text()) or {}
    tables = []
    for model in data.get("models", []):
        tables.append(
            {
                "name": model["name"],
                "description": (model.get("description") or "").strip(),
                "columns": [
                    {"name": c["name"], "description": (c.get("description") or "").strip()}
                    for c in model.get("columns", [])
                ],
            }
        )
    return {"tables": tables}


def catalog_prompt_text(cat: dict) -> str:
    """A compact, LLM-friendly rendering used to ground generated SQL."""
    lines: list[str] = []
    for table in cat["tables"]:
        lines.append(f"TABLE main.{table['name']} — {table['description']}")
        for col in table["columns"]:
            lines.append(f"    {col['name']}: {col['description']}")
    return "\n".join(lines)


def catalog_json(cat: dict) -> str:
    """Deterministic JSON (tables sorted by name) for the committed artifact."""
    ordered = {"tables": sorted(cat["tables"], key=lambda t: t["name"])}
    return json.dumps(ordered, indent=2, ensure_ascii=False) + "\n"

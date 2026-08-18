"""Codegen: write ``catalog/marts.json`` from the marts ``schema.yml``.

The JSON is a curated, machine-readable catalog of the marts — framed as context an
AI agent can ground on (it sits alongside dbt's ``manifest.json``). Regenerate after
editing the marts docs:

    uv run python generate_catalog.py
"""

from __future__ import annotations

import logging
from pathlib import Path

from catalog import catalog_json, load_catalog

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent
MARTS_SCHEMA = ROOT / "models" / "marts" / "schema.yml"
OUTPUT = ROOT / "catalog" / "marts.json"


def main() -> None:
    cat = load_catalog(MARTS_SCHEMA)
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(catalog_json(cat))
    log.info("Wrote %s (%d tables)", OUTPUT.relative_to(ROOT), len(cat["tables"]))


if __name__ == "__main__":
    main()

"""Codegen: compile ``metrics.yml`` into the ``mart_metrics`` dbt model.

Run after editing ``metrics.yml`` so the generated model stays in sync:

    uv run python generate_metrics_model.py

The generated ``models/marts/mart_metrics.sql`` is committed (like dbt-codegen
output) so ``dbt build`` picks it up with no extra runtime step.
"""

from __future__ import annotations

import logging
from pathlib import Path

from semantic import compile_metrics_model, load_metrics

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

ROOT = Path(__file__).parent
METRICS_YML = ROOT / "metrics.yml"
OUTPUT = ROOT / "models" / "marts" / "mart_metrics.sql"


def main() -> None:
    metrics = load_metrics(METRICS_YML)
    OUTPUT.write_text(compile_metrics_model(metrics))
    log.info("Wrote %s (%d metrics)", OUTPUT.relative_to(ROOT), len(metrics))


if __name__ == "__main__":
    main()

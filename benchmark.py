"""PS-SCOPE-02 measurement harness: mart query latency and warehouse size.

Times a full read of every ``main.mart_*`` table the way the app reads it (the
``app_db.query`` path: a read-only DuckDB connection, a fresh cursor, ``.df()``)
and reports the warehouse file size. It measures only; it sets no budgets.
Numeric budgets are the owner's call (PS-SCOPE-02).

    uv run python benchmark.py                      # app warehouse (seattle.duckdb)
    uv run python benchmark.py --db other.duckdb --repeats 5 --json bench.json

The ``st.cache_data`` layer is deliberately bypassed: a cached read would time
the cache, not the warehouse.
"""

from __future__ import annotations

import argparse
import json
import logging
import statistics
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import duckdb

from app_db import DB_PATH

log = logging.getLogger(__name__)

DEFAULT_DB = DB_PATH
DEFAULT_REPEATS = 3


@dataclass(frozen=True)
class MartTiming:
    mart: str
    rows: int
    repeats: int
    min_ms: float
    median_ms: float
    max_ms: float


@dataclass(frozen=True)
class BenchmarkReport:
    db_path: str
    size_bytes: int
    marts: list[MartTiming]


def list_marts(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Names of the dbt mart tables (``main.mart_*``), sorted."""
    rows = con.execute(
        """
        select table_name from information_schema.tables
        where table_schema = 'main' and table_type = 'BASE TABLE'
          and table_name like 'mart\\_%' escape '\\'
        order by table_name
        """
    ).fetchall()
    return [r[0] for r in rows]


def time_mart(con: duckdb.DuckDBPyConnection, mart: str, repeats: int) -> MartTiming:
    """Time ``select * from main.<mart>`` into a DataFrame, ``repeats`` times."""
    sql = f'select * from main."{mart}"'
    samples: list[float] = []
    rows = 0
    for _ in range(repeats):
        start = time.perf_counter()
        rows = len(con.cursor().execute(sql).df())
        samples.append((time.perf_counter() - start) * 1000)
    timing = MartTiming(
        mart=mart,
        rows=rows,
        repeats=repeats,
        min_ms=min(samples),
        median_ms=statistics.median(samples),
        max_ms=max(samples),
    )
    log.debug("timed %s: %s", mart, timing)
    return timing


def run_benchmark(db_path: Path, repeats: int = DEFAULT_REPEATS) -> BenchmarkReport:
    """Measure every mart in the warehouse at ``db_path`` plus its file size."""
    if repeats < 1:
        raise ValueError(f"repeats must be >= 1, got {repeats}")
    db_path = Path(db_path)
    size_bytes = db_path.stat().st_size  # FileNotFoundError if the warehouse is absent
    con = duckdb.connect(str(db_path), read_only=True)
    try:
        marts = list_marts(con)
        if not marts:
            raise ValueError(f"no mart tables (main.mart_*) found in {db_path}")
        log.info(
            "benchmarking %d marts in %s (%d repeats)", len(marts), db_path, repeats
        )
        timings = [time_mart(con, m, repeats) for m in marts]
    finally:
        con.close()
    return BenchmarkReport(db_path=str(db_path), size_bytes=size_bytes, marts=timings)


def format_report(report: BenchmarkReport) -> str:
    """A plain-text table, slowest median first."""
    width = max(len(m.mart) for m in report.marts)
    lines = [
        f"warehouse: {report.db_path}",
        f"size: {report.size_bytes / 1_000_000:.2f} MB ({report.size_bytes:,} bytes)",
        "",
        f"{'mart':<{width}}  {'rows':>10}  {'min ms':>9}  {'median ms':>9}  {'max ms':>9}",
    ]
    for m in sorted(report.marts, key=lambda t: t.median_ms, reverse=True):
        lines.append(
            f"{m.mart:<{width}}  {m.rows:>10,}  {m.min_ms:>9.2f}  {m.median_ms:>9.2f}  {m.max_ms:>9.2f}"
        )
    total = sum(m.median_ms for m in report.marts)
    lines.append(f"\n{len(report.marts)} marts, sum of medians {total:.2f} ms")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--db", type=Path, default=DEFAULT_DB, help="DuckDB warehouse file"
    )
    parser.add_argument(
        "--repeats", type=int, default=DEFAULT_REPEATS, help="timed reads per mart"
    )
    parser.add_argument("--json", type=Path, help="also write the report as JSON here")
    args = parser.parse_args(argv)

    report = run_benchmark(args.db, repeats=args.repeats)
    print(format_report(report))
    if args.json:
        args.json.write_text(json.dumps(asdict(report), indent=2))
        log.info("wrote %s", args.json)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    main()

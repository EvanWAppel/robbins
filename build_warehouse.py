"""Build the Robbins DuckDB warehouse from Seattle-metro open data.

Upstream sources feed the ``raw`` schema of ``seattle.duckdb``, which dbt then
transforms into staging + mart models. Seattle's dominant open-data portal is
**Socrata** (`data.seattle.gov`, `data.kingcounty.gov`), reached via the SODA
API, so the net-new piece versus Elvis is :func:`fetch_socrata`. King County GIS
is ArcGIS, so the ported ArcGIS helpers will live alongside it as topics land.

Usage:
    uv run python build_warehouse.py
"""

from __future__ import annotations

import logging
import socket
import urllib.parse
from pathlib import Path

import duckdb
import pandas as pd
import requests

import city_config as cfg

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("build_warehouse")


# Some upstreams (notably aqs.epa.gov) advertise an AAAA record but have broken
# IPv6, so a default connect hangs in SYN_SENT until timeout. Prefer IPv4 for all
# fetches, falling back to whatever's available if a host is IPv4-less.
_orig_getaddrinfo = socket.getaddrinfo


def _ipv4_first(*args, **kwargs):
    results = _orig_getaddrinfo(*args, **kwargs)
    return [r for r in results if r[0] == socket.AF_INET] or results


# Deliberate global monkeypatch; the IPv4-filtered wrapper can't mirror the
# stdlib stub's exact overloads, so silence the one expected type mismatch.
socket.getaddrinfo = _ipv4_first  # ty: ignore[invalid-assignment]

DB_PATH = Path(__file__).parent / "seattle.duckdb"

# SODA default page size. Anonymous access allows large pages; 50k keeps the
# number of round-trips low for multi-hundred-thousand-row datasets.
SODA_PAGE_SIZE = 50_000
SODA_TIMEOUT = 180


# --------------------------------------------------------------------------- #
# Socrata / SODA API (net-new vs. Elvis)                                       #
# --------------------------------------------------------------------------- #
def socrata_resource_url(domain: str, dataset_id: str) -> str:
    """SODA JSON resource endpoint for a dataset."""
    return f"https://{domain}/resource/{dataset_id}.json"


def socrata_csv_url(domain: str, dataset_id: str) -> str:
    """Bulk CSV-export endpoint — full dataset, no filtering. For whole-table loads."""
    return f"https://{domain}/api/views/{dataset_id}/rows.csv?accessType=DOWNLOAD"


def socrata_resource_csv_url(
    domain: str,
    dataset_id: str,
    where: str | None = None,
    select: str | None = None,
    order: str | None = None,
    limit: int = 2_000_000,
) -> str:
    """SODA resource ``.csv`` endpoint with SoQL — CSV *and* server-side filtering.

    Unlike the bulk ``/api/views/{id}/rows.csv`` export, the resource endpoint
    honors ``$where``/``$select``/``$limit``, so we can demonstrate CSV ingestion
    while capping a huge dataset (e.g. SPD crime) to recent years. The query is
    URL-encoded so DuckDB's httpfs reader can fetch it directly.
    """
    params = {"$limit": limit}
    if where:
        params["$where"] = where
    if select:
        params["$select"] = select
    if order:
        params["$order"] = order
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    return f"https://{domain}/resource/{dataset_id}.csv?{query}"


def _soda_get(url: str, params: dict, app_token: str | None) -> list[dict]:
    """One SODA GET → list of row dicts. Isolated so tests can stub the network."""
    headers = {"X-App-Token": app_token} if app_token else {}
    resp = requests.get(url, params=params, headers=headers, timeout=SODA_TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def fetch_socrata(
    domain: str,
    dataset_id: str,
    where: str | None = None,
    select: str | None = None,
    order: str | None = None,
    page_size: int = SODA_PAGE_SIZE,
    app_token: str | None = cfg.SOCRATA_APP_TOKEN,
) -> pd.DataFrame:
    """Fetch a whole Socrata dataset via the SODA API, paging until a short page.

    Pages with ``$limit``/``$offset``. Socrata only guarantees stable paging when
    an explicit ``$order`` is given, so we default to ``:id`` when the caller
    supplies none. A fetch that returns zero rows raises (never ship an empty
    page — see PRD / CLAUDE.md data discipline).

    For very large datasets (e.g. SPD crime), prefer :func:`socrata_csv_url` and
    let DuckDB ``read_csv_auto`` ingest the export instead of paging JSON.
    """
    url = socrata_resource_url(domain, dataset_id)
    log.info(
        "Socrata fetch %s/%s (app_token=%s)",
        domain,
        dataset_id,
        "yes" if app_token else "no",
    )
    rows: list[dict] = []
    offset = 0
    while True:
        params: dict = {
            "$limit": page_size,
            "$offset": offset,
            "$order": order or ":id",
        }
        if where:
            params["$where"] = where
        if select:
            params["$select"] = select
        page = _soda_get(url, params, app_token)
        rows.extend(page)
        log.info("  %s: %d rows fetched", dataset_id, len(rows))
        if len(page) < page_size:
            break
        offset += len(page)

    if not rows:
        raise ValueError(f"Socrata {domain}/{dataset_id} returned zero rows")
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# DuckDB raw loader                                                            #
# --------------------------------------------------------------------------- #
def ingest_csv(
    con: duckdb.DuckDBPyConnection, table: str, source: str, **read_opts
) -> None:
    """Ingest a CSV (local path or remote URL) straight into ``raw.<table>``.

    For very large Socrata datasets (SPD crime ~1.5M rows, Fire 911 ~2.2M) this
    is the ingestion path: hand DuckDB the bulk CSV-export URL and let it read
    the whole file, rather than paging millions of JSON rows. Everything is read
    as text (``all_varchar``); the staging layer casts. Raises on zero rows.
    """
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    if source.startswith("http"):
        con.execute("INSTALL httpfs; LOAD httpfs;")
    opts = {"all_varchar": True, **read_opts}
    opt_sql = ", ".join(f"{k}={str(v).lower() if isinstance(v, bool) else repr(v)}"
                        for k, v in opts.items())
    con.execute(
        f"CREATE OR REPLACE TABLE raw.{table} AS "
        f"SELECT * FROM read_csv_auto(?, {opt_sql})",
        [source],
    )
    row = con.execute(f"SELECT count(*) FROM raw.{table}").fetchone()
    n = row[0] if row else 0
    log.info("Loaded raw.%s: %d rows (CSV %s)", table, n, source)
    if not n:
        raise ValueError(f"CSV ingest for raw.{table} returned zero rows: {source}")


def load_raw(con: duckdb.DuckDBPyConnection, table: str, df: pd.DataFrame) -> None:
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.register("_df", df)
    con.execute(f"CREATE OR REPLACE TABLE raw.{table} AS SELECT * FROM _df")
    con.unregister("_df")
    log.info("Loaded raw.%s: %d rows, %d cols", table, len(df), len(df.columns))


# --------------------------------------------------------------------------- #
# Per-topic raw builders                                                       #
# --------------------------------------------------------------------------- #
def build_building_permits(con: duckdb.DuckDBPyConnection) -> None:
    """Seattle DCI building permits (Socrata JSON, ~192k rows)."""
    load_raw(con, "building_permits", fetch_socrata(*cfg.PERMITS))


def build_crime(con: duckdb.DuckDBPyConnection) -> None:
    """SPD crime, recent years via the filterable resource CSV endpoint (~630k)."""
    url = socrata_resource_csv_url(
        *cfg.SPD_CRIME, where=f"report_date_time >= '{cfg.CRIME_START}'"
    )
    ingest_csv(con, "crime", url)


def build_fire_911(con: duckdb.DuckDBPyConnection) -> None:
    """Seattle Fire 911 dispatch, recent years via resource CSV endpoint."""
    url = socrata_resource_csv_url(
        *cfg.SFD_911, where=f"datetime >= '{cfg.FIRE_START}'"
    )
    ingest_csv(con, "fire_911", url)


def build_food_inspections(con: duckdb.DuckDBPyConnection) -> None:
    """Public Health – Seattle & King County food inspections (Socrata, ~106k)."""
    load_raw(con, "food_inspections", fetch_socrata(*cfg.FOOD_INSPECTIONS))


def build_short_term_rentals(con: duckdb.DuckDBPyConnection) -> None:
    """Seattle short-term rental licenses (Socrata, ~11k, ~70% geocoded)."""
    load_raw(con, "short_term_rentals", fetch_socrata(*cfg.SHORT_TERM_RENTALS))


def build_business_licenses(con: duckdb.DuckDBPyConnection) -> None:
    """Active Seattle business license tax certificates (Socrata, ~84k, non-spatial)."""
    load_raw(con, "business_licenses", fetch_socrata(*cfg.BUSINESS_LICENSES))


# raw table name -> builder. Add topics here as their sources are verified.
BUILDERS = {
    "building_permits": build_building_permits,
    "crime": build_crime,
    "fire_911": build_fire_911,
    "food_inspections": build_food_inspections,
    "short_term_rentals": build_short_term_rentals,
    "business_licenses": build_business_licenses,
}


# --------------------------------------------------------------------------- #
# Orchestration                                                                #
# --------------------------------------------------------------------------- #
def main(tables: list[str] | None = None) -> None:
    """Build the warehouse. Pass a subset of table names to build only those."""
    targets = tables or list(BUILDERS)
    unknown = [t for t in targets if t not in BUILDERS]
    if unknown:
        raise SystemExit(
            f"Unknown table(s): {', '.join(unknown)}. Known: {', '.join(BUILDERS)}"
        )
    con = duckdb.connect(str(DB_PATH))
    try:
        for table in targets:
            log.info("=== building raw.%s ===", table)
            BUILDERS[table](con)
    finally:
        con.close()
    log.info("Done. Warehouse at %s", DB_PATH)


if __name__ == "__main__":
    import sys

    main(sys.argv[1:] or None)

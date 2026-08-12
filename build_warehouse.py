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
    """Bulk CSV-export endpoint — let DuckDB ingest this directly for big datasets."""
    return f"https://{domain}/api/views/{dataset_id}/rows.csv?accessType=DOWNLOAD"


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
def load_raw(con: duckdb.DuckDBPyConnection, table: str, df: pd.DataFrame) -> None:
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.register("_df", df)
    con.execute(f"CREATE OR REPLACE TABLE raw.{table} AS SELECT * FROM _df")
    con.unregister("_df")
    log.info("Loaded raw.%s: %d rows, %d cols", table, len(df), len(df.columns))


# --------------------------------------------------------------------------- #
# Orchestration                                                                #
# --------------------------------------------------------------------------- #
def main() -> None:
    con = duckdb.connect(str(DB_PATH))
    try:
        log.info("Fetching building_permits (Seattle DCI, Socrata) ...")
        load_raw(con, "building_permits", fetch_socrata(*cfg.PERMITS))
    finally:
        con.close()

    log.info("Done. Warehouse at %s", DB_PATH)


if __name__ == "__main__":
    main()

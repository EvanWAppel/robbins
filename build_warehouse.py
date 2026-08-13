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

import io
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
# NOAA GHCN-Daily — keyless per-station bulk CSV (ported from Elvis)           #
# --------------------------------------------------------------------------- #
NCEI_GHCN_ACCESS = (
    "https://www.ncei.noaa.gov/data/"
    "global-historical-climatology-network-daily/access"
)


def noaa_ghcn_url(station: str) -> str:
    """The keyless GHCN-Daily CSV holding a station's entire daily record.

    NCEI serves one CSV per station with a wide column set (PRCP, SNOW, TMAX,
    TMIN, TAVG, ...). Values follow the GHCN convention — tenths of a mm for
    precip, tenths of a degree C for temperatures — so the staging layer divides
    by 10. Updated daily.
    """
    return f"{NCEI_GHCN_ACCESS}/{station}.csv"


# --------------------------------------------------------------------------- #
# EPA AQS — keyless pre-generated national daily bulk files (ported from Elvis) #
# --------------------------------------------------------------------------- #
AQS_AIRDATA = "https://aqs.epa.gov/aqsweb/airdata"

# National-file column -> our snake_case name. Everything else is dropped.
_AQS_COLUMNS = {
    "State Code": "state_code",
    "County Code": "county_code",
    "County Name": "county_name",
    "Site Num": "site_num",
    "Parameter Code": "parameter_code",
    "Parameter Name": "parameter_name",
    "Latitude": "latitude",
    "Longitude": "longitude",
    "Date Local": "date_local",
    "Arithmetic Mean": "arithmetic_mean",
    "AQI": "aqi",
    "Units of Measure": "units",
    "Local Site Name": "local_site_name",
    "CBSA Name": "cbsa_name",
}


def aqs_daily_url(param_code: str, year: int) -> str:
    """The keyless national daily-summary zip for one pollutant and year."""
    return f"{AQS_AIRDATA}/daily_{param_code}_{year}.zip"


def _aqs_metro_daily(df: pd.DataFrame, state: str, counties: set[str]) -> pd.DataFrame:
    """Keep only the metro counties' authoritative daily rows, snake_cased.

    A national daily file carries several rows per monitor per day (different
    sample durations / pollutant standards). The rows bearing an ``AQI`` are the
    one-per-day values on each pollutant's daily standard, so we keep those and
    drop the rest. State/county codes are compared as strings (leading zeros).
    """
    keep = (
        (df["State Code"].astype(str) == state)
        & (df["County Code"].astype(str).isin(counties))
        & (df["AQI"].notna())
    )
    return (
        df.loc[keep, list(_AQS_COLUMNS)]
        .rename(columns=_AQS_COLUMNS)
        .reset_index(drop=True)
    )


def fetch_aqs_year(
    param_code: str, year: int, state: str, counties: set[str]
) -> pd.DataFrame:
    """Download one national daily zip and return just the metro daily rows."""
    url = aqs_daily_url(param_code, year)
    log.info("AQS fetch %s %d -> %s", param_code, year, url)
    resp = requests.get(url, timeout=SODA_TIMEOUT)
    resp.raise_for_status()
    national = pd.read_csv(
        io.BytesIO(resp.content),
        compression="zip",
        dtype={"State Code": str, "County Code": str},
        low_memory=False,
    )
    metro = _aqs_metro_daily(national, state, counties)
    log.info("  %s %d: %d metro daily rows (of %d national)",
             param_code, year, len(metro), len(national))
    return metro


# --------------------------------------------------------------------------- #
# ArcGIS FeatureServer (ported from Elvis; King County GIS + Seattle art)      #
# --------------------------------------------------------------------------- #
ARCGIS_PAGE = 2000


def fetch_features(
    base_url: str,
    where: str = "1=1",
    out_fields: str = "*",
    geometry: bool = True,
    out_sr: int = 4326,
    ssl_verify: bool = True,
) -> list[tuple[dict, dict | None]]:
    """Paginate an ArcGIS layer, returning (attributes, geometry) per feature.

    Works for FeatureServer/MapServer layers across orgs. ``ssl_verify=False``
    tolerates a server with a broken TLS cert — pass it ONLY per-host, and we
    log loudly when it's used (never disable verification globally).
    """
    if not ssl_verify:
        log.warning("TLS verification DISABLED for %s (broken-cert host)", base_url)
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def get(url: str, params: dict) -> dict:
        r = requests.get(url, params=params, timeout=180, verify=ssl_verify)
        r.raise_for_status()
        return r.json()

    meta = get(base_url, {"f": "json"})
    page = min(meta.get("maxRecordCount") or ARCGIS_PAGE, ARCGIS_PAGE)
    out: list[tuple[dict, dict | None]] = []
    offset = 0
    while True:
        feats = get(
            f"{base_url}/query",
            {
                "where": where,
                "outFields": out_fields,
                "returnGeometry": "true" if geometry else "false",
                "outSR": out_sr,
                "f": "json",
                "resultOffset": offset,
                "resultRecordCount": page,
            },
        ).get("features", [])
        if not feats:
            break
        out.extend((f.get("attributes", {}), f.get("geometry")) for f in feats)
        offset += len(feats)
        log.info("  %s: %d features", base_url.rsplit("/services/", 1)[-1], len(out))
        if len(feats) < page:
            break
    return out


def _centroid(geom: dict | None) -> tuple[float | None, float | None]:
    """(lon, lat) for a point, or the vertex-average of a polygon's outer ring."""
    if not geom:
        return (None, None)
    if "x" in geom:
        return (geom.get("x"), geom.get("y"))
    rings = geom.get("rings")
    if rings:
        ext = rings[0]
        pts = ext[:-1] if len(ext) > 1 and ext[0] == ext[-1] else ext
        if pts:
            return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))
    return (None, None)


def _epoch_to_date(ms) -> str | None:
    """ArcGIS epoch-millisecond timestamp -> ISO date string (None if missing)."""
    if ms is None or (isinstance(ms, float) and pd.isna(ms)):
        return None
    dt = pd.to_datetime(ms, unit="ms", errors="coerce")
    # ArcGIS uses a 1900 sentinel for "no date"; treat pre-1990 as null.
    if pd.isna(dt) or dt.year < 1990:
        return None
    return dt.strftime("%Y-%m-%d")


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


def build_public_art(con: duckdb.DuckDBPyConnection) -> None:
    """Seattle public art (ArcGIS PublicArt2 layer, ~758 points).

    The layer's LATITUDE/LONGITUDE attribute columns are all 0, so we read the
    real WGS84 coordinates from the feature geometry (out_sr=4326).
    """
    org, service, layer = cfg.PUBLIC_ART
    base = f"{org}/{service}/FeatureServer/{layer}"
    rows: list[dict] = []
    for attrs, geom in fetch_features(base, geometry=True):
        # Drop the source LATITUDE/LONGITUDE attrs (all 0, and they collide
        # case-insensitively with our geometry-derived columns in DuckDB).
        a = {k: v for k, v in attrs.items() if k.upper() not in ("LATITUDE", "LONGITUDE")}
        a["longitude"], a["latitude"] = _centroid(geom)
        rows.append(a)
    load_raw(con, "public_art", pd.DataFrame(rows))


def build_air_quality(con: duckdb.DuckDBPyConnection) -> None:
    """EPA AQS daily PM2.5 + Ozone for the Seattle metro (King/Pierce/Snohomish).

    Loops the keyless national daily files for each pollutant and year in the
    configured window, keeping only the metro counties' AQI-bearing daily rows,
    and concatenates them into one raw table.
    """
    counties = set(cfg.AQS_COUNTIES)
    frames: list[pd.DataFrame] = []
    for param_code in cfg.AQS_PARAMS:
        for year in range(cfg.AQS_START_YEAR, cfg.AQS_END_YEAR + 1):
            frames.append(fetch_aqs_year(param_code, year, cfg.AQS_STATE, counties))
    combined = pd.concat(frames, ignore_index=True)
    if combined.empty:
        raise ValueError("EPA AQS fetch returned zero metro rows")
    load_raw(con, "air_quality", combined)


def build_weather(con: duckdb.DuckDBPyConnection) -> None:
    """Sea-Tac daily weather, GHCN-Daily station CSV (~28k days since 1948).

    The whole station record is one keyless CSV; DuckDB reads it directly. The
    file is wide (100+ mostly-empty attribute columns) so we read all as text
    and let the staging layer pick out and unit-convert the fields we chart.
    """
    ingest_csv(con, "weather", noaa_ghcn_url(cfg.NOAA_STATION))


# raw table name -> builder. Add topics here as their sources are verified.
BUILDERS = {
    "building_permits": build_building_permits,
    "crime": build_crime,
    "fire_911": build_fire_911,
    "food_inspections": build_food_inspections,
    "short_term_rentals": build_short_term_rentals,
    "business_licenses": build_business_licenses,
    "public_art": build_public_art,
    "weather": build_weather,
    "air_quality": build_air_quality,
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

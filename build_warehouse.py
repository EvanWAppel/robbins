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
import json
import logging
import re
import socket
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path

import duckdb
import pandas as pd
import requests

import city_config as cfg
import stations

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
# Water — three keyless federal feeds (USGS NWIS, NOAA CO-OPS, NRCS SNOTEL)     #
# --------------------------------------------------------------------------- #
def usgs_nwis_dv_url(site: str, param: str, start: str, end: str) -> str:
    """USGS NWIS daily-values JSON for one site + parameter over a date range."""
    return (
        "https://waterservices.usgs.gov/nwis/dv/?format=json"
        f"&sites={site}&parameterCd={param}"
        f"&startDT={start}&endDT={end}"
    )


def usgs_nwis_dv_county_url(fips5: str, param: str, start: str, end: str) -> str:
    """USGS NWIS daily-values JSON for every active gage in one county.

    ``fips5`` is the 5-digit state+county FIPS (e.g. ``53033`` = King). The
    response carries one ``timeSeries`` per gage; a county with no gage returns
    an empty ``timeSeries`` list, which :func:`parse_usgs_dv` renders as an empty
    frame (not an error) — some region counties genuinely have none.
    """
    return (
        "https://waterservices.usgs.gov/nwis/dv/?format=json"
        f"&countyCd={fips5}&parameterCd={param}&statCd=00003&siteStatus=active"
        f"&startDT={start}&endDT={end}"
    )


# The tidy columns every USGS streamflow frame carries (also the empty-frame shape).
_USGS_COLUMNS = ["obs_date", "discharge_cfs", "site_no", "station_name", "lat", "lon"]


def parse_usgs_dv(payload: dict) -> pd.DataFrame:
    """USGS NWIS dv JSON -> tidy daily frame, one row per (gage, day).

    Handles the single-site and multi-site (county) responses identically by
    iterating every ``timeSeries``. Each carries its own gage id, name, and
    coordinates in ``sourceInfo``. An empty ``timeSeries`` yields an empty frame
    with the standard columns so callers can treat "no gage" as a normal state.
    """
    rows: list[dict] = []
    for ts in payload.get("value", {}).get("timeSeries", []):
        info = ts.get("sourceInfo", {})
        site_no = info.get("siteCode", [{}])[0].get("value", "")
        name = info.get("siteName", "")
        geo = info.get("geoLocation", {}).get("geogLocation", {})
        lat, lon = geo.get("latitude"), geo.get("longitude")
        for obs in ts.get("values", [{}])[0].get("value", []):
            rows.append(
                {
                    "obs_date": obs.get("dateTime"),
                    "discharge_cfs": obs.get("value"),
                    "site_no": site_no,
                    "station_name": name,
                    "lat": lat,
                    "lon": lon,
                }
            )
    return pd.DataFrame(rows, columns=_USGS_COLUMNS)


def add_headline_flag(
    df: pd.DataFrame, station_col: str, valid: pd.Series
) -> pd.DataFrame:
    """Add an ``is_headline`` bool marking each county's one curated station.

    The headline is the station with the most valid observations in its county
    (ties -> lexicographically smallest id), via the shared
    :func:`stations.pick_headline_stations` rule — so weather, river, tide, and
    snow all curate identically. ``valid`` is a per-row bool (aligned to ``df``)
    that is True when the row carries the measurement the county's charts use;
    the frame must carry a ``county`` column. Every other station still loads
    (for the density map); only the headline drives a county's charts.
    """
    counts = (
        pd.DataFrame(
            {"county": df["county"], "station_id": df[station_col],
             "valid": valid.astype(bool)}
        )
        .groupby(["county", "station_id"])["valid"]
        .sum()
        .reset_index()
    )
    records = [
        {"county": county, "station_id": station, "valid_obs": int(count)}
        for county, station, count in zip(
            counts["county"], counts["station_id"], counts["valid"], strict=True
        )
    ]
    headline = stations.pick_headline_stations(records)
    out = df.copy()
    out["is_headline"] = [
        headline.get(county) == station
        for county, station in zip(df["county"], df[station_col], strict=True)
    ]
    return out


def noaa_tides_monthly_url(station: str, begin: str, end: str) -> str:
    """NOAA CO-OPS monthly-mean sea-level datums JSON (dates as YYYYMMDD)."""
    return (
        "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?"
        "product=monthly_mean&application=robbins"
        f"&begin_date={begin}&end_date={end}"
        f"&datum=MSL&station={station}"
        "&time_zone=lst&units=english&format=json"
    )


def snotel_stations_url(network: str, state: str) -> str:
    """NRCS AWDB station-metadata endpoint for one network + state.

    Returns every station (triplet, name, county, elevation); we filter to the
    region counties client-side in :func:`parse_snotel_stations` because the
    ``stateCds``/``networkCds`` query filters are unreliable on this API.
    """
    return (
        "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations"
        f"?networkCds={network}&stateCds={state}&activeOnly=true"
    )


def parse_snotel_stations(
    payload: list[dict], region_counties: dict[str, str]
) -> list[dict]:
    """Keep only SNOTEL stations whose county is one of our region counties.

    ``region_counties`` maps FIPS -> county name (``city_config.REGION_COUNTIES``).
    The AWDB response gives ``countyName`` (e.g. "King") but no FIPS, so we
    resolve the FIPS by name — only for Washington stations (``:WA:`` in the
    triplet), since county names repeat across states (Jefferson MT/OR). Stations in non-region counties (Chelan, Klamath,
    …) drop out. Returns dicts of ``triplet``/``name``/``county``/``elevation``.
    """
    name_to_fips = {name: fips for fips, name in region_counties.items()}
    kept: list[dict] = []
    for station in payload:
        triplet = station.get("stationTriplet", "")
        if not triplet.endswith(":SNTL") or ":WA:" not in triplet:
            continue
        fips = name_to_fips.get(station.get("countyName", ""))
        if fips is None:
            continue
        kept.append(
            {
                "triplet": triplet,
                "name": station.get("name", ""),
                "county": fips,
                "elevation": station.get("elevation"),
                "latitude": station.get("latitude"),
                "longitude": station.get("longitude"),
            }
        )
    return kept


def snotel_daily_csv_url(
    triplet: str, start: str, end: str, elements: tuple[str, ...] = ("WTEQ", "SNWD")
) -> str:
    """NRCS SNOTEL daily report CSV for one station (dates as YYYY-MM-DD)."""
    cols = ",".join(f"{e}::value" for e in elements)
    return (
        "https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/"
        f"customSingleStationReport/daily/{triplet}/{start},{end}/{cols}"
    )


def fetch_usgs_dv(site: str, param: str, start: str, end: str) -> pd.DataFrame:
    """USGS daily values -> DataFrame[obs_date, value]. Raises on an empty series."""
    url = usgs_nwis_dv_url(site, param, start, end)
    log.info("USGS NWIS fetch %s param %s (%s..%s)", site, param, start, end)
    resp = requests.get(url, timeout=SODA_TIMEOUT)
    resp.raise_for_status()
    series = resp.json()["value"]["timeSeries"]
    if not series:
        raise ValueError(f"USGS NWIS returned no series for {site}/{param}")
    values = series[0]["values"][0]["value"]
    df = pd.DataFrame(values)[["dateTime", "value"]].rename(
        columns={"dateTime": "obs_date"}
    )
    log.info("  USGS %s: %d daily rows", site, len(df))
    return df


def fetch_noaa_tides_monthly(station: str, begin: str, end: str) -> pd.DataFrame:
    """NOAA monthly-mean datums -> DataFrame (one row per month). Raises if empty."""
    url = noaa_tides_monthly_url(station, begin, end)
    log.info("NOAA tides fetch station %s (%s..%s)", station, begin, end)
    resp = requests.get(url, timeout=SODA_TIMEOUT)
    resp.raise_for_status()
    data = resp.json().get("data")
    if not data:
        raise ValueError(f"NOAA tides returned no data for station {station}")
    log.info("  NOAA %s: %d monthly rows", station, len(data))
    return pd.DataFrame(data)


def fetch_snotel_daily(triplet: str, start: str, end: str) -> pd.DataFrame:
    """NRCS SNOTEL daily report CSV -> DataFrame. Skips the '#'-commented header."""
    url = snotel_daily_csv_url(triplet, start, end)
    log.info("NRCS SNOTEL fetch %s (%s..%s)", triplet, start, end)
    resp = requests.get(url, timeout=SODA_TIMEOUT)
    resp.raise_for_status()
    df = pd.read_csv(io.StringIO(resp.text), comment="#")
    if df.empty:
        raise ValueError(f"NRCS SNOTEL returned no rows for {triplet}")
    # Columns are verbose ("Snow Water Equivalent (in) ...") — normalize.
    df.columns = ["obs_date", "swe_in", "snow_depth_in"][: len(df.columns)]
    log.info("  SNOTEL %s: %d daily rows", triplet, len(df))
    return df


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


# Square feet per square mile (State Plane WA reports Shape__Area in US survey ft).
_SQFT_PER_SQMI = 27_878_400.0


def _rings_bbox(rings: list[list[list[float]]]) -> tuple[float, float, float, float]:
    """(minx, miny, maxx, maxy) over every vertex of every ring."""
    xs = [p[0] for ring in rings for p in ring]
    ys = [p[1] for ring in rings for p in ring]
    return (min(xs), min(ys), max(xs), max(ys))


def _rings_to_multipolygon_geojson(rings: list[list[list[float]]]) -> str:
    """ArcGIS rings -> GeoJSON MultiPolygon with each ring as its own polygon.

    We deliberately do NOT model holes: treating every ring as a separate filled
    polygon means a point counts as "inside" if it falls in any ring, which is
    correct for multipart neighborhoods and only over-covers the rare hole. Good
    enough for a density choropleth, and robust to ring-winding quirks.
    """
    return json.dumps(
        {
            "type": "MultiPolygon",
            "coordinates": [[[[float(x), float(y)] for x, y in ring]] for ring in rings],
        }
    )


def mcpp_feature_row(attrs: dict, geom: dict | None) -> dict | None:
    """Pure transform: one ArcGIS MCPP (attrs, polygon geom) -> a raw.mcpp row.

    Returns None for a feature with no rings. ``geojson`` feeds the point-in-
    polygon join (spatial extension); ``rings_json`` feeds the map render; the
    bbox columns prefilter the join so ST_Contains runs on ~one candidate/point.
    """
    rings = (geom or {}).get("rings") or []
    if not rings:
        return None
    minx, miny, maxx, maxy = _rings_bbox(rings)
    area_sqft = float(attrs.get("Shape__Area") or 0.0)
    lon, lat = _centroid(geom)
    return {
        "neighborhood": (attrs.get("neighborhood") or "").strip().upper(),
        "precinct": attrs.get("precinct"),
        "area_sqft": area_sqft,
        "area_sq_miles": area_sqft / _SQFT_PER_SQMI,
        "geojson": _rings_to_multipolygon_geojson(rings),
        "rings_json": json.dumps(rings),
        "minx": minx,
        "miny": miny,
        "maxx": maxx,
        "maxy": maxy,
        "centroid_lon": lon,
        "centroid_lat": lat,
    }


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


def build_csr_311(con: duckdb.DuckDBPyConnection) -> None:
    """Seattle 311 / Find-It-Fix-It service requests, recent years via CSV export."""
    url = socrata_resource_csv_url(
        *cfg.CSR_311, where=f"createddate >= '{cfg.CSR_311_START}'"
    )
    ingest_csv(con, "csr_311", url)


# NTD two-letter mode code -> human label. Covers the modes the Puget Sound
# agencies actually report; an unknown code falls back to the raw code so nothing
# is silently dropped.
_NTD_MODE_LABELS = {
    "MB": "Bus",
    "CB": "Commuter Bus",
    "RB": "Bus Rapid Transit",
    "TB": "Trolleybus",
    "LR": "Light Rail",
    "SR": "Streetcar",
    "CR": "Commuter Rail",
    "MG": "Monorail / Automated Guideway",
    "MO": "Monorail",
    "FB": "Ferryboat",
    "DR": "Demand Response",
    "DT": "Demand Response Taxi",
    "VP": "Vanpool",
}
FERRY_MODE = "FB"


def ntd_mode_label(mode_code: str | None) -> str:
    """Human label for an NTD mode code, falling back to the raw code if unknown."""
    if not mode_code:
        return "Unknown"
    return _NTD_MODE_LABELS.get(mode_code.strip().upper(), mode_code.strip().upper())


def build_ntd_ridership(con: duckdb.DuckDBPyConnection) -> None:
    """Puget Sound monthly ridership (FTA NTD, Socrata) — transit *and* ferries.

    One raw table feeds two topics: the ferry pages filter to mode FB, the transit
    pages take the rest. We fetch only the curated metro agencies (and only recent
    years), attach each agency's friendly label and a human mode label at fetch
    time, so staging is a straight cast.
    """
    agencies = list(cfg.NTD_AGENCIES)
    quoted = ", ".join("'" + a.replace("'", "''") + "'" for a in agencies)
    where = f"agency in ({quoted}) and state = 'WA' and date >= '{cfg.NTD_START}'"
    df = fetch_socrata(
        *cfg.NTD_RIDERSHIP,
        where=where,
        select="agency, mode, tos, date, upt",
        order="date",
    )
    df["agency_label"] = df["agency"].map(cfg.NTD_AGENCIES)
    df["mode_label"] = df["mode"].map(ntd_mode_label)
    df["is_ferry"] = df["mode"] == FERRY_MODE
    load_raw(con, "ntd_ridership", df)


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


def build_mcpp(con: duckdb.DuckDBPyConnection) -> None:
    """Seattle SPD MCPP neighborhoods (ArcGIS MCPP layer, ~58 polygons).

    Backs the neighborhood choropleths. Each row carries the polygon as GeoJSON
    (for point-in-polygon joins in the dbt marts, via the spatial extension), the
    raw rings (for the PyDeck map), a bounding box (to prefilter the join), and
    area in square feet / square miles for the per-area density.
    """
    org, service, layer = cfg.MCPP_NEIGHBORHOODS
    base = f"{org}/{service}/FeatureServer/{layer}"
    rows = [
        row
        for attrs, geom in fetch_features(
            base, out_fields="neighborhood,precinct,Shape__Area", geometry=True
        )
        if (row := mcpp_feature_row(attrs, geom))
    ]
    load_raw(con, "mcpp", pd.DataFrame(rows))


_WATER_NAME_RE = re.compile(
    r"\b(" + "|".join(cfg.PARK_WATER_KEYWORDS) + r")", re.IGNORECASE
)


def is_water_park_name(name: str | None) -> bool:
    """True if a park's name references water (Seattle has many waterfront parks).

    The boundary layer carries no amenity attributes, so the name is our only
    signal. Matches any of :data:`city_config.PARK_WATER_KEYWORDS` at a word
    boundary — so "Green Lake" and "Lakeridge" match but "Discovery" (which merely
    *contains* "cove") does not. Approximate by design (labeled as such in the UI).
    """
    if not name:
        return False
    return _WATER_NAME_RE.search(name) is not None


def build_parks(con: duckdb.DuckDBPyConnection) -> None:
    """Seattle Parks & Recreation park boundaries (ArcGIS, ~511 points).

    The layer is point geometry (one point per park); coordinates come from the
    feature geometry (out_sr=4326). We attach the name-derived water flag here so
    the raw table already carries it.
    """
    org, service, layer = cfg.PARK_BOUNDARIES
    base = f"{org}/{service}/FeatureServer/{layer}"
    rows: list[dict] = []
    for attrs, geom in fetch_features(base, out_fields="NAME,PARKSBND_AREA", geometry=True):
        lon, lat = _centroid(geom)
        rows.append(
            {
                "name": attrs.get("NAME"),
                "area_sqft": attrs.get("PARKSBND_AREA"),
                "longitude": lon,
                "latitude": lat,
                "is_water_name": is_water_park_name(attrs.get("NAME")),
            }
        )
    load_raw(con, "parks", pd.DataFrame(rows))


def tree_genus(scientific_name: str | None) -> str | None:
    """Genus (first token) of a botanical name, title-cased. None if unavailable.

    SDOT records the full scientific name (e.g. ``"Acer rubrum"`` -> ``"Acer"``).
    Some names are hybrids written with a leading ``"x "`` (``"x Cupressocyparis
    leylandii"``) or an unknown placeholder; we skip the hybrid marker and treat a
    blank / "unknown" as no genus so the "most common genera" chart stays clean.
    """
    if not scientific_name:
        return None
    tokens = scientific_name.strip().split()
    if not tokens:
        return None
    # Skip a leading hybrid marker ("x" / "×") so the genus is the real first word.
    if tokens[0].lower() in ("x", "×") and len(tokens) > 1:
        tokens = tokens[1:]
    genus = tokens[0].capitalize()
    if genus.lower() in ("unknown", "vacant", "stump", ""):
        return None
    return genus


def build_trees(con: duckdb.DuckDBPyConnection) -> None:
    """SDOT street trees (ArcGIS SDOT_Trees_(Active), ~212k points).

    Point geometry; coordinates come from the feature geometry (out_sr=4326). We
    request only the columns we chart to keep the ~106-page fetch lean, and derive
    the genus (name-derived, TDD'd) here so the raw table already carries it.
    """
    org, service, layer = cfg.SDOT_TREES
    base = f"{org}/{service}/FeatureServer/{layer}"
    fields = "SCIENTIFIC_NAME,CONDITION,HERITAGE,EXCEPTIONAL,PLANTED_DATE,PRIMARYDISTRICTCD"
    rows: list[dict] = []
    for attrs, geom in fetch_features(base, out_fields=fields, geometry=True):
        lon, lat = _centroid(geom)
        rows.append(
            {
                "scientific_name": attrs.get("SCIENTIFIC_NAME"),
                "genus": tree_genus(attrs.get("SCIENTIFIC_NAME")),
                "condition": attrs.get("CONDITION"),
                "heritage": attrs.get("HERITAGE"),
                "exceptional": attrs.get("EXCEPTIONAL"),
                "planted_epoch_ms": attrs.get("PLANTED_DATE"),
                "district": attrs.get("PRIMARYDISTRICTCD"),
                "longitude": lon,
                "latitude": lat,
            }
        )
    load_raw(con, "trees", pd.DataFrame(rows))


def build_river(con: duckdb.DuckDBPyConnection) -> None:
    """Regional daily streamflow — every active USGS gage in each region county.

    One county-scoped NWIS call per county (``countyCd``); counties with no gage
    (Island, Kitsap) return an empty series and are logged, not treated as an
    error. Rows carry gage id, county, and coordinates; the county headline is
    the gage with the most valid daily discharge observations.
    """
    today = datetime.now(UTC).date()
    frames: list[pd.DataFrame] = []
    for fips, county_name in cfg.REGION_COUNTIES.items():
        url = usgs_nwis_dv_county_url(
            fips, cfg.USGS_FLOW_PARAM, f"{cfg.WATER_START_YEAR}-01-01", today.isoformat()
        )
        log.info("USGS river fetch %s County (%s)", county_name, fips)
        resp = requests.get(url, timeout=SODA_TIMEOUT)
        resp.raise_for_status()
        df = parse_usgs_dv(resp.json())
        if df.empty:
            log.info("  no active streamflow gages in %s County", county_name)
            continue
        df["county"] = fips
        df["county_name"] = county_name
        frames.append(df)
        log.info("  %s: %d gages, %d daily rows", county_name, df["site_no"].nunique(), len(df))
    if not frames:
        raise ValueError("USGS returned no streamflow gages for any region county")
    combined = pd.concat(frames, ignore_index=True)
    discharge = pd.to_numeric(combined["discharge_cfs"], errors="coerce")
    valid = discharge >= 0  # USGS no-data sentinels are negative; NaN compares False
    load_raw(con, "river", add_headline_flag(combined, "site_no", valid))


def build_tides(con: duckdb.DuckDBPyConnection) -> None:
    """Regional monthly sea-level datums — the five saltwater-front tide gauges.

    Only the coastal region counties have a long-record CO-OPS gauge (verified
    crosswalk in :data:`city_config.NOAA_TIDE_STATIONS`); each station's series
    is tagged with its county so the UI never implies inland tide coverage.
    """
    today = datetime.now(UTC).date()
    frames: list[pd.DataFrame] = []
    for station_id, (fips, station_name, lat, lon) in cfg.NOAA_TIDE_STATIONS.items():
        df = fetch_noaa_tides_monthly(
            station_id, f"{cfg.TIDES_START_YEAR}0101", today.strftime("%Y%m%d")
        )
        df["station_id"] = station_id
        df["station_name"] = station_name
        df["lat"] = lat
        df["lon"] = lon
        df["county"] = fips
        df["county_name"] = cfg.REGION_COUNTIES[fips]
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    valid = pd.to_numeric(combined["MSL"], errors="coerce").notna()
    load_raw(con, "tides", add_headline_flag(combined, "station_id", valid))


def build_snow(con: duckdb.DuckDBPyConnection) -> None:
    """Regional daily snowpack — every active WA SNOTEL station in a region county.

    Station discovery filters the AWDB inventory to the region counties by name
    (:func:`parse_snotel_stations`); each station's SWE/depth series is tagged
    with its county. Lowland counties (Island, Kitsap, Thurston) have no station.
    """
    today = datetime.now(UTC).date()
    resp = requests.get(
        snotel_stations_url(cfg.SNOTEL_NETWORK, cfg.SNOTEL_STATE), timeout=SODA_TIMEOUT
    )
    resp.raise_for_status()
    region_stations = parse_snotel_stations(resp.json(), cfg.REGION_COUNTIES)
    if not region_stations:
        raise ValueError("No SNOTEL stations resolved to region counties")
    log.info("snow: %d region SNOTEL stations", len(region_stations))
    frames: list[pd.DataFrame] = []
    for station in region_stations:
        df = fetch_snotel_daily(
            station["triplet"], f"{cfg.WATER_START_YEAR}-10-01", today.isoformat()
        )
        df["station_triplet"] = station["triplet"]
        df["station_name"] = station["name"]
        df["lat"] = station["latitude"]
        df["lon"] = station["longitude"]
        df["county"] = station["county"]
        df["county_name"] = cfg.REGION_COUNTIES[station["county"]]
        frames.append(df)
        log.info("  snow %s (%s County): %d rows", station["name"], df["county_name"].iloc[0], len(df))
    combined = pd.concat(frames, ignore_index=True)
    valid = pd.to_numeric(combined["swe_in"], errors="coerce").notna()
    load_raw(con, "snow", add_headline_flag(combined, "station_triplet", valid))


def build_water(con: duckdb.DuckDBPyConnection) -> None:
    """The regional water topic — river, tide, and snow, each region-wide.

    One builder, three ``raw`` tables (``river``, ``tides``, ``snow``), so the
    whole topic rebuilds together. Each network carries station identity and a
    per-county headline; per-county gaps (no gage / no gauge / no station) are
    real and left absent, never extrapolated from a neighbor.
    """
    build_river(con)
    build_tides(con)
    build_snow(con)


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


# The GHCN columns we keep per station (the file is 90+ columns, mostly empty).
# A per-station access CSV only carries columns for elements that station reports,
# so we select tolerantly (a station without SNOW simply lacks that column; pandas
# unions columns on concat, filling the gap with NaN).
_GHCN_USECOLS = {
    "STATION", "DATE", "LATITUDE", "LONGITUDE", "NAME",
    "PRCP", "SNOW", "SNWD", "TMAX", "TMIN",
}


def assign_weather_counties(
    con: duckdb.DuckDBPyConnection, points: pd.DataFrame
) -> pd.DataFrame:
    """Map each weather station to a region county by point-in-polygon.

    ``points`` has distinct ``STATION``/``LATITUDE``/``LONGITUDE``. County
    polygons come from TIGERweb; the DuckDB ``spatial`` extension runs
    ``ST_Contains``. Stations outside the ten region counties (the discovery
    bbox slightly overspills) fall out of the inner join. Returns
    ``STATION``/``county``/``county_name``.
    """
    feats = fetch_features(
        cfg.COUNTY_BOUNDARY, where="STATE='53'", out_fields="GEOID,NAME", geometry=True
    )
    counties = pd.DataFrame(
        [
            {
                "county": attrs["GEOID"],
                "county_name": (attrs.get("NAME") or "").replace(" County", ""),
                "geojson": _rings_to_multipolygon_geojson(geom["rings"]),
            }
            for attrs, geom in feats
            if geom and geom.get("rings") and attrs.get("GEOID") in cfg.REGION_COUNTIES
        ]
    )
    pts = points.copy()
    pts["LATITUDE"] = pts["LATITUDE"].astype(float)
    pts["LONGITUDE"] = pts["LONGITUDE"].astype(float)
    con.execute("INSTALL spatial; LOAD spatial;")
    con.register("_pts", pts)
    con.register("_cty", counties)
    result = con.execute(
        """
        SELECT p.STATION AS "STATION", c.county, c.county_name
        FROM _pts p
        JOIN _cty c
          ON ST_Contains(
               ST_GeomFromGeoJSON(c.geojson),
               ST_Point(p.LONGITUDE, p.LATITUDE)
             )
        """
    ).df()
    con.unregister("_pts")
    con.unregister("_cty")
    log.info("weather: %d/%d stations assigned to a region county", len(result), len(points))
    return result


def build_weather(con: duckdb.DuckDBPyConnection) -> None:
    """Regional daily weather — every temperature-reporting GHCN station.

    Discovery: filter the national GHCN inventory to the region bounding box,
    the TMAX element, and a recent last-year (:mod:`stations`). Each surviving
    station's daily record is clipped to WEATHER_REGIONAL_START_YEAR onward (a
    uniform window across every station, including Sea-Tac, for a lean build) and
    concatenated, then assigned to a county by point-in-polygon. Stations that
    overspill the region drop at the join.
    """
    inv = requests.get(cfg.GHCN_INVENTORY_URL, timeout=SODA_TIMEOUT)
    inv.raise_for_status()
    station_ids = stations.select_region_weather_stations(
        stations.parse_ghcn_inventory(inv.text),
        cfg.REGION_BBOX,
        cfg.GHCN_ELEMENT,
        cfg.GHCN_MIN_LAST_YEAR,
    )
    if not station_ids:
        raise ValueError("GHCN inventory yielded no region weather stations")
    log.info("weather: %d region temperature stations discovered", len(station_ids))
    frames: list[pd.DataFrame] = []
    for station_id in station_ids:
        resp = requests.get(noaa_ghcn_url(station_id), timeout=SODA_TIMEOUT)
        if resp.status_code == 404:
            log.warning("weather: no access CSV for %s, skipping", station_id)
            continue
        resp.raise_for_status()
        sdf = pd.read_csv(
            io.StringIO(resp.text), usecols=lambda c: c in _GHCN_USECOLS, dtype=str
        )
        recent = sdf[
            sdf["DATE"].str.slice(0, 4).astype(int) >= cfg.WEATHER_REGIONAL_START_YEAR
        ]
        if not recent.empty:
            frames.append(recent)
    if not frames:
        raise ValueError("GHCN station CSVs yielded no recent weather rows")
    combined = pd.concat(frames, ignore_index=True)
    county_map = assign_weather_counties(
        con, combined[["STATION", "LATITUDE", "LONGITUDE"]].drop_duplicates()
    )
    combined = combined.merge(county_map, on="STATION", how="inner")
    if combined.empty:
        raise ValueError("No weather stations fell inside a region county")
    # A headline must carry both charted series (rain and temperature) that day.
    valid = combined["PRCP"].notna() & combined["TMAX"].notna()
    load_raw(con, "weather", add_headline_flag(combined, "STATION", valid))


# raw table name -> builder. Add topics here as their sources are verified.
BUILDERS = {
    "building_permits": build_building_permits,
    "crime": build_crime,
    "csr_311": build_csr_311,
    "ntd_ridership": build_ntd_ridership,
    "fire_911": build_fire_911,
    "food_inspections": build_food_inspections,
    "short_term_rentals": build_short_term_rentals,
    "business_licenses": build_business_licenses,
    "public_art": build_public_art,
    "mcpp": build_mcpp,
    "parks": build_parks,
    "trees": build_trees,
    "weather": build_weather,
    "air_quality": build_air_quality,
    "water": build_water,
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

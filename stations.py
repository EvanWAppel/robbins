"""Shared regional-station helpers for the Weather & Water topic (PS-TOPICS-02).

Pure functions only — no network, no DuckDB — so they are cheap to unit-test.
Two responsibilities:

* :func:`pick_headline_stations` — the single curation rule shared by all four
  federal networks (weather / river / tide / snow): one headline station per
  county for the KPI and chart series, chosen as the most valid observations of
  the charted measurement, with a deterministic tie-break. Every other station still loads for the density map;
  the headline is only the series a county's charts foreground.
* :func:`parse_ghcn_inventory` + :func:`select_region_weather_stations` — GHCN
  weather station discovery. NOAA does not tag stations with a county, so we
  discover the region's weather stations from the national inventory by
  bounding box, element, and active window; county assignment happens later via
  a spatial join in the build. (River/tide/snow get their county straight from
  the source: USGS ``countyCd``, SNOTEL ``countyName``, a verified tide
  crosswalk in :mod:`city_config`.)
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

# GHCN-Daily inventory column meaning (whitespace-separated in the published
# file): ID  LATITUDE  LONGITUDE  ELEMENT  FIRSTYEAR  LASTYEAR.
_INVENTORY_FIELDS = 6


def pick_headline_stations(
    stations: Iterable[Mapping[str, object]],
) -> dict[str, str]:
    """Map each county to its one headline ``station_id``.

    ``stations`` yields mappings with ``county``, ``station_id`` and
    ``valid_obs`` (count of observations carrying the charted measurement). The
    winner per county has the most valid observations; ties break to the
    lexicographically smallest station id so the choice is stable across rebuilds.
    Every network is clipped to the same start year, so a distinct-year count
    would tie almost every station and leave the choice to the id tie-break.
    """
    best: dict[str, tuple[int, str]] = {}
    for row in stations:
        county = str(row["county"])
        station_id = str(row["station_id"])
        valid_obs = int(str(row["valid_obs"]))
        current = best.get(county)
        # Prefer more valid observations; on a tie prefer the smaller station id.
        if (
            current is None
            or valid_obs > current[0]
            or (valid_obs == current[0] and station_id < current[1])
        ):
            best[county] = (valid_obs, station_id)
    return {county: station_id for county, (_, station_id) in best.items()}


def parse_ghcn_inventory(text: str) -> list[dict[str, object]]:
    """Parse GHCN-Daily ``ghcnd-inventory.txt`` into per-row records.

    One record per (station, element) row. Malformed / short lines are skipped
    rather than raising, so a stray blank line in the 36 MB file is harmless.
    """
    records: list[dict[str, object]] = []
    for line in text.splitlines():
        parts = line.split()
        if len(parts) < _INVENTORY_FIELDS:
            continue
        station_id, lat, lon, element, first_year, last_year = parts[:_INVENTORY_FIELDS]
        records.append(
            {
                "station_id": station_id,
                "lat": float(lat),
                "lon": float(lon),
                "element": element,
                "first_year": int(first_year),
                "last_year": int(last_year),
            }
        )
    return records


def select_region_weather_stations(
    records: Iterable[Mapping[str, object]],
    bbox: tuple[float, float, float, float],
    element: str,
    min_last_year: int,
) -> list[str]:
    """Distinct station ids inside ``bbox`` that still report ``element``.

    ``bbox`` is ``(min_lat, max_lat, min_lon, max_lon)``. A station qualifies if
    it has a row for ``element`` whose ``last_year >= min_last_year`` and whose
    coordinates fall in the box. Returns a sorted, de-duplicated id list (a
    station reporting several elements must appear once).
    """
    min_lat, max_lat, min_lon, max_lon = bbox
    keep: set[str] = set()
    for rec in records:
        if rec["element"] != element:
            continue
        if int(str(rec["last_year"])) < min_last_year:
            continue
        lat = float(str(rec["lat"]))
        lon = float(str(rec["lon"]))
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            keep.add(str(rec["station_id"]))
    return sorted(keep)

"""TDD for the shared regional-station helpers (Weather & Water, PS-TOPICS-02).

These pure functions back the four-network regional expansion: the curation rule
that picks one headline station per county (used identically for weather, river,
tide, and snow), and the GHCN-Daily inventory parser + region filter that
discovers the weather stations to ingest. County assignment for river/tide/snow
comes from the source APIs (USGS countyCd, SNOTEL countyName, a verified tide
crosswalk), so only weather needs the inventory-driven discovery tested here.
"""

from __future__ import annotations

import city_config as cfg
import stations


# --------------------------------------------------------------------------- #
# pick_headline_stations — the shared "one curated station per county" rule    #
# --------------------------------------------------------------------------- #
def test_pick_headline_chooses_longest_record_per_county():
    rows = [
        {"county": "King", "station_id": "A", "record_years": 30},
        {"county": "King", "station_id": "B", "record_years": 75},
        {"county": "Pierce", "station_id": "C", "record_years": 12},
    ]
    assert stations.pick_headline_stations(rows) == {"King": "B", "Pierce": "C"}


def test_pick_headline_breaks_ties_by_station_id():
    # Equal record length -> deterministic lexicographic-min station id.
    rows = [
        {"county": "King", "station_id": "USW00024234", "record_years": 50},
        {"county": "King", "station_id": "USW00024233", "record_years": 50},
    ]
    assert stations.pick_headline_stations(rows) == {"King": "USW00024233"}


def test_pick_headline_empty_is_empty():
    assert stations.pick_headline_stations([]) == {}


# --------------------------------------------------------------------------- #
# GHCN-Daily inventory parsing + region filter (weather station discovery)     #
# --------------------------------------------------------------------------- #
# One real-format inventory line per station (whitespace-separated:
# ID LATITUDE LONGITUDE ELEMENT FIRSTYEAR LASTYEAR).
# Lines: Sea-Tac (in region, active); same station's precip row; a Whatcom-ish
# active TMAX station; a precip-only volunteer gauge; San Diego (outside bbox);
# an in-bbox but stale (last<2024) station.
SAMPLE_INVENTORY = """\
USW00024233  47.4444 -122.3139 TMAX 1948 2026
USW00024233  47.4444 -122.3139 PRCP 1948 2026
USC00456789  48.7500 -122.4800 TMAX 1990 2025
US1WAKG0021  47.6000 -122.3000 PRCP 2015 2026
USW00023188  32.7336 -117.1831 TMAX 1939 2026
USC00350000  45.5000 -121.0000 TMAX 1970 2010
"""


def test_parse_ghcn_inventory_reads_fields():
    recs = stations.parse_ghcn_inventory(SAMPLE_INVENTORY)
    first = recs[0]
    assert first["station_id"] == "USW00024233"
    assert first["element"] == "TMAX"
    assert first["first_year"] == 1948
    assert first["last_year"] == 2026
    assert abs(float(str(first["lat"])) - 47.4444) < 1e-6
    assert abs(float(str(first["lon"])) + 122.3139) < 1e-6


def test_select_region_weather_stations_filters_bbox_element_active():
    recs = stations.parse_ghcn_inventory(SAMPLE_INVENTORY)
    ids = stations.select_region_weather_stations(
        recs, bbox=cfg.REGION_BBOX, element="TMAX", min_last_year=2024
    )
    # Only the two in-bbox, active, TMAX-reporting stations survive; the precip
    # volunteer gauge, the out-of-region station, and the stale station drop.
    assert ids == ["USC00456789", "USW00024233"]


def test_select_region_weather_stations_dedupes_by_station():
    # A station listed for several elements must appear once, not once per row.
    recs = stations.parse_ghcn_inventory(SAMPLE_INVENTORY)
    ids = stations.select_region_weather_stations(
        recs, bbox=cfg.REGION_BBOX, element="TMAX", min_last_year=2024
    )
    assert len(ids) == len(set(ids))


# --------------------------------------------------------------------------- #
# Verified tide-station crosswalk (config data integrity)                      #
# --------------------------------------------------------------------------- #
def test_tide_station_counties_are_region_counties():
    # Every tide gauge is pinned to a real saltwater-front region county.
    for fips, _name, _lat, _lon in cfg.NOAA_TIDE_STATIONS.values():
        assert fips in cfg.REGION_COUNTIES


def test_tide_crosswalk_covers_the_five_verified_gauges():
    assert set(cfg.NOAA_TIDE_STATIONS) == {
        "9449424",  # Cherry Point (Whatcom)
        "9444900",  # Port Townsend (Jefferson)
        "9447130",  # Seattle (King)
        "9445958",  # Bremerton (Kitsap)
        "9446484",  # Tacoma (Pierce)
    }

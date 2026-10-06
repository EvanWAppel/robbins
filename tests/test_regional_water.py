"""TDD for the regional Weather & Water fetch adapters (PS-TOPICS-02).

The network calls themselves are exercised only at build time (and inspected by
the owner). Here we pin the pure pieces: county-scoped request URLs and the
response parsers that turn multi-station USGS / SNOTEL payloads into tidy,
county-tagged frames. A county with no station (e.g. Island/Kitsap for rivers)
must parse to an empty frame, not raise — absence is a real, expected state.
"""

from __future__ import annotations

import build_warehouse as bw
import city_config as cfg


# --------------------------------------------------------------------------- #
# USGS NWIS — county-scoped daily streamflow                                   #
# --------------------------------------------------------------------------- #
def test_usgs_county_dv_url():
    url = bw.usgs_nwis_dv_county_url("53033", "00060", "2014-01-01", "2024-12-31")
    assert url.startswith("https://waterservices.usgs.gov/nwis/dv/?format=json")
    assert "countyCd=53033" in url
    assert "parameterCd=00060" in url
    assert "startDT=2014-01-01" in url
    assert "endDT=2024-12-31" in url
    assert "siteStatus=active" in url
    # Pin the daily mean; a gage publishing max/min too would otherwise mix stats.
    assert "statCd=00003" in url


# A two-gage county payload in USGS NWIS dv JSON shape.
_USGS_PAYLOAD = {
    "value": {
        "timeSeries": [
            {
                "sourceInfo": {
                    "siteName": "CEDAR RIVER AT RENTON, WA",
                    "siteCode": [{"value": "12119000"}],
                    "geoLocation": {
                        "geogLocation": {"latitude": 47.4826, "longitude": -122.2015}
                    },
                },
                "values": [
                    {
                        "value": [
                            {"dateTime": "2014-01-01T00:00:00.000", "value": "512"},
                            {"dateTime": "2014-01-02T00:00:00.000", "value": "498"},
                        ]
                    }
                ],
            },
            {
                "sourceInfo": {
                    "siteName": "GREEN RIVER NEAR AUBURN, WA",
                    "siteCode": [{"value": "12113000"}],
                    "geoLocation": {
                        "geogLocation": {"latitude": 47.31, "longitude": -122.20}
                    },
                },
                "values": [
                    {"value": [{"dateTime": "2014-01-01T00:00:00.000", "value": "1400"}]}
                ],
            },
        ]
    }
}


def test_parse_usgs_dv_multi_site():
    df = bw.parse_usgs_dv(_USGS_PAYLOAD)
    assert len(df) == 3  # 2 + 1 daily rows
    assert set(df["site_no"]) == {"12119000", "12113000"}
    assert set(df.columns) >= {
        "obs_date",
        "discharge_cfs",
        "site_no",
        "station_name",
        "lat",
        "lon",
    }
    cedar = df[df["site_no"] == "12119000"]
    assert list(cedar["discharge_cfs"]) == ["512", "498"]
    assert cedar["station_name"].iloc[0] == "CEDAR RIVER AT RENTON, WA"


def test_parse_usgs_dv_empty_county_is_empty_frame():
    # Island/Kitsap: no gages -> empty timeSeries -> empty frame, no raise.
    df = bw.parse_usgs_dv({"value": {"timeSeries": []}})
    assert df.empty
    assert set(df.columns) >= {"obs_date", "discharge_cfs", "site_no"}


# --------------------------------------------------------------------------- #
# NRCS SNOTEL — station discovery filtered to region counties                  #
# --------------------------------------------------------------------------- #
def test_snotel_stations_url():
    url = bw.snotel_stations_url("SNTL", "WA")
    assert "networkCds=SNTL" in url
    assert "stateCds=WA" in url


_SNOTEL_STATIONS = [
    {"stationTriplet": "791:WA:SNTL", "name": "Stampede Pass", "countyName": "King",
     "stateCode": "WA", "elevation": 3860, "latitude": 47.28, "longitude": -121.34},
    {"stationTriplet": "999:OR:SNTL", "name": "Somewhere OR", "countyName": "Klamath",
     "stateCode": "OR", "elevation": 5000, "latitude": 42.0, "longitude": -121.0},
    {"stationTriplet": "908:WA:SNTL", "name": "Stevens Pass", "countyName": "Chelan",
     "stateCode": "WA", "elevation": 4060, "latitude": 47.74, "longitude": -121.09},
    {"stationTriplet": "352:WA:SNTL", "name": "Corral Pass", "countyName": "Pierce",
     "stateCode": "WA", "elevation": 6000, "latitude": 46.93, "longitude": -121.47},
    # Same county name as a region county, but in Montana — must not map to WA.
    {"stationTriplet": "123:MT:SNTL", "name": "Elsewhere MT", "countyName": "Jefferson",
     "stateCode": "MT", "elevation": 7000, "latitude": 46.2, "longitude": -112.1},
]


def test_parse_snotel_stations_keeps_only_region_counties():
    kept = bw.parse_snotel_stations(_SNOTEL_STATIONS, cfg.REGION_COUNTIES)
    triplets = {s["triplet"] for s in kept}
    # King + Pierce are region counties; Klamath (OR) and Chelan are not, and
    # Jefferson MT shares a name with Jefferson WA but is out of state.
    assert triplets == {"791:WA:SNTL", "352:WA:SNTL"}


def test_parse_snotel_stations_resolves_county_fips():
    kept = bw.parse_snotel_stations(_SNOTEL_STATIONS, cfg.REGION_COUNTIES)
    by_triplet = {s["triplet"]: s for s in kept}
    assert by_triplet["791:WA:SNTL"]["county"] == "53033"  # King
    assert by_triplet["352:WA:SNTL"]["county"] == "53053"  # Pierce


# --------------------------------------------------------------------------- #
# add_headline_flag — mark each county's curated headline station              #
# --------------------------------------------------------------------------- #
def test_add_headline_flag_marks_most_valid_observations_per_county():
    import pandas as pd

    # King: A has 2 valid rows, B has 1 -> A is headline.
    # Pierce: only C -> C is headline.
    df = pd.DataFrame(
        {
            "county": ["53033", "53033", "53033", "53053"],
            "site": ["A", "A", "B", "C"],
            "val": [1, 2, 3, 4],
        }
    )
    valid = pd.Series([True, True, True, True])
    out = bw.add_headline_flag(df, "site", valid)
    flags = dict(zip(out["site"], out["is_headline"], strict=True))
    # A appears twice; both rows flagged headline.
    assert flags["A"] is True
    assert flags["B"] is False
    assert flags["C"] is True
    # Original columns preserved, one new boolean column added.
    assert "is_headline" in out.columns
    assert len(out) == len(df)


def test_add_headline_flag_dense_station_beats_sparse_smaller_id():
    import pandas as pd

    # Both stations span the same years (the old distinct-year score tied them,
    # handing the headline to the smaller id). The daily station has more valid
    # observations and must win despite sorting after the sparse co-op id.
    days = pd.date_range("2014-01-01", "2015-12-31", freq="D")
    dense = pd.DataFrame({"county": "53033", "site": "USW00024233", "d": days})
    sparse = pd.DataFrame(
        {"county": "53033", "site": "USC00451233",
         "d": pd.to_datetime(["2014-06-01", "2015-06-01"])}
    )
    df = pd.concat([dense, sparse], ignore_index=True)
    out = bw.add_headline_flag(df, "site", pd.Series(True, index=df.index))
    headline = set(out.loc[out["is_headline"], "site"])
    assert headline == {"USW00024233"}


def test_add_headline_flag_ignores_invalid_rows():
    import pandas as pd

    # A has more rows, but only one carries the charted measurement; B has two.
    df = pd.DataFrame(
        {"county": ["53033"] * 5, "site": ["A", "A", "A", "B", "B"]}
    )
    valid = pd.Series([True, False, False, True, True])
    out = bw.add_headline_flag(df, "site", valid)
    assert set(out.loc[out["is_headline"], "site"]) == {"B"}

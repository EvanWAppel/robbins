"""TDD for the EPA AQS air-quality ingestion — keyless national daily bulk files.

Each ``daily_{param}_{year}.zip`` is a national file; we keep only the Seattle-
metro counties and the authoritative daily rows (those carrying an AQI — one per
monitor per day, on the pollutant's daily standard). Two pure pieces are tested:
the URL builder and the metro/daily filter+rename.
"""

from __future__ import annotations

import pandas as pd

import build_warehouse as bw


def test_aqs_daily_url():
    assert (
        bw.aqs_daily_url("88101", 2024)
        == "https://aqs.epa.gov/aqsweb/airdata/daily_88101_2024.zip"
    )


def _raw_frame() -> pd.DataFrame:
    # Minimal national-file shape: two metro rows (one with AQI, one hourly row
    # without), plus an out-of-state row that must be dropped.
    return pd.DataFrame(
        {
            "State Code": ["53", "53", "06"],
            "County Code": ["033", "033", "037"],
            "County Name": ["King", "King", "Los Angeles"],
            "Site Num": ["0030", "0030", "1103"],
            "Parameter Code": ["88101", "88101", "88101"],
            "Parameter Name": ["PM2.5 - Local Conditions"] * 3,
            "Latitude": [47.6, 47.6, 34.0],
            "Longitude": [-122.3, -122.3, -118.2],
            "Date Local": ["2024-01-01", "2024-01-01", "2024-01-01"],
            "Arithmetic Mean": [20.0, 18.5, 12.0],
            "AQI": [68.0, None, 50.0],
            "Units of Measure": ["Micrograms/cubic meter (LC)"] * 3,
            "Local Site Name": ["Seattle-10th & Weller", "Seattle-10th & Weller", "LA"],
            "CBSA Name": ["Seattle-Tacoma-Bellevue, WA"] * 2 + ["Los Angeles, CA"],
        }
    )


def test_aqs_metro_daily_keeps_only_metro_aqi_rows():
    out = bw._aqs_metro_daily(_raw_frame(), state="53", counties={"033", "053", "061"})
    # Out-of-state row and the AQI-less hourly row are both dropped.
    assert len(out) == 1
    assert out.iloc[0]["county_name"] == "King"
    assert out.iloc[0]["aqi"] == 68.0


def test_aqs_metro_daily_renames_to_snake_case():
    out = bw._aqs_metro_daily(_raw_frame(), state="53", counties={"033"})
    assert set(out.columns) == {
        "state_code", "county_code", "county_name", "site_num",
        "parameter_code", "parameter_name", "latitude", "longitude",
        "date_local", "arithmetic_mean", "aqi", "units",
        "local_site_name", "cbsa_name",
    }

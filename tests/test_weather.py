"""TDD for the NOAA GHCN-Daily weather fetch — Sea-Tac station bulk CSV.

The station's whole daily record is a single keyless CSV at NCEI; the only
Python transform is the URL builder (unit conversion + casting live in the dbt
staging layer). We test that the builder points at the right station file.
"""

from __future__ import annotations

import build_warehouse as bw


def test_noaa_ghcn_url_default_station():
    assert (
        bw.noaa_ghcn_url("USW00024233")
        == "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/USW00024233.csv"
    )


def test_noaa_ghcn_url_uses_given_station():
    # A different station id flows straight into the access path.
    url = bw.noaa_ghcn_url("USW00094290")
    assert url.endswith("/access/USW00094290.csv")

"""TDD for the Water topic's three URL builders (USGS + NOAA + NRCS SNOTEL).

The "signature water body" page draws on three keyless federal feeds; the pure,
testable piece of each is its request URL. Response parsing is exercised at fetch
time; here we pin the URL shape so a config change can't silently misroute.
"""

from __future__ import annotations

import build_warehouse as bw


def test_usgs_nwis_dv_url():
    url = bw.usgs_nwis_dv_url("12119000", "00060", "2015-01-01", "2024-12-31")
    assert url == (
        "https://waterservices.usgs.gov/nwis/dv/?format=json"
        "&sites=12119000&parameterCd=00060"
        "&startDT=2015-01-01&endDT=2024-12-31"
    )


def test_noaa_tides_monthly_url():
    url = bw.noaa_tides_monthly_url("9447130", "20000101", "20241231")
    assert url.startswith("https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?")
    assert "product=monthly_mean" in url
    assert "station=9447130" in url
    assert "begin_date=20000101" in url
    assert "end_date=20241231" in url
    assert "datum=MSL" in url
    assert "format=json" in url


def test_snotel_daily_csv_url():
    url = bw.snotel_daily_csv_url("791:WA:SNTL", "2015-10-01", "2024-06-01")
    assert url == (
        "https://wcc.sc.egov.usda.gov/reportGenerator/view_csv/"
        "customSingleStationReport/daily/791:WA:SNTL/"
        "2015-10-01,2024-06-01/WTEQ::value,SNWD::value"
    )

"""Regional Puget Sound water — snowpack, rivers, and sea level, by county.

Three federal networks with real, unequal coverage: USGS streamflow gages (8/10
counties), NOAA tide gauges (the 5 saltwater-front counties), and NRCS SNOTEL snow
(the 7 mountainous ones). Each county's charts use its headline station (the one
with the most valid observations); a county with no station in a network is shown as an explicit gap, never
filled in from a neighbor. The map shows every station colored by network.
"""

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st
from pydeck.data_utils import compute_view

import ui
from app_db import query
from city_config import REGION_COUNTIES
from geography import county_selector
from regional_water import water_queries

st.title("Water")
st.caption(
    "The Cascade-to-tap-to-Sound water story across Puget Sound, from three keyless "
    "federal networks: NRCS SNOTEL snowpack, USGS river streamflow, and NOAA tide "
    "gauges. Coverage varies by county; gaps are shown, not filled in."
)

county = st.session_state.get("selected_county")
if not st.session_state.get("_regional_navigation"):
    county = county_selector()
multi = county is None
place = f"{REGION_COUNTIES[county]} County" if county else "Puget Sound"

q = water_queries(county)
coverage = query(*q["coverage"])
snow_peak = query(*q["snow_annual_peak"])
snow_recent = query(*q["snow_recent"])
river_normals = query(*q["river_monthly"])
river_annual = query(*q["river_annual"])
tides_annual = query(*q["tides_annual"])
river_st = query(*q["river_stations"])
tides_st = query(*q["tides_stations"])
snow_st = query(*q["snow_stations"])

st.subheader(place if county else "Puget Sound — county headline stations")
if coverage.empty:
    st.info(
        "No river, tide, or snow stations are loaded for this selection. This is "
        "missing coverage, not an absence of water."
    )
    st.stop()

networks_here = set(coverage["network"])
st.caption(
    f"Observed {coverage['first_date'].min():%b %Y}–{coverage['last_date'].max():%b %Y}. "
    "Charts use each county's headline station; the map shows every station."
)
with st.expander("Station coverage by network and county"):
    st.dataframe(
        coverage.rename(
            columns={
                "network": "Network", "county": "County", "station_count": "Stations",
                "first_date": "First", "last_date": "Last",
            }
        )[["Network", "County", "Stations", "First", "Last"]],
        hide_index=True, width="stretch",
    )

# --- KPIs: how many counties each network reaches in this selection ---
by_net = coverage.groupby("network")["station_count"].sum()
c1, c2, c3 = st.columns(3)
c1.metric("River gages", f"{int(by_net.get('River', 0))}")
c2.metric("Tide gauges", f"{int(by_net.get('Tide', 0))}")
c3.metric("Snow stations", f"{int(by_net.get('Snow', 0))}")

st.divider()


def _color(base):
    return alt.Color("county:N", title="County") if multi else alt.value(base)


month_sort = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

# --- Snowpack ---
st.subheader("Cascade snowpack, year by year")
if snow_peak.empty:
    st.info(f"No NRCS SNOTEL snow station in {place}. Lowland counties have none.")
else:
    st.caption("Peak snow-water-equivalent each water year (headline station per county). "
               "2015 was a historic snow-drought across the region.")
    peak_chart = alt.Chart(snow_peak).mark_bar().encode(
        x=alt.X("water_year:O", title="Water year"),
        y=alt.Y("peak_swe_in:Q", title="Peak SWE (in)"),
        color=alt.Color("county:N", title="County") if multi else alt.Color(
            "peak_swe_in:Q", scale=alt.Scale(scheme="blues"), legend=None),
        xOffset=alt.XOffset("county:N") if multi else alt.Undefined,
        tooltip=[alt.Tooltip("county:N"), alt.Tooltip("water_year:O", title="Water year"),
                 alt.Tooltip("peak_swe_in:Q", title="Peak SWE (in)", format=".1f")],
    )
    ui.chart(peak_chart, width="stretch")
    if not snow_recent.empty and not multi:
        st.caption("The most recent three winters, day by day.")
        recent_chart = alt.Chart(snow_recent).mark_line().encode(
            x=alt.X("obs_date:T", title=None),
            y=alt.Y("swe_in:Q", title="Snow water equivalent (in)"),
            color=alt.Color("water_year:N", title="Water year"),
            tooltip=[alt.Tooltip("obs_date:T", title="Date"),
                     alt.Tooltip("swe_in:Q", title="SWE (in)", format=".1f")],
        )
        ui.chart(recent_chart, width="stretch")

# --- River ---
st.subheader("Rivers through the year")
if river_normals.empty:
    st.info(f"No USGS streamflow gage in {place}.")
else:
    st.caption("Average daily streamflow by month at the headline gage — high with "
               "winter rain and spring melt, low by late summer.")
    if multi:
        river_chart = alt.Chart(river_normals).mark_line(point=True).encode(
            x=alt.X("month_name:N", sort=month_sort, title=None),
            y=alt.Y("avg_discharge_cfs:Q", title="Avg discharge (cfs)"),
            color=_color("#3f7d86"),
            tooltip=[alt.Tooltip("county:N"), alt.Tooltip("month_name:N", title="Month"),
                     alt.Tooltip("avg_discharge_cfs:Q", title="Avg discharge (cfs)", format=",.0f")],
        )
    else:
        river_chart = alt.Chart(river_normals).mark_area(
            color="#3f7d86", opacity=0.7, line={"color": "#3f7d86"}).encode(
            x=alt.X("month_name:N", sort=month_sort, title=None),
            y=alt.Y("avg_discharge_cfs:Q", title="Avg discharge (cfs)"),
            tooltip=[alt.Tooltip("month_name:N", title="Month"),
                     alt.Tooltip("avg_discharge_cfs:Q", title="Avg discharge (cfs)", format=",.0f")],
        )
    ui.chart(river_chart, width="stretch")

# --- Sea level ---
st.subheader("Puget Sound sea level")
if tides_annual.empty:
    st.info(f"No NOAA tide gauge in {place}. Only saltwater-front counties have one.")
else:
    tides_full = tides_annual[tides_annual["month_count"] >= 12]
    if tides_full.empty:
        st.info("Not enough full years of tide data for a sea-level trend in this selection.")
    else:
        st.caption("Average annual mean sea level at the headline gauge (NOAA datum, feet). "
                   "The current partial year is excluded.")
        sea_chart = alt.Chart(tides_full).mark_line(point=True).encode(
            x=alt.X("year:O", title=None),
            y=alt.Y("avg_msl_ft:Q", title="Mean sea level (ft)", scale=alt.Scale(zero=False)),
            color=_color("#4f88a6"),
            tooltip=[alt.Tooltip("county:N"), alt.Tooltip("year:O", title="Year"),
                     alt.Tooltip("avg_msl_ft:Q", title="Mean sea level (ft)", format=".3f")],
        )
        if multi:
            ui.chart(sea_chart, width="stretch")
        else:
            trend = sea_chart.transform_regression("year", "avg_msl_ft").mark_line(
                color="#b4503f", strokeDash=[5, 5])
            ui.chart(sea_chart + trend, width="stretch")

# --- Station map (all three networks) ---
def _stations(df, network, color):
    if df.empty:
        return None
    d = df.dropna(subset=["latitude", "longitude"]).copy()
    if d.empty:
        return None
    d["network"] = network
    d["color"] = [color] * len(d)
    return d[["latitude", "longitude", "station_name", "county", "network", "color"]]


layers = [
    frame for frame in (
        _stations(river_st, "River gage", [63, 125, 134, 200]),
        _stations(tides_st, "Tide gauge", [79, 136, 166, 200]),
        _stations(snow_st, "Snow station", [140, 160, 200, 200]),
    ) if frame is not None
]
if layers:
    st.subheader("Water monitoring stations")
    st.caption("River gages (teal), tide gauges (blue), and snow stations (light).")
    points = pd.concat(layers, ignore_index=True)
    viewport = compute_view(points[["longitude", "latitude"]])
    viewport.zoom = min(viewport.zoom - 0.5, 9)
    viewport.pitch = 0
    st.pydeck_chart(
        pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            initial_view_state=viewport,
            layers=[
                pdk.Layer(
                    "ScatterplotLayer", data=points,
                    get_position="[longitude, latitude]", get_fill_color="color",
                    get_radius=1800, radius_min_pixels=4, radius_max_pixels=16, pickable=True,
                )
            ],
            tooltip={"text": "{station_name}\n{county} County · {network}"},
        )
    )

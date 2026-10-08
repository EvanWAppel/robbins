"""Regional Puget Sound weather — "Rain & Records" across county headline stations.

Every county's charts use its "headline" NOAA GHCN-Daily station (the most days
with rain and both temperatures); the map shows every temperature-reporting station
in the selection. With a county chosen the page reads like the old single-station
page; across all of Puget Sound it compares counties. Historical observations, not current conditions.
"""

import altair as alt
import pydeck as pdk
import streamlit as st
from pydeck.data_utils import compute_view

import ui
from app_db import query
from city_config import REGION_COUNTIES, WEATHER_REGIONAL_START_YEAR
from geography import county_selector
from regional_weather import weather_queries

st.title("Rain & Records")
st.caption(
    "Daily weather from NOAA GHCN-Daily stations across Puget Sound. Each county's "
    "charts use its 'headline' station (the most days with rain and temperature "
    "readings); the map shows every station. "
    "These are historical observations, not current weather conditions."
)

county = st.session_state.get("selected_county")
if not st.session_state.get("_regional_navigation"):
    county = county_selector()
multi = county is None

q = weather_queries(county)
coverage = query(*q["coverage"])
normals = query(*q["monthly_normals"])
annual = query(*q["annual"])
records = query(*q["records"])
recent = query(*q["recent"])
stations = query(*q["stations"])

st.subheader(f"{REGION_COUNTIES[county]} County" if county else "Puget Sound — county headline stations")
if coverage.empty:
    st.info(
        "No weather stations are loaded for this selection. This is missing "
        "coverage, not an absence of weather."
    )
    st.stop()

st.caption(
    f"Observed {coverage['first_date'].min():%b %Y}–{coverage['last_date'].max():%b %Y} "
    f"across {int(coverage['station_count'].sum())} station(s). "
    "Charts use each county's headline station; the map shows all of them."
)
if multi:
    missing = sorted(set(REGION_COUNTIES.values()) - set(coverage["county"]))
    if missing:
        st.info("No loaded weather stations for: " + ", ".join(missing) + ".")
with st.expander("Station coverage by county"):
    st.dataframe(
        coverage.rename(
            columns={
                "county": "County", "headline_station": "Headline station",
                "station_count": "Stations", "first_date": "First", "last_date": "Last",
            }
        )[["County", "Headline station", "Stations", "First", "Last"]],
        hide_index=True, width="stretch",
    )

# --- KPIs ---
c1, c2, c3 = st.columns(3)
c1.metric("Counties covered", f"{len(coverage)}")
c2.metric("Weather stations", f"{int(coverage['station_count'].sum())}")
c3.metric("Observed since", f"{coverage['first_date'].min():%Y}")

st.divider()


def _color(base):
    """County color when comparing the region; a fixed hue for one county."""
    return alt.Color("county:N", title="County") if multi else alt.value(base)


# --- Climatology: precip by calendar month ---
st.subheader("A wet winter and a dry summer")
st.caption("Average daily precipitation by calendar month (headline station per county).")
month_sort = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
if multi:
    precip_chart = alt.Chart(normals).mark_line(point=True).encode(
        x=alt.X("month_name:N", sort=month_sort, title=None),
        y=alt.Y("avg_precip_in:Q", title="Avg precip (in/day)"),
        color=_color("#4f88a6"),
        tooltip=[alt.Tooltip("county:N"), alt.Tooltip("month_name:N", title="Month"),
                 alt.Tooltip("avg_precip_in:Q", title="Avg precip (in/day)", format=".3f")],
    )
else:
    precip_chart = alt.Chart(normals).mark_bar(color="#4f88a6").encode(
        x=alt.X("month_name:N", sort=month_sort, title=None),
        y=alt.Y("avg_precip_in:Q", title="Avg precip (in/day)"),
        tooltip=[alt.Tooltip("month_name:N", title="Month"),
                 alt.Tooltip("avg_precip_in:Q", title="Avg precip (in/day)", format=".3f")],
    )
ui.chart(precip_chart, width="stretch")

# --- Temperature by month ---
if not multi:
    st.subheader("Average high and low by month")
    temp_domain = [float(normals["avg_tmin_f"].min()) - 5, float(normals["avg_tmax_f"].max()) + 5]
    temp_chart = alt.Chart(normals).mark_area(opacity=0.3, color="#c1913f").encode(
        x=alt.X("month_name:N", sort=month_sort, title=None),
        y=alt.Y("avg_tmin_f:Q", title="Temperature (°F)", scale=alt.Scale(zero=False, domain=temp_domain)),
        y2="avg_tmax_f:Q",
        tooltip=[alt.Tooltip("month_name:N", title="Month"),
                 alt.Tooltip("avg_tmax_f:Q", title="Avg high (°F)", format=".0f"),
                 alt.Tooltip("avg_tmin_f:Q", title="Avg low (°F)", format=".0f")],
    )
    ui.chart(temp_chart, width="stretch")
else:
    st.subheader("Average summer high by county")
    st.caption("Mean daily high temperature by calendar month, headline station per county.")
    temp_chart = alt.Chart(normals).mark_line(point=True).encode(
        x=alt.X("month_name:N", sort=month_sort, title=None),
        y=alt.Y("avg_tmax_f:Q", title="Avg high (°F)", scale=alt.Scale(zero=False)),
        color=_color("#c1913f"),
        tooltip=[alt.Tooltip("county:N"), alt.Tooltip("month_name:N", title="Month"),
                 alt.Tooltip("avg_tmax_f:Q", title="Avg high (°F)", format=".0f")],
    )
    ui.chart(temp_chart, width="stretch")

# --- Annual rainfall trend (drop each series' partial current year) ---
st.subheader("Total rainfall by year")
st.caption("Each county's headline station; the current (partial) year is excluded.")
annual_full = annual[annual["year"] < annual.groupby("county")["year"].transform("max")]
rain_line = alt.Chart(annual_full).mark_line(point=True).encode(
    x=alt.X("year:O", title=None),
    y=alt.Y("total_precip_in:Q", title="Total precip (in)"),
    color=_color("#4f88a6"),
    tooltip=[alt.Tooltip("county:N"), alt.Tooltip("year:O", title="Year"),
             alt.Tooltip("total_precip_in:Q", title="Total precip (in)", format=".1f"),
             alt.Tooltip("rain_days:Q", title="Rainy days")],
)
ui.chart(rain_line, width="stretch")

# --- Recent daily band (only legible for a single county) ---
if not multi and not recent.empty:
    st.subheader("The last two years, day by day")
    st.caption("Daily high and low at the county's headline station.")
    recent_domain = [float(recent["tmin_f"].min()) - 5, float(recent["tmax_f"].max()) + 5]
    recent_band = alt.Chart(recent).mark_area(opacity=0.4, color="#c1913f").encode(
        x=alt.X("obs_date:T", title=None),
        y=alt.Y("tmin_f:Q", title="Temperature (°F)", scale=alt.Scale(zero=False, domain=recent_domain)),
        y2="tmax_f:Q",
        tooltip=[alt.Tooltip("obs_date:T", title="Date"),
                 alt.Tooltip("tmax_f:Q", title="High (°F)", format=".0f"),
                 alt.Tooltip("tmin_f:Q", title="Low (°F)", format=".0f")],
    )
    ui.chart(recent_band, width="stretch")

# --- Station map (every station in the selection) ---
mappable = stations.dropna(subset=["latitude", "longitude"])
if not mappable.empty:
    st.subheader("Weather stations")
    st.caption("Every temperature-reporting station; larger/darker points are headline stations.")
    mappable = mappable.copy()
    mappable["color"] = mappable["is_headline"].apply(
        lambda h: [193, 145, 63, 220] if h else [79, 136, 166, 160]
    )
    mappable["radius"] = mappable["is_headline"].apply(lambda h: 2600 if h else 1400)
    viewport = compute_view(mappable[["longitude", "latitude"]])
    viewport.zoom = min(viewport.zoom - 0.5, 9)
    viewport.pitch = 0
    st.pydeck_chart(
        pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            initial_view_state=viewport,
            layers=[
                pdk.Layer(
                    "ScatterplotLayer", data=mappable,
                    get_position="[longitude, latitude]", get_fill_color="color",
                    get_radius="radius", radius_min_pixels=3, radius_max_pixels=22, pickable=True,
                )
            ],
            tooltip={"text": "{station_name}\n{county} County"},
        )
    )

# --- Records table ---
# The warehouse holds WEATHER_REGIONAL_START_YEAR onward only, so these are
# records within that window, not all-time station records.
st.subheader(f"Records since {WEATHER_REGIONAL_START_YEAR}"
             + (f" — {REGION_COUNTIES[county]} County" if county else " by county"))
records_display = records.rename(
    columns={"county": "County", "record_type": "Record", "obs_date": "Date", "value": "Value"}
)
cols = ["Record", "Date", "Value"] if county else ["County", "Record", "Date", "Value"]
st.dataframe(records_display[cols], width="stretch", hide_index=True)

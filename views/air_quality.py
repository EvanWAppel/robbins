"""Puget Sound air quality — geographically filtered EPA observations.

Puget Sound air is clean most of the year; the story is the handful of wildfire-
smoke days that spike the AQI into the red. The page leads with how rare bad days
are, then the monthly peaks that expose the smoke seasons, the monitors on a map,
and the all-time worst days. Sourced from EPA's keyless national daily bulk files.
"""

import altair as alt
import pydeck as pdk
import streamlit as st
from pydeck.data_utils import compute_view

import ui
from app_db import query
from city_config import REGION_COUNTIES
from geography import county_selector
from regional_air import air_queries

# EPA AQI category colors (adapted for the dark theme).
CAT_COLORS = {
    "Good": "#2ecc71",
    "Moderate": "#f1c40f",
    "Unhealthy for Sensitive Groups": "#e67e22",
    "Unhealthy": "#e74c3c",
    "Very Unhealthy": "#8e44ad",
    "Hazardous": "#7e0023",
}

st.title("Air Quality")
st.caption(
    "Daily PM2.5 and ozone observations from EPA monitors. "
    "Coverage varies by county, pollutant, and reporting period; these are "
    "historical observations, not current air-quality conditions."
)

# The main app renders the shared control; support direct page smoke checks too.
county = st.session_state.get("selected_county")
if not st.session_state.get("_regional_navigation"):
    county = county_selector()
queries = air_queries(county)
categories = query(*queries["categories"])
worst = query(*queries["worst"])
sites = query(*queries["sites"])
monthly = query(*queries["monthly"])
coverage = query(*queries["coverage"])
label = f"{REGION_COUNTIES[county]} County" if county else "Puget Sound — available monitors"
st.subheader(label)
if coverage.empty:
    st.info("No air-quality observations are loaded for this selection. This is missing coverage, not zero pollution.")
    st.stop()

st.caption(
    f"Observed {coverage['first_date'].min():%b %d, %Y}–{coverage['last_date'].max():%b %d, %Y}. "
    "Observed dates describe the loaded records, not the last retrieval time."
)
if county is None:
    missing = sorted(set(REGION_COUNTIES.values()) - set(coverage["county"]))
    if missing:
        st.info("No loaded observations for: " + ", ".join(missing) + ". Regional summaries use the available monitors only.")
with st.expander("Monitor coverage and reporting periods"):
    st.dataframe(coverage, hide_index=True, width="stretch")

# --- KPIs ---
total_days = int(categories["day_count"].sum())
good_mod = int(
    categories.loc[categories["aqi_category"].isin(["Good", "Moderate"]), "day_count"].sum()
)
worst_row = worst.iloc[0] if not worst.empty else None
c1, c2, c3, c4 = st.columns(4)
c1.metric("PM2.5 days", f"{total_days:,}")
c2.metric("Good / Moderate", f"{good_mod / total_days * 100:.0f}%" if total_days else "No PM2.5 data")
c3.metric("Peak PM2.5 AQI", f"{int(worst_row.max_aqi)}" if worst_row is not None else "No PM2.5 data")
if worst_row is not None:
    c3.caption(worst_row.obs_date.strftime("%b %-d, %Y"))
c4.metric("PM2.5 monitors", f"{len(sites)}")

st.divider()

# --- Category distribution ---
st.subheader("Daily PM2.5 categories")
st.caption("Each observed day is counted once, using the highest PM2.5 AQI among the selected monitors.")
cat_chart = (
    alt.Chart(categories)
    .mark_bar()
    .encode(
        x=alt.X("day_count:Q", title="Days"),
        y=alt.Y("aqi_category:N", sort=alt.EncodingSortField("severity"), title=None),
        color=alt.Color(
            "aqi_category:N",
            scale=alt.Scale(domain=list(CAT_COLORS), range=list(CAT_COLORS.values())),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("aqi_category:N", title="Category"),
            alt.Tooltip("day_count:Q", title="Days", format=","),
        ],
    )
)
ui.chart(cat_chart, width="stretch")

# --- Monthly peak AQI (the smoke seasons) ---
st.subheader("Monthly peak AQI")
st.caption(
    "Peak AQI recorded each month among the selected monitors, by pollutant. "
    "Available sites and reporting periods may differ between pollutants."
)
peak_chart = (
    alt.Chart(monthly)
    .mark_line(point=True)
    .encode(
        x=alt.X("obs_month:T", title=None),
        y=alt.Y("max_aqi:Q", title="Peak AQI"),
        color=alt.Color("pollutant:N", title="Pollutant"),
        tooltip=[
            alt.Tooltip("obs_month:T", title="Month", format="%b %Y"),
            alt.Tooltip("pollutant:N", title="Pollutant"),
            alt.Tooltip("max_aqi:Q", title="Peak AQI"),
            alt.Tooltip("avg_aqi:Q", title="Avg AQI", format=".1f"),
        ],
    )
)
ui.chart(peak_chart, width="stretch")

# --- Monitor map ---
st.subheader("PM2.5 monitor locations")
st.caption("Each point is a PM2.5 monitor, sized and colored by its average AQI.")


def _aqi_color(aqi: float) -> list[int]:
    if aqi <= 50:
        return [46, 204, 113, 200]
    if aqi <= 100:
        return [241, 196, 15, 200]
    return [231, 126, 34, 200]


if not sites.dropna(subset=["latitude", "longitude"]).empty:
    sites = sites.dropna(subset=["latitude", "longitude"]).copy()
    sites["color"] = sites["avg_aqi"].apply(_aqi_color)
    viewport = compute_view(sites[["longitude", "latitude"]])
    viewport.zoom = min(viewport.zoom - 0.75, 10)
    viewport.pitch = 0
    st.pydeck_chart(
        pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            initial_view_state=viewport,
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=sites,
                    get_position="[longitude, latitude]",
                    get_fill_color="color",
                    get_radius="avg_aqi * 40",
                    radius_min_pixels=4,
                    radius_max_pixels=30,
                    pickable=True,
                )
            ],
            tooltip={"text": "{site}\n{county} County · avg AQI {avg_aqi}"},
        )
    )
else:
    st.info("No mapped PM2.5 monitors for this selection.")

# --- Worst days ---
st.subheader("Highest PM2.5 days in the loaded period")
worst = worst.copy()
worst["obs_date"] = worst["obs_date"].dt.date
worst_display = worst.rename(
    columns={
        "obs_date": "Date",
        "max_aqi": "Peak AQI",
        "aqi_category": "Category",
        "site": "Monitor",
        "county": "County",
    }
)
st.dataframe(worst_display, width="stretch", hide_index=True)

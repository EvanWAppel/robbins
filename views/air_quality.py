"""Seattle-metro air quality — EPA AQS daily PM2.5 + Ozone (King/Pierce/Snohomish).

Puget Sound air is clean most of the year; the story is the handful of wildfire-
smoke days that spike the AQI into the red. The page leads with how rare bad days
are, then the monthly peaks that expose the smoke seasons, the monitors on a map,
and the all-time worst days. Sourced from EPA's keyless national daily bulk files.
"""

import altair as alt
import pydeck as pdk
import streamlit as st

from app_db import query

# EPA AQI category colors (adapted for the dark theme).
CAT_COLORS = {
    "Good": "#2ecc71",
    "Moderate": "#f1c40f",
    "Unhealthy for Sensitive Groups": "#e67e22",
    "Unhealthy": "#e74c3c",
    "Very Unhealthy": "#8e44ad",
    "Hazardous": "#7e0023",
}

st.title("💨 Air Quality")
st.caption(
    "Daily PM2.5 and Ozone at EPA monitors across King, Pierce and Snohomish "
    "counties since 2019. Air Quality Index (AQI) is comparable across pollutants: "
    "0-50 is Good, 300+ is Hazardous."
)

categories = query(
    "select aqi_category, day_count, severity from main.mart_air_category_days order by severity"
)
worst = query(
    "select obs_date, max_aqi, aqi_category, site, county from main.mart_air_worst_days"
)
sites = query(
    "select site, county, latitude, longitude, avg_aqi, max_aqi, day_count from main.mart_air_sites"
)
monthly = query(
    "select obs_month, pollutant, avg_aqi, max_aqi, reading_count from main.mart_air_monthly order by obs_month"
)

# --- KPIs ---
total_days = int(categories["day_count"].sum())
good_mod = int(
    categories.loc[categories["aqi_category"].isin(["Good", "Moderate"]), "day_count"].sum()
)
worst_row = worst.iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Days measured", f"{total_days:,}")
c2.metric("Good or Moderate", f"{good_mod / total_days * 100:.0f}%")
c3.metric("Worst day (AQI)", f"{int(worst_row.max_aqi)}",
          worst_row.obs_date.strftime("%b %-d, %Y"), delta_color="off")
c4.metric("Monitors", f"{len(sites)}")

st.divider()

# --- Category distribution ---
st.subheader("Most days the air is clean")
st.caption("Metro days by their worst PM2.5 reading, 2019-present.")
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
st.altair_chart(cat_chart, width="stretch")

# --- Monthly peak AQI (the smoke seasons) ---
st.subheader("When the smoke rolls in")
st.caption(
    "Peak AQI recorded each month. The tall spikes are wildfire smoke "
    "(Sept 2020, Oct 2022); the Ozone bump tracks summer heat."
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
st.altair_chart(peak_chart, width="stretch")

# --- Monitor map ---
st.subheader("Monitors across the metro")
st.caption("Each point is a PM2.5 monitor, sized and colored by its average AQI.")


def _aqi_color(aqi: float) -> list[int]:
    if aqi <= 50:
        return [46, 204, 113, 200]
    if aqi <= 100:
        return [241, 196, 15, 200]
    return [231, 126, 34, 200]


sites = sites.copy()
sites["color"] = sites["avg_aqi"].apply(_aqi_color)
st.pydeck_chart(
    pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=sites["latitude"].mean(),
            longitude=sites["longitude"].mean(),
            zoom=8,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=sites,
                get_position="[longitude, latitude]",
                get_fill_color="color",
                get_radius="avg_aqi * 40",
                pickable=True,
            )
        ],
        tooltip={"text": "{site}\n{county} County · avg AQI {avg_aqi}"},
    )
)

# --- Worst days ---
st.subheader("The worst air days on record")
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

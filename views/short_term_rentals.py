"""Seattle short-term rental licenses — status, property type, and where they're located."""

import altair as alt
import pydeck as pdk
import streamlit as st

from app_db import query

st.title("🏠 Short-Term Rentals")
st.caption(
    "City of Seattle short-term rental (STR) licenses. "
    "Explore license status, property types, and where licensed rentals are located."
)

# --- KPIs ---
total = query("select sum(license_count) as licenses from main.mart_str_by_status")
active = query(
    "select license_count from main.mart_str_by_status where licensestatus = 'Active'"
)
mapped = query("select count(*) as mapped from main.mart_str_map")

active_count = int(active["license_count"][0]) if len(active) else 0

c1, c2, c3 = st.columns(3)
c1.metric("Total licenses", f"{int(total['licenses'][0]):,}")
c2.metric("Active licenses", f"{active_count:,}")
c3.metric("Mapped licenses", f"{int(mapped['mapped'][0]):,}")

st.divider()

# --- By status ---
by_status = query(
    """
    select licensestatus, license_count
    from main.mart_str_by_status
    order by license_count desc
    """
)
st.subheader("Licenses by status")
status_chart = (
    alt.Chart(by_status)
    .mark_bar(color="#ff8c00")
    .encode(
        x=alt.X("license_count:Q", title="Licenses"),
        y=alt.Y("licensestatus:N", sort="-x", title=None),
        tooltip=[
            "licensestatus",
            alt.Tooltip("license_count:Q", title="Licenses", format=","),
        ],
    )
)
st.altair_chart(status_chart, width="stretch")

# --- By property type ---
by_type = query(
    """
    select propertytype, license_count
    from main.mart_str_by_type
    order by license_count desc
    limit 15
    """
)
st.subheader("Licenses by property type")
type_chart = (
    alt.Chart(by_type)
    .mark_bar(color="#3f88c5")
    .encode(
        x=alt.X("license_count:Q", title="Licenses"),
        y=alt.Y("propertytype:N", sort="-x", title=None),
        tooltip=[
            "propertytype",
            alt.Tooltip("license_count:Q", title="Licenses", format=","),
        ],
    )
)
st.altair_chart(type_chart, width="stretch")

# --- By region ---
by_region = query(
    """
    select geographicregion, license_count
    from main.mart_str_by_region
    order by license_count desc
    limit 15
    """
)
st.subheader("Licenses by geographic region")
region_chart = (
    alt.Chart(by_region)
    .mark_bar(color="#2e8b57")
    .encode(
        x=alt.X("license_count:Q", title="Licenses"),
        y=alt.Y("geographicregion:N", sort="-x", title=None),
        tooltip=[
            "geographicregion",
            alt.Tooltip("license_count:Q", title="Licenses", format=","),
        ],
    )
)
st.altair_chart(region_chart, width="stretch")

st.divider()

# --- Where licensed rentals are (PyDeck) ---
st.subheader("Where licensed short-term rentals are located")
st.caption("Geocoded STR licenses. Each point is one licensed rental.")
points = query(
    """
    select licenseid, licensestatus, propertytype, latitude, longitude
    from main.mart_str_map
    """
)
center_lat = float(points["latitude"].mean())
center_lon = float(points["longitude"].mean())
st.pydeck_chart(
    pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=center_lat, longitude=center_lon, zoom=10
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=points,
                get_position="[longitude, latitude]",
                get_fill_color="[255, 140, 0, 140]",
                get_radius=60,
                pickable=True,
            )
        ],
        tooltip={"text": "{propertytype}\n{licensestatus}"},
    )
)

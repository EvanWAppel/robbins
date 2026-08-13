"""Seattle parks — the Parks & Recreation system, mapped and sized.

Sourced from ArcGIS (like Public Art) — the boundary layer gives one point and
an acreage per park. The system is mostly small neighborhood parks with a few
big flagships (Discovery, Magnuson, Seward). The "water" flag is name-derived:
the boundary layer has no amenity data, so we flag parks whose name references
water — approximate, but it lights up Seattle's waterfront character.
"""

import altair as alt
import pydeck as pdk
import streamlit as st

from app_db import query

st.title("🌲 Parks")
st.caption(
    "Seattle Parks & Recreation's ~500 parks, sized by acreage and located from "
    "the ArcGIS boundary layer. Parks whose *name* references water (beaches, "
    "lakes, waterfronts) are flagged — a rough proxy, since the layer carries no "
    "amenity attributes."
)

points = query(
    "select name, area_acres, latitude, longitude, is_water_name from main.mart_parks_points"
)
bands = query(
    "select size_band, park_count, sort_order from main.mart_parks_size_bands order by sort_order"
)
largest = query(
    "select name, area_acres, is_water_name from main.mart_parks_largest"
)

# --- KPIs ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Parks", f"{len(points):,}")
c2.metric("Total acreage", f"{points['area_acres'].sum():,.0f}")
c3.metric("Largest park", f"{largest.iloc[0]['area_acres']:,.0f} ac",
          largest.iloc[0]["name"].title(), delta_color="off")
c4.metric("Water-name parks", f"{int(points['is_water_name'].sum()):,}")

st.divider()

# --- Size distribution ---
st.subheader("A system of small parks and a few giants")
st.caption("Parks by size band.")
band_chart = (
    alt.Chart(bands)
    .mark_bar(color="#27ae60")
    .encode(
        x=alt.X("park_count:Q", title="Parks"),
        y=alt.Y("size_band:N", sort=alt.EncodingSortField("sort_order"), title=None),
        tooltip=[
            alt.Tooltip("size_band:N", title="Size"),
            alt.Tooltip("park_count:Q", title="Parks"),
        ],
    )
)
st.altair_chart(band_chart, width="stretch")

# --- Map ---
st.subheader("Every park on the map")
st.caption("Point size scales with acreage; blue points are water-name parks.")
points = points.copy()
points["color"] = points["is_water_name"].map(
    lambda w: [41, 128, 185, 200] if w else [39, 174, 96, 160]
)
# Radius from acreage, with a floor so tiny parks stay visible and a cap so the
# flagships don't swallow the map.
points["radius"] = points["area_acres"].clip(lower=1, upper=300) ** 0.5 * 40
st.pydeck_chart(
    pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=points["latitude"].mean(),
            longitude=points["longitude"].mean(),
            zoom=10.5,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=points,
                get_position="[longitude, latitude]",
                get_fill_color="color",
                get_radius="radius",
                pickable=True,
            )
        ],
        tooltip={"text": "{name}\n{area_acres} acres"},
    )
)

# --- Largest parks ---
st.subheader("The biggest parks")
largest_display = largest.assign(name=largest["name"].str.title()).rename(
    columns={"name": "Park", "area_acres": "Acres", "is_water_name": "Water name"}
)
st.dataframe(largest_display, width="stretch", hide_index=True)

# --- Browse ---
st.subheader("Find a park")
search = st.text_input("Filter by name", "")
shown = points[["name", "area_acres", "is_water_name"]].assign(
    name=points["name"].str.title()
)
if search:
    shown = shown[shown["name"].str.contains(search, case=False, na=False)]
shown = shown.rename(
    columns={"name": "Park", "area_acres": "Acres", "is_water_name": "Water name"}
)
st.dataframe(shown, width="stretch", hide_index=True)

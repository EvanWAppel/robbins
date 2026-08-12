"""Seattle public art — the city's Office of Arts & Culture collection, mapped."""

import altair as alt
import pydeck as pdk
import streamlit as st

from app_db import query

st.title("🎨 Public Art")
st.caption(
    "The City of Seattle's public art collection (Office of Arts & Culture). "
    "This page is sourced from ArcGIS, not Socrata — the app's second ingestion "
    "pattern."
)

# --- KPIs ---
by_type = query(
    "select classification, artwork_count from main.mart_art_by_type order by artwork_count desc"
)
points = query(
    """
    select title, artist, classification, medium, dated, location, latitude, longitude
    from main.mart_art_points
    """
)
c1, c2, c3 = st.columns(3)
c1.metric("Artworks", f"{int(by_type['artwork_count'].sum()):,}")
c2.metric("Distinct artists", f"{points['artist'].nunique():,}")
c3.metric("Classifications", f"{by_type['classification'].nunique():,}")

st.divider()

# --- By classification ---
st.subheader("Artworks by classification")
type_chart = (
    alt.Chart(by_type.head(15))
    .mark_bar(color="#8e44ad")
    .encode(
        x=alt.X("artwork_count:Q", title="Artworks"),
        y=alt.Y("classification:N", sort="-x", title=None),
        tooltip=[
            "classification",
            alt.Tooltip("artwork_count:Q", title="Artworks", format=","),
        ],
    )
)
st.altair_chart(type_chart, width="stretch")

# --- Map ---
st.subheader("Where the art is")
st.caption("Each point is one artwork. Hover for the title and artist.")
st.pydeck_chart(
    pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=points["latitude"].mean(),
            longitude=points["longitude"].mean(),
            zoom=11,
            pitch=0,
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=points,
                get_position="[longitude, latitude]",
                get_fill_color=[142, 68, 173, 180],
                get_radius=80,
                pickable=True,
            )
        ],
        tooltip={"text": "{title}\n{artist} · {classification}"},
    )
)

# --- Browse ---
st.subheader("Browse the collection")
search = st.text_input("Filter by title or artist", "")
shown = points[["title", "artist", "classification", "medium", "dated", "location"]]
if search:
    mask = shown["title"].str.contains(search, case=False, na=False) | shown[
        "artist"
    ].str.contains(search, case=False, na=False)
    shown = shown[mask]
st.dataframe(shown, width="stretch", hide_index=True)

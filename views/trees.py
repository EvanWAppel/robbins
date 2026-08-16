"""Seattle's street trees — SDOT's ~212k-tree inventory by species and place.

Sourced from ArcGIS (like Parks and Public Art). SDOT records each managed
street tree with its scientific name, condition, and — for many — a planting
date. The map is a random sample; charts use the full inventory.
"""

import altair as alt
import pydeck as pdk
import streamlit as st

from app_db import query

st.title("🌳 Street Trees")
st.caption(
    "SDOT's active street-tree inventory — the trees the city manages in the "
    "public right-of-way. Points on the map are a random sample; charts use the "
    "full ~212k-tree dataset."
)

# --- KPIs ---
summary = query("select * from main.mart_trees_summary")
s = summary.iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Street trees", f"{int(s['total_trees']):,}")
c2.metric("Species", f"{int(s['distinct_species']):,}")
c3.metric("Genera", f"{int(s['distinct_genera']):,}")
c4.metric("Heritage trees", f"{int(s['heritage_trees']):,}")

st.divider()

# --- Top species + genera ---
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Most common species")
    species = query(
        """
        select scientific_name, tree_count
        from main.mart_trees_by_species
        order by tree_count desc
        limit 15
        """
    )
    species_chart = (
        alt.Chart(species)
        .mark_bar(color="#27ae60")
        .encode(
            x=alt.X("tree_count:Q", title="Trees"),
            y=alt.Y("scientific_name:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("scientific_name:N", title="Species"),
                alt.Tooltip("tree_count:Q", title="Trees", format=","),
            ],
        )
    )
    st.altair_chart(species_chart, width="stretch")
with col_b:
    st.subheader("Most common genera")
    genera = query(
        """
        select genus, tree_count
        from main.mart_trees_by_genus
        order by tree_count desc
        limit 15
        """
    )
    genera_chart = (
        alt.Chart(genera)
        .mark_bar(color="#16a085")
        .encode(
            x=alt.X("tree_count:Q", title="Trees"),
            y=alt.Y("genus:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("genus:N", title="Genus"),
                alt.Tooltip("tree_count:Q", title="Trees", format=","),
            ],
        )
    )
    st.altair_chart(genera_chart, width="stretch")

# --- Planting over time ---
planted = query(
    "select plant_year, tree_count from main.mart_trees_planted_by_year order by 1"
)
st.subheader("Recorded plantings by year")
st.caption(
    "Only trees with a recorded planting date (a portion of the inventory) — a "
    "rough view of the street-tree program's pace over time."
)
planted_chart = (
    alt.Chart(planted)
    .mark_area(line={"color": "#27ae60"}, color="#a9dfbf", opacity=0.6)
    .encode(
        x=alt.X("plant_year:O", title=None),
        y=alt.Y("tree_count:Q", title="Trees planted"),
        tooltip=[
            alt.Tooltip("plant_year:O", title="Year"),
            alt.Tooltip("tree_count:Q", title="Trees", format=","),
        ],
    )
)
st.altair_chart(planted_chart, width="stretch")

# --- Condition ---
condition = query(
    "select condition, tree_count from main.mart_trees_by_condition order by tree_count desc"
)
st.subheader("Assessed condition")
st.caption(
    "Condition is only recorded for a small share of the inventory — most trees "
    "are not (yet) assessed, which is itself part of the data story."
)
condition_chart = (
    alt.Chart(condition)
    .mark_bar(color="#2ecc71")
    .encode(
        x=alt.X("tree_count:Q", title="Trees"),
        y=alt.Y("condition:N", sort="-x", title=None),
        tooltip=[
            alt.Tooltip("condition:N", title="Condition"),
            alt.Tooltip("tree_count:Q", title="Trees", format=","),
        ],
    )
)
st.altair_chart(condition_chart, width="stretch")

# --- Map ---
st.subheader("Where the trees are")
st.caption(
    "A random sample of ~15k trees, binned into a hex grid. Taller/brighter hexes "
    "have more street trees — the leafy neighborhoods stand out."
)
sample = query(
    "select latitude, longitude from main.mart_trees_map_sample"
)
st.pydeck_chart(
    pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=sample["latitude"].mean(),
            longitude=sample["longitude"].mean(),
            zoom=10.5,
            pitch=35,
        ),
        layers=[
            pdk.Layer(
                "HexagonLayer",
                data=sample,
                get_position=["longitude", "latitude"],
                radius=200,
                elevation_scale=4,
                elevation_range=[0, 600],
                extruded=True,
                pickable=True,
                coverage=0.85,
                color_range=[
                    [237, 248, 233],
                    [199, 233, 192],
                    [161, 217, 155],
                    [116, 196, 118],
                    [49, 163, 84],
                    [0, 109, 44],
                ],
            )
        ],
    )
)

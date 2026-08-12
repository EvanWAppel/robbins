"""Seattle Fire 911 dispatch calls — patterns across type, time, and place."""

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

from app_db import query

st.title("🚒 Fire 911 Calls")
st.caption(
    "Seattle Fire Department 911 dispatches. Points on the map are a random "
    "sample; charts use the full dataset."
)

# --- KPIs ---
kpi = query(
    """
    select
        sum(call_count)                             as total_calls,
        (select count(*) from main.mart_fire_by_type) as distinct_types
    from main.mart_fire_monthly
    """
)
span = query(
    """
    select min(call_month) as first_month, max(call_month) as last_month
    from main.mart_fire_monthly
    """
)
c1, c2, c3 = st.columns(3)
c1.metric("Dispatched calls", f"{int(kpi['total_calls'][0]):,}")
c2.metric("Call types", f"{int(kpi['distinct_types'][0]):,}")
c3.metric(
    "Period",
    f"{span['first_month'][0]:%b %Y} – {span['last_month'][0]:%b %Y}",
)

st.divider()

# --- Monthly trend ---
monthly = query(
    "select call_month, call_count from main.mart_fire_monthly order by 1"
)
st.subheader("Calls per month")
trend = (
    alt.Chart(monthly)
    .mark_line(point=True, color="#f26419")
    .encode(
        x=alt.X("call_month:T", title=None),
        y=alt.Y("call_count:Q", title="Calls"),
        tooltip=[
            alt.Tooltip("call_month:T", title="Month"),
            alt.Tooltip("call_count:Q", title="Calls", format=","),
        ],
    )
)
st.altair_chart(trend, width="stretch")

# --- Top call types ---
types = query(
    """
    select call_type, call_count
    from main.mart_fire_by_type
    order by call_count desc
    limit 15
    """
)
st.subheader("Most common call types")
types_chart = (
    alt.Chart(types)
    .mark_bar(color="#f26419")
    .encode(
        x=alt.X("call_count:Q", title="Calls"),
        y=alt.Y("call_type:N", sort="-x", title=None),
        tooltip=[
            "call_type",
            alt.Tooltip("call_count:Q", title="Calls", format=","),
        ],
    )
)
st.altair_chart(types_chart, width="stretch")

# --- Hour x weekday heatmap ---
heat = query(
    "select weekday, hour_of_day, call_count from main.mart_fire_by_hour_weekday"
)
weekday_order = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
st.subheader("When calls come in")
st.caption("Dispatched calls by hour of day and day of week.")
heatmap = (
    alt.Chart(heat)
    .mark_rect()
    .encode(
        x=alt.X("hour_of_day:O", title="Hour of day"),
        y=alt.Y("weekday:N", sort=weekday_order, title=None),
        color=alt.Color(
            "call_count:Q", title="Calls", scale=alt.Scale(scheme="oranges")
        ),
        tooltip=[
            "weekday",
            "hour_of_day",
            alt.Tooltip("call_count:Q", title="Calls", format=","),
        ],
    )
)
st.altair_chart(heatmap, width="stretch")

# --- Map (sampled) ---
st.subheader("Where calls happen")
st.caption(
    "A random sample of ~12k geolocated calls, binned into a hex grid over "
    "the city. Click a hexagon to see the calls there."
)
sample = query(
    """
    select latitude, longitude, call_type, address
    from main.mart_fire_map_sample
    """
)
layer = pdk.Layer(
    "HexagonLayer",
    id="hex",
    data=sample,
    get_position=["longitude", "latitude"],
    radius=250,
    elevation_scale=5,
    elevation_range=[0, 700],
    extruded=True,
    pickable=True,
    auto_highlight=True,
    coverage=0.8,
)
view_state = pdk.ViewState(
    latitude=sample["latitude"].mean(),
    longitude=sample["longitude"].mean(),
    zoom=10,
    pitch=35,
)
deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    # Carto Positron: a light basemap with clear roads and labels, no API token.
    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
)
event = st.pydeck_chart(
    deck, on_select="rerun", selection_mode="single-object", key="fire_hex"
)

# --- Data card for the clicked hexagon ---
picked = []
if event and getattr(event, "selection", None):
    picked = (event.selection.get("objects") or {}).get("hex", [])
if picked:
    obj = picked[0]
    points = obj.get("points", [])
    # deck.gl wraps each binned record as {"source": <row>}; fall back to the row.
    rows = pd.DataFrame([p.get("source", p) for p in points]) if points else pd.DataFrame()
    count = len(rows) if not rows.empty else int(obj.get("elevationValue", 0))
    st.markdown(f"### 📍 {count:,} calls in this hexagon")
    if not rows.empty:
        top = (
            rows["call_type"].value_counts().head(8).rename_axis("Call type")
            .reset_index(name="Calls")
        )
        c_a, c_b = st.columns([1, 1])
        with c_a:
            st.caption("Top call types here")
            st.dataframe(top, width="stretch", hide_index=True)
        with c_b:
            st.caption("Sample of calls")
            st.dataframe(
                rows[["call_type", "address"]].head(12),
                width="stretch",
                hide_index=True,
            )
else:
    st.caption("👆 No hexagon selected — click one on the map above.")

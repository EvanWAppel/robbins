"""SPD crime offenses — recent-year patterns across type, time, and place."""

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

from app_db import query

st.title("🚨 Crime")
st.caption(
    "Seattle Police Department reported offenses (recent years). Points on the "
    "map are a random sample; charts use the full recent-years dataset."
)

# --- KPIs ---
kpi = query(
    """
    select
        sum(incident_count)                              as total_offenses,
        (select count(*) from main.mart_crime_by_category) as distinct_types
    from main.mart_crime_monthly
    """
)
span = query(
    """
    select min(crime_month) as first_month, max(crime_month) as last_month
    from main.mart_crime_monthly
    """
)
c1, c2, c3 = st.columns(3)
c1.metric("Reported offenses", f"{int(kpi['total_offenses'][0]):,}")
c2.metric("Offense categories", f"{int(kpi['distinct_types'][0]):,}")
c3.metric(
    "Period",
    f"{span['first_month'][0]:%b %Y} – {span['last_month'][0]:%b %Y}",
)

st.divider()

# --- Monthly trend ---
monthly = query(
    "select crime_month, incident_count from main.mart_crime_monthly order by 1"
)
st.subheader("Offenses per month")
trend = (
    alt.Chart(monthly)
    .mark_line(point=True, color="#e4572e")
    .encode(
        x=alt.X("crime_month:T", title=None),
        y=alt.Y("incident_count:Q", title="Offenses"),
        tooltip=[
            alt.Tooltip("crime_month:T", title="Month"),
            alt.Tooltip("incident_count:Q", title="Offenses", format=","),
        ],
    )
)
st.altair_chart(trend, width="stretch")

# --- Top offense categories ---
types = query(
    """
    select offense_category, incident_count
    from main.mart_crime_by_category
    order by incident_count desc
    limit 15
    """
)
st.subheader("Most common offense categories")
types_chart = (
    alt.Chart(types)
    .mark_bar(color="#e4572e")
    .encode(
        x=alt.X("incident_count:Q", title="Offenses"),
        y=alt.Y("offense_category:N", sort="-x", title=None),
        tooltip=[
            "offense_category",
            alt.Tooltip("incident_count:Q", title="Offenses", format=","),
        ],
    )
)
st.altair_chart(types_chart, width="stretch")

# --- Hour x weekday heatmap ---
heat = query(
    "select weekday, hour_of_day, incident_count from main.mart_crime_by_hour_weekday"
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
st.subheader("When offenses are reported")
st.caption("Reported offenses by hour of day and day of week.")
heatmap = (
    alt.Chart(heat)
    .mark_rect()
    .encode(
        x=alt.X("hour_of_day:O", title="Hour of day"),
        y=alt.Y("weekday:N", sort=weekday_order, title=None),
        color=alt.Color(
            "incident_count:Q", title="Offenses", scale=alt.Scale(scheme="reds")
        ),
        tooltip=[
            "weekday",
            "hour_of_day",
            alt.Tooltip("incident_count:Q", title="Offenses", format=","),
        ],
    )
)
st.altair_chart(heatmap, width="stretch")

# --- Map (sampled) ---
st.subheader("Where offenses happen")
st.caption(
    "A random sample of ~12k geolocated offenses, binned into a hex grid over "
    "the city. Click a hexagon to see the offenses there."
)
sample = query(
    """
    select latitude, longitude, offense_category, offense_description, address
    from main.mart_crime_map_sample
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
    deck, on_select="rerun", selection_mode="single-object", key="crime_hex"
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
    st.markdown(f"### 📍 {count:,} offenses in this hexagon")
    if not rows.empty:
        top = (
            rows["offense_category"].value_counts().head(8).rename_axis("Category")
            .reset_index(name="Offenses")
        )
        c_a, c_b = st.columns([1, 1])
        with c_a:
            st.caption("Top categories here")
            st.dataframe(top, width="stretch", hide_index=True)
        with c_b:
            st.caption("Sample of offenses")
            st.dataframe(
                rows[["offense_description", "address"]].head(12),
                width="stretch",
                hide_index=True,
            )
else:
    st.caption("👆 No hexagon selected — click one on the map above.")

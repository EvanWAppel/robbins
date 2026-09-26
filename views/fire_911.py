"""Seattle Fire 911 dispatch calls — patterns across type, time, and place."""

import altair as alt
import streamlit as st

import ui
from app_db import query
from ui import choropleth_legend, neighborhood_choropleth

st.title("Fire 911 Calls")
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
    .mark_line(point=True, color="#b4503f")
    .encode(
        x=alt.X("call_month:T", title=None),
        y=alt.Y("call_count:Q", title="Calls"),
        tooltip=[
            alt.Tooltip("call_month:T", title="Month"),
            alt.Tooltip("call_count:Q", title="Calls", format=","),
        ],
    )
)
ui.chart(trend, width="stretch")

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
    .mark_bar(color="#b4503f")
    .encode(
        x=alt.X("call_count:Q", title="Calls"),
        y=alt.Y("call_type:N", sort="-x", title=None),
        tooltip=[
            "call_type",
            alt.Tooltip("call_count:Q", title="Calls", format=","),
        ],
    )
)
ui.chart(types_chart, width="stretch")

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
ui.chart(heatmap, width="stretch")

# --- Neighborhood choropleth ---
st.subheader("Where calls concentrate")
st.caption(
    "Fire 911 dispatches per square mile by SPD neighborhood (Micro Community "
    "Policing Plan areas). Darker = denser. Hover a neighborhood for its totals."
)
nb = query(
    """
    select neighborhood, incident_count, incidents_per_sq_mile,
           area_sq_miles, rings_json
    from main.mart_fire_911_by_neighborhood
    """
)
st.pydeck_chart(neighborhood_choropleth(nb, unit="calls / sq mi"))
st.html(choropleth_legend(nb, "calls / sq mi"))

# --- Densest neighborhoods ---
st.caption("Densest neighborhoods, by calls per square mile")
top_nb = nb.sort_values("incidents_per_sq_mile", ascending=False).head(12)
st.dataframe(
    {
        "Neighborhood": top_nb["neighborhood"].str.title(),
        "Calls": top_nb["incident_count"].map("{:,.0f}".format),
        "Per sq mi": top_nb["incidents_per_sq_mile"].map("{:,.0f}".format),
    },
    width="stretch",
    hide_index=True,
)

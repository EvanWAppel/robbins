"""SPD crime offenses — recent-year patterns across type, time, and place."""

import altair as alt
import streamlit as st

from app_db import query
from ui import choropleth_legend, neighborhood_choropleth

st.title("Crime")
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
    .mark_line(point=True, color="#b4503f")
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
    .mark_bar(color="#b4503f")
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

# --- Neighborhood choropleth ---
st.subheader("Where offenses concentrate")
st.caption(
    "Reported offenses per square mile by SPD neighborhood (Micro Community "
    "Policing Plan areas). Darker = denser. Hover a neighborhood for its totals."
)
nb = query(
    """
    select neighborhood, incident_count, incidents_per_sq_mile,
           area_sq_miles, rings_json
    from main.mart_crime_by_neighborhood
    """
)
st.pydeck_chart(neighborhood_choropleth(nb, unit="offenses / sq mi"))
st.html(choropleth_legend(nb, "offenses / sq mi"))

# --- Densest neighborhoods ---
st.caption("Densest neighborhoods, by offenses per square mile")
top_nb = nb.sort_values("incidents_per_sq_mile", ascending=False).head(12)
st.dataframe(
    {
        "Neighborhood": top_nb["neighborhood"].str.title(),
        "Offenses": top_nb["incident_count"].map("{:,.0f}".format),
        "Per sq mi": top_nb["incidents_per_sq_mile"].map("{:,.0f}".format),
    },
    width="stretch",
    hide_index=True,
)

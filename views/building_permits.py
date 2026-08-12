"""Seattle DCI building permits — volume, valuation, and where they're issued."""

import altair as alt
import pydeck as pdk
import streamlit as st

from app_db import query

st.title("🏗️ Building Permits")
st.caption(
    "City of Seattle (DCI) building-permit history with estimated project costs. "
    "Great for spotting the city's building cycles and where construction lands."
)

# --- KPIs ---
kpi = query(
    """
    select
        sum(permit_count)     as permits,
        sum(total_valuation)  as valuation
    from main.mart_permits_monthly
    """
)
span = query(
    "select min(issue_month) as first, max(issue_month) as last from main.mart_permits_monthly"
)
c1, c2, c3 = st.columns(3)
c1.metric("Permits issued", f"{int(kpi['permits'][0]):,}")
c2.metric("Total est. project cost", f"${kpi['valuation'][0] / 1e9:.1f}B")
c3.metric("Period", f"{span['first'][0]:%Y} – {span['last'][0]:%Y}")

st.divider()

# --- Monthly permits + valuation ---
monthly = query(
    """
    select issue_month, permit_count, total_valuation
    from main.mart_permits_monthly
    order by 1
    """
)
st.subheader("Permits issued per month")
permits_line = (
    alt.Chart(monthly)
    .mark_area(color="#3f88c5", opacity=0.7)
    .encode(
        x=alt.X("issue_month:T", title=None),
        y=alt.Y("permit_count:Q", title="Permits"),
        tooltip=[
            alt.Tooltip("issue_month:T", title="Month"),
            alt.Tooltip("permit_count:Q", title="Permits", format=","),
        ],
    )
)
st.altair_chart(permits_line, width="stretch")

st.subheader("Estimated project cost per month")
val_line = (
    alt.Chart(monthly)
    .mark_line(color="#2e8b57")
    .encode(
        x=alt.X("issue_month:T", title=None),
        y=alt.Y("total_valuation:Q", title="Est. cost ($)", axis=alt.Axis(format="~s")),
        tooltip=[
            alt.Tooltip("issue_month:T", title="Month"),
            alt.Tooltip("total_valuation:Q", title="Est. cost", format="$,.0f"),
        ],
    )
)
st.altair_chart(val_line, width="stretch")

# --- By permit class ---
by_class = query(
    """
    select permit_class, permit_count, total_valuation
    from main.mart_permits_by_class
    order by permit_count desc
    limit 15
    """
)
st.subheader("Permits by class")
class_chart = (
    alt.Chart(by_class)
    .mark_bar(color="#3f88c5")
    .encode(
        x=alt.X("permit_count:Q", title="Permits"),
        y=alt.Y("permit_class:N", sort="-x", title=None),
        tooltip=[
            "permit_class",
            alt.Tooltip("permit_count:Q", title="Permits", format=","),
            alt.Tooltip("total_valuation:Q", title="Est. cost", format="$,.0f"),
        ],
    )
)
st.altair_chart(class_chart, width="stretch")
st.dataframe(by_class, width="stretch", hide_index=True)

st.divider()

# --- Where recent permits land (PyDeck) ---
st.subheader("Where recent permits are issued")
st.caption("Most recent 5,000 geocoded permits. Taller/brighter = more permits nearby.")
points = query(
    """
    select latitude, longitude
    from main.mart_permits_map_sample
    """
)
st.pydeck_chart(
    pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(
            latitude=47.62, longitude=-122.33, zoom=10, pitch=40
        ),
        layers=[
            pdk.Layer(
                "HexagonLayer",
                data=points,
                get_position="[longitude, latitude]",
                radius=250,
                elevation_scale=8,
                extruded=True,
                coverage=0.9,
                pickable=True,
            )
        ],
        tooltip={"text": "{elevationValue} permits"},
    )
)

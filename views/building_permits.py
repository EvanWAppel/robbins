"""Seattle DCI building permits — volume, valuation, and where they're issued."""

import altair as alt
import pydeck as pdk
import streamlit as st

import ui
from app_db import query

st.title("Building Permits")
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
    .mark_area(color="#4f88a6", opacity=0.7)
    .encode(
        x=alt.X("issue_month:T", title=None),
        y=alt.Y("permit_count:Q", title="Permits"),
        tooltip=[
            alt.Tooltip("issue_month:T", title="Month"),
            alt.Tooltip("permit_count:Q", title="Permits", format=","),
        ],
    )
)
ui.chart(permits_line, width="stretch")

st.subheader("Estimated project cost per month")
val_line = (
    alt.Chart(monthly)
    .mark_line(color="#2f6285")
    .encode(
        x=alt.X("issue_month:T", title=None),
        y=alt.Y("total_valuation:Q", title="Est. cost ($)", axis=alt.Axis(format="~s")),
        tooltip=[
            alt.Tooltip("issue_month:T", title="Month"),
            alt.Tooltip("total_valuation:Q", title="Est. cost", format="$,.0f"),
        ],
    )
)
ui.chart(val_line, width="stretch")

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
    .mark_bar(color="#4f88a6")
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
ui.chart(class_chart, width="stretch")
st.dataframe(by_class, width="stretch", hide_index=True)

st.divider()

# --- Where recent permits land (PyDeck) ---
st.subheader("Where recent permits are issued")
st.caption(
    "Each dot is one of the most recent 5,000 geocoded permits. "
    "Zoom in and hover for the address, permit type, and issue date. "
    "Multiple permits at the same location may overlap."
)
points = query(
    """
    select latitude, longitude, permit_number,
           coalesce(address, 'Address unavailable') as address,
           coalesce(permit_type_desc, 'Type unavailable') as permit_type_desc,
           cast(issue_date as varchar) as issue_date
    from main.mart_permits_map_sample
    """
)
st.pydeck_chart(
    pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=47.62, longitude=-122.33, zoom=10.5, pitch=0
        ),
        layers=[
            pdk.Layer(
                "ScatterplotLayer",
                data=points,
                get_position="[longitude, latitude]",
                get_radius=25,
                radius_min_pixels=3,
                radius_max_pixels=8,
                get_fill_color=[79, 136, 166, 160],
                pickable=True,
            )
        ],
        tooltip={
            "text": "{address}\n{permit_type_desc}\nPermit: {permit_number}\nIssued: {issue_date}"
        },
    )
)

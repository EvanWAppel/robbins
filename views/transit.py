"""Puget Sound transit ridership — the pandemic collapse, recovery, and rail's rise.

Monthly unlinked passenger trips from the FTA's National Transit Database, curated
to the metro's operators (King County Metro, Sound Transit, Community Transit,
Pierce Transit, Everett Transit, Seattle Streetcar). Ferries have their own page.
"""

import altair as alt
import streamlit as st

from app_db import query

st.title("🚌 Transit Ridership")
st.caption(
    "Monthly boardings across Puget Sound transit agencies (FTA National Transit "
    "Database), 2015-present. Buses carry most riders; Sound Transit's Link light "
    "rail is the region's clearest growth story."
)

# --- KPIs ---
monthly = query(
    "select ridership_month, boardings from main.mart_transit_monthly order by 1"
)
latest = monthly.iloc[-1]
prepandemic_peak = monthly[monthly["ridership_month"] < "2020-03-01"]["boardings"].max()
recovery = 100 * latest["boardings"] / prepandemic_peak
rail = query(
    "select ridership_month, boardings from main.mart_transit_light_rail_monthly order by 1"
)
rail_growth = rail.iloc[-1]["boardings"] / rail.iloc[0]["boardings"]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest month", f"{latest['boardings'] / 1e6:.1f}M", f"{latest['ridership_month']:%b %Y}",
          delta_color="off")
c2.metric("Pre-pandemic peak", f"{prepandemic_peak / 1e6:.1f}M / mo")
c3.metric("Recovery vs. peak", f"{recovery:.0f}%")
c4.metric("Light rail growth", f"{rail_growth:.1f}×", "since 2015", delta_color="off")

st.divider()

# --- Monthly trend ---
st.subheader("Monthly boardings")
st.caption("The March 2020 collapse and the long climb back.")
trend = (
    alt.Chart(monthly)
    .mark_area(line={"color": "#8e44ad"}, color="#d7bde2", opacity=0.5)
    .encode(
        x=alt.X("ridership_month:T", title=None),
        y=alt.Y("boardings:Q", title="Boardings / month"),
        tooltip=[
            alt.Tooltip("ridership_month:T", title="Month"),
            alt.Tooltip("boardings:Q", title="Boardings", format=","),
        ],
    )
)
st.altair_chart(trend, width="stretch")

# --- Agency + mode ---
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Boardings by agency")
    agency = query(
        "select agency_label, boardings from main.mart_transit_by_agency order by boardings desc"
    )
    agency_chart = (
        alt.Chart(agency)
        .mark_bar(color="#8e44ad")
        .encode(
            x=alt.X("boardings:Q", title="Boardings (2015-present)"),
            y=alt.Y("agency_label:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("agency_label:N", title="Agency"),
                alt.Tooltip("boardings:Q", title="Boardings", format=","),
            ],
        )
    )
    st.altair_chart(agency_chart, width="stretch")
with col_b:
    st.subheader("Boardings by mode")
    mode = query(
        "select mode_label, boardings from main.mart_transit_by_mode order by boardings desc limit 8"
    )
    mode_chart = (
        alt.Chart(mode)
        .mark_bar(color="#a569bd")
        .encode(
            x=alt.X("boardings:Q", title="Boardings (2015-present)"),
            y=alt.Y("mode_label:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("mode_label:N", title="Mode"),
                alt.Tooltip("boardings:Q", title="Boardings", format=","),
            ],
        )
    )
    st.altair_chart(mode_chart, width="stretch")

# --- Light rail growth ---
st.subheader("Link light rail is pulling away")
st.caption(
    "Sound Transit's Link expanded north (Northgate, 2021) and east (2 Line, 2024), "
    "driving monthly light-rail boardings well past their pre-pandemic level — the "
    "opposite trajectory from bus ridership."
)
rail_chart = (
    alt.Chart(rail)
    .mark_line(color="#1abc9c", point=False)
    .encode(
        x=alt.X("ridership_month:T", title=None),
        y=alt.Y("boardings:Q", title="Light-rail boardings / month"),
        tooltip=[
            alt.Tooltip("ridership_month:T", title="Month"),
            alt.Tooltip("boardings:Q", title="Boardings", format=","),
        ],
    )
)
st.altair_chart(rail_chart, width="stretch")

"""Puget Sound ferry ridership — Washington State Ferries + the King County Water Taxi.

The stand-in for the (dropped) Tourism topic: ferries are a clean, machine-readable
proxy for Puget Sound travel, with strong summer seasonality. Monthly boardings from
the FTA National Transit Database; WSF is the largest ferry system in the U.S.
"""

import altair as alt
import streamlit as st

from app_db import query

st.title("⛴️ Ferry Ridership")
st.caption(
    "Monthly ferry boardings across Puget Sound (FTA National Transit Database), "
    "2015-present. Washington State Ferries dominates; ridership swells every summer "
    "— a useful proxy for regional travel and tourism."
)

# --- KPIs ---
annual = query(
    "select ridership_year, boardings, months_reported from main.mart_ferry_annual order by ridership_year"
)
full_years = annual[annual["months_reported"] == 12]
latest_full = full_years.iloc[-1]
operator = query(
    "select operator, boardings from main.mart_ferry_by_operator order by boardings desc"
)
wsf_share = 100 * operator.iloc[0]["boardings"] / operator["boardings"].sum()
seasonal = query(
    "select month_of_year, avg_boardings from main.mart_ferry_seasonal order by month_of_year"
)
peak_month = seasonal.loc[seasonal["avg_boardings"].idxmax(), "month_of_year"]
month_names = [
    "", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]

c1, c2, c3 = st.columns(3)
c1.metric(
    f"Boardings ({int(latest_full['ridership_year'])})",
    f"{latest_full['boardings'] / 1e6:.1f}M",
)
c2.metric("Washington State Ferries share", f"{wsf_share:.0f}%")
c3.metric("Busiest month", month_names[int(peak_month)])

st.divider()

# --- Monthly trend ---
monthly = query(
    "select ridership_month, boardings from main.mart_ferry_monthly order by 1"
)
st.subheader("Monthly ferry boardings")
st.caption("Seasonal peaks every summer, the 2020 pandemic collapse, and recovery.")
trend = (
    alt.Chart(monthly)
    .mark_area(line={"color": "#2980b9"}, color="#aed6f1", opacity=0.5)
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

# --- Seasonality + operator ---
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Summer swell")
    st.caption("Average boardings by calendar month.")
    seasonal = seasonal.assign(month=seasonal["month_of_year"].map(lambda m: month_names[int(m)]))
    seasonal_chart = (
        alt.Chart(seasonal)
        .mark_bar(color="#2980b9")
        .encode(
            x=alt.X("month:N", sort=month_names[1:], title=None),
            y=alt.Y("avg_boardings:Q", title="Avg boardings"),
            tooltip=[
                alt.Tooltip("month:N", title="Month"),
                alt.Tooltip("avg_boardings:Q", title="Avg boardings", format=",.0f"),
            ],
        )
    )
    st.altair_chart(seasonal_chart, width="stretch")
with col_b:
    st.subheader("By operator")
    st.caption("Washington State Ferries vs. the King County Water Taxi.")
    operator_chart = (
        alt.Chart(operator)
        .mark_bar(color="#5dade2")
        .encode(
            x=alt.X("boardings:Q", title="Boardings (2015-present)"),
            y=alt.Y("operator:N", sort="-x", title=None),
            tooltip=[
                alt.Tooltip("operator:N", title="Operator"),
                alt.Tooltip("boardings:Q", title="Boardings", format=","),
            ],
        )
    )
    st.altair_chart(operator_chart, width="stretch")

# --- Annual (full years only) ---
st.subheader("Annual boardings")
st.caption("Full calendar years only — the current partial year is omitted.")
annual_full = full_years.assign(year=full_years["ridership_year"].astype(int).astype(str))
annual_chart = (
    alt.Chart(annual_full)
    .mark_bar(color="#2980b9")
    .encode(
        x=alt.X("year:N", title=None),
        y=alt.Y("boardings:Q", title="Boardings / year"),
        tooltip=[
            alt.Tooltip("year:N", title="Year"),
            alt.Tooltip("boardings:Q", title="Boardings", format=","),
        ],
    )
)
st.altair_chart(annual_chart, width="stretch")

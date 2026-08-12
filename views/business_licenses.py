"""Seattle business license tax certificates — volume, industries, and ownership."""

import altair as alt
import streamlit as st

from app_db import query

st.title("📋 Business Licenses")
st.caption(
    "City of Seattle active business license tax certificates. "
    "A window into the local business mix — industries, ownership, and where firms register."
)

# --- KPIs ---
industries = query(
    """
    select naics_description, license_count
    from main.mart_licenses_by_industry
    order by license_count desc
    """
)
cities = query(
    """
    select city, license_count
    from main.mart_licenses_by_city
    order by license_count desc
    """
)
c1, c2, c3 = st.columns(3)
c1.metric("Active licenses", f"{int(industries['license_count'].sum()):,}")
c2.metric("Industries", f"{len(industries):,}")
c3.metric("Cities covered", f"{len(cities):,}")

st.divider()

# --- New licenses per month ---
monthly = query(
    """
    select license_month, license_count
    from main.mart_licenses_monthly
    order by 1
    """
)
st.subheader("New licenses per month")
monthly_line = (
    alt.Chart(monthly)
    .mark_line(color="#3f88c5")
    .encode(
        x=alt.X("license_month:T", title=None),
        y=alt.Y("license_count:Q", title="Licenses"),
        tooltip=[
            alt.Tooltip("license_month:T", title="Month"),
            alt.Tooltip("license_count:Q", title="Licenses", format=","),
        ],
    )
)
st.altair_chart(monthly_line, width="stretch")

# --- Top industries ---
top_industries = industries.head(15)
st.subheader("Top industries")
industry_chart = (
    alt.Chart(top_industries)
    .mark_bar(color="#3f88c5")
    .encode(
        x=alt.X("license_count:Q", title="Licenses"),
        y=alt.Y("naics_description:N", sort="-x", title=None),
        tooltip=[
            alt.Tooltip("naics_description:N", title="Industry"),
            alt.Tooltip("license_count:Q", title="Licenses", format=","),
        ],
    )
)
st.altair_chart(industry_chart, width="stretch")
st.dataframe(top_industries, width="stretch", hide_index=True)

# --- Ownership breakdown ---
ownership = query(
    """
    select ownership_type, license_count
    from main.mart_licenses_by_ownership
    order by license_count desc
    """
)
st.subheader("Ownership type")
ownership_chart = (
    alt.Chart(ownership)
    .mark_bar(color="#2e8b57")
    .encode(
        x=alt.X("license_count:Q", title="Licenses"),
        y=alt.Y("ownership_type:N", sort="-x", title=None),
        tooltip=[
            alt.Tooltip("ownership_type:N", title="Ownership"),
            alt.Tooltip("license_count:Q", title="Licenses", format=","),
        ],
    )
)
st.altair_chart(ownership_chart, width="stretch")

# --- Top cities ---
top_cities = cities.head(12)
st.subheader("Top cities")
city_chart = (
    alt.Chart(top_cities)
    .mark_bar(color="#3f88c5")
    .encode(
        x=alt.X("license_count:Q", title="Licenses"),
        y=alt.Y("city:N", sort="-x", title=None),
        tooltip=[
            alt.Tooltip("city:N", title="City"),
            alt.Tooltip("license_count:Q", title="Licenses", format=","),
        ],
    )
)
st.altair_chart(city_chart, width="stretch")

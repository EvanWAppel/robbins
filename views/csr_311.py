"""Seattle 311 — Find-It-Fix-It service requests across type, channel, and place.

Customer Service Requests are how residents report potholes, graffiti, abandoned
vehicles, illegal dumping and the like — increasingly through the Find-It-Fix-It
mobile app. Recent years only; the map is a random sample, charts use the full
recent-years dataset.
"""

import altair as alt
import streamlit as st

from app_db import query
from ui import choropleth_legend, neighborhood_choropleth

st.title("Service Requests")
st.caption(
    "Seattle Customer Service Requests (Find-It-Fix-It), 2020-present. Residents "
    "report potholes, graffiti, abandoned vehicles and more. Points on the map are "
    "a random sample; charts use the full recent-years dataset."
)

# --- KPIs ---
kpi = query(
    """
    select
        sum(request_count)                                as total_requests,
        (select count(*) from main.mart_csr_by_type)      as distinct_types
    from main.mart_csr_monthly
    """
)
span = query(
    """
    select min(request_month) as first_month, max(request_month) as last_month
    from main.mart_csr_monthly
    """
)
app_share = query(
    """
    select
        sum(case when method_received ilike '%find it fix it%' then request_count else 0 end)
            as app_requests,
        sum(request_count) as all_requests
    from main.mart_csr_by_method
    """
)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Requests", f"{int(kpi['total_requests'][0]):,}")
c2.metric("Request types", f"{int(kpi['distinct_types'][0]):,}")
c3.metric(
    "Period",
    f"{span['first_month'][0]:%b %Y} – {span['last_month'][0]:%b %Y}",
)
app_pct = 100 * app_share["app_requests"][0] / app_share["all_requests"][0]
c4.metric("Via Find-It-Fix-It app", f"{app_pct:.0f}%")

st.divider()

# --- Monthly trend ---
monthly = query(
    "select request_month, request_count from main.mart_csr_monthly order by 1"
)
st.subheader("Requests per month")
trend = (
    alt.Chart(monthly)
    .mark_line(point=True, color="#4f88a6")
    .encode(
        x=alt.X("request_month:T", title=None),
        y=alt.Y("request_count:Q", title="Requests"),
        tooltip=[
            alt.Tooltip("request_month:T", title="Month"),
            alt.Tooltip("request_count:Q", title="Requests", format=","),
        ],
    )
)
st.altair_chart(trend, width="stretch")

# --- Top request types ---
types = query(
    """
    select request_type, request_count
    from main.mart_csr_by_type
    order by request_count desc
    limit 15
    """
)
st.subheader("What residents report most")
types_chart = (
    alt.Chart(types)
    .mark_bar(color="#4f88a6")
    .encode(
        x=alt.X("request_count:Q", title="Requests"),
        y=alt.Y("request_type:N", sort="-x", title=None),
        tooltip=[
            "request_type",
            alt.Tooltip("request_count:Q", title="Requests", format=","),
        ],
    )
)
st.altair_chart(types_chart, width="stretch")

# --- Reporting channel + owning department ---
col_a, col_b = st.columns(2)
with col_a:
    st.subheader("How they report")
    method = query(
        """
        select method_received, request_count
        from main.mart_csr_by_method
        order by request_count desc
        limit 8
        """
    )
    method_chart = (
        alt.Chart(method)
        .mark_bar(color="#8fb3b5")
        .encode(
            x=alt.X("request_count:Q", title="Requests"),
            y=alt.Y("method_received:N", sort="-x", title=None),
            tooltip=[
                "method_received",
                alt.Tooltip("request_count:Q", title="Requests", format=","),
            ],
        )
    )
    st.altair_chart(method_chart, width="stretch")
with col_b:
    st.subheader("Who handles it")
    dept = query(
        """
        select department, request_count
        from main.mart_csr_by_department
        order by request_count desc
        limit 8
        """
    )
    dept_chart = (
        alt.Chart(dept)
        .mark_bar(color="#8fb3b5")
        .encode(
            x=alt.X("request_count:Q", title="Requests"),
            y=alt.Y("department:N", sort="-x", title=None),
            tooltip=[
                "department",
                alt.Tooltip("request_count:Q", title="Requests", format=","),
            ],
        )
    )
    st.altair_chart(dept_chart, width="stretch")

# --- Neighborhood choropleth ---
st.subheader("Where requests concentrate")
st.caption(
    "311 requests per square mile by SPD neighborhood (Micro Community Policing "
    "Plan areas). Darker = denser. Hover a neighborhood for its totals."
)
nb = query(
    """
    select neighborhood, incident_count, incidents_per_sq_mile,
           area_sq_miles, rings_json
    from main.mart_csr_311_by_neighborhood
    """
)
st.pydeck_chart(neighborhood_choropleth(nb, unit="requests / sq mi"))
st.html(choropleth_legend(nb, "requests / sq mi"))

# --- Densest neighborhoods ---
st.caption("Densest neighborhoods, by requests per square mile")
top_nb = nb.sort_values("incidents_per_sq_mile", ascending=False).head(12)
st.dataframe(
    {
        "Neighborhood": top_nb["neighborhood"].str.title(),
        "Requests": top_nb["incident_count"].map("{:,.0f}".format),
        "Per sq mi": top_nb["incidents_per_sq_mile"].map("{:,.0f}".format),
    },
    width="stretch",
    hide_index=True,
)

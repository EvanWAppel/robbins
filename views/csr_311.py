"""Seattle 311 — Find-It-Fix-It service requests across type, channel, and place.

Customer Service Requests are how residents report potholes, graffiti, abandoned
vehicles, illegal dumping and the like — increasingly through the Find-It-Fix-It
mobile app. Recent years only; the map is a random sample, charts use the full
recent-years dataset.
"""

import altair as alt
import pandas as pd
import pydeck as pdk
import streamlit as st

from app_db import query

st.title("📱 311 Service Requests")
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
    .mark_line(point=True, color="#2e86de")
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
    .mark_bar(color="#2e86de")
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
        .mark_bar(color="#54a0ff")
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
        .mark_bar(color="#54a0ff")
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

# --- Map (sampled) ---
st.subheader("Where requests come from")
st.caption(
    "A random sample of ~12k geolocated requests, binned into a hex grid over the "
    "city. Click a hexagon to see the requests there."
)
sample = query(
    """
    select latitude, longitude, request_type, department, address
    from main.mart_csr_map_sample
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
    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
)
event = st.pydeck_chart(
    deck, on_select="rerun", selection_mode="single-object", key="csr_hex"
)

# --- Data card for the clicked hexagon ---
picked = []
if event and getattr(event, "selection", None):
    picked = (event.selection.get("objects") or {}).get("hex", [])
if picked:
    obj = picked[0]
    points = obj.get("points", [])
    rows = pd.DataFrame([p.get("source", p) for p in points]) if points else pd.DataFrame()
    count = len(rows) if not rows.empty else int(obj.get("elevationValue", 0))
    st.markdown(f"### 📍 {count:,} requests in this hexagon")
    if not rows.empty:
        top = (
            rows["request_type"].value_counts().head(8).rename_axis("Request type")
            .reset_index(name="Requests")
        )
        c_a, c_b = st.columns([1, 1])
        with c_a:
            st.caption("Top request types here")
            st.dataframe(top, width="stretch", hide_index=True)
        with c_b:
            st.caption("Sample of requests")
            st.dataframe(
                rows[["request_type", "address"]].head(12),
                width="stretch",
                hide_index=True,
            )
else:
    st.caption("👆 No hexagon selected — click one on the map above.")

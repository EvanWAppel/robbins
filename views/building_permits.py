"""Regional building permits — structure permits from nine Puget Sound publishers.

Seattle, Pierce County, Tacoma, Bellevue, Everett, Bellingham, Puyallup, Kitsap
County and the Thurston Regional Planning Council, reduced to one definition of a
structure permit and one 2016+ window. Coverage is partial: every county view
says what it leaves out, and a county with no publisher shows a gap, not zero.
Valuation is shown per publisher only — definitions differ, so it is never summed.
"""

import altair as alt
import pydeck as pdk
import streamlit as st
from pydeck.data_utils import compute_view

import ui
from app_db import query
from city_config import PERMIT_GAPS, PERMIT_SOURCES, REGION_COUNTIES
from geography import county_selector
from regional_permits import permits_queries

PUBLISHER = {s.source_id: s.publisher for s in PERMIT_SOURCES}

st.title("Building Permits")
st.caption(
    "Structure permits (new construction, additions, alterations, re-roofs and "
    "demolitions) issued since 2016, from nine public feeds: Seattle, Pierce County, "
    "Tacoma, Bellevue, Everett, Bellingham, Puyallup, Kitsap County and the Thurston "
    "Regional Planning Council. Trade-only permits (electrical, mechanical, "
    "plumbing) are left out. Most other cities publish no permit data."
)

county = st.session_state.get("selected_county")
if not st.session_state.get("_regional_navigation"):
    county = county_selector()
multi = county is None
place = f"{REGION_COUNTIES[county]} County" if county else "Puget Sound"

q = permits_queries(county)
kpi = query(*q["kpis"])
if kpi.empty or kpi["permits"].isna().all():
    st.info(
        f"No integrated building-permit publisher for {place}. This is missing "
        "coverage, not an absence of construction."
    )
    if county in PERMIT_GAPS:
        st.caption(PERMIT_GAPS[county])
    st.stop()

if county in PERMIT_GAPS:
    st.warning(f"Partial coverage: {PERMIT_GAPS[county]}")

k = kpi.iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Permits issued", f"{int(k['permits']):,}")
c2.metric("Publishers", f"{int(k['publishers'])}")
c3.metric("Jurisdictions", f"{int(k['jurisdictions'])}")
c4.metric("Period", f"{k['first_month']:%Y} – {k['last_month']:%Y}")

publishers = query(*q["publishers"])
publishers["publisher"] = publishers["publisher_source"].map(PUBLISHER)
with st.expander("What each publisher covers"):
    st.dataframe(
        publishers.rename(columns={
            "publisher": "Publisher", "jurisdiction": "Jurisdiction", "county": "County",
            "coverage": "Coverage", "scope": "Scope", "valuation_basis": "Valuation basis",
            "permits": "Permits", "first_month": "First", "last_month": "Last",
        })[["Publisher", "Jurisdiction", "County", "Coverage", "Scope",
            "Valuation basis", "Permits", "First", "Last"]],
        hide_index=True, width="stretch",
    )
    st.caption(
        "Publishers still define permits a little differently even after filtering, "
        "and Thurston's feed covers only residential construction and demolition — "
        "compare trends, not exact levels. Kitsap County's feed starts in 2020."
    )

st.divider()

# --- Monthly permits ---
monthly = query(*q["monthly"])
series_title = "County" if multi else "Jurisdiction"
st.subheader("Permits issued per month")
if multi or county == "53035":
    st.caption(
        "Kitsap County's feed starts with applications submitted in 2020, so its "
        "series begins then (and early 2020 is undercounted) — not a building surge."
    )
monthly_chart = (
    alt.Chart(monthly)
    .mark_area(opacity=0.8)
    .encode(
        x=alt.X("issue_month:T", title=None),
        y=alt.Y("permits:Q", title="Permits", stack=True),
        color=alt.Color("series:N", title=series_title),
        tooltip=[
            alt.Tooltip("issue_month:T", title="Month", format="%b %Y"),
            alt.Tooltip("series:N", title=series_title),
            alt.Tooltip("permits:Q", title="Permits", format=","),
        ],
    )
)
ui.chart(monthly_chart, width="stretch")

# --- Annual by jurisdiction ---
annual = query(*q["annual"])
st.subheader("Permits per year by jurisdiction")
st.caption("The current year is partial.")
annual_chart = (
    alt.Chart(annual)
    .mark_bar()
    .encode(
        x=alt.X("year:O", title=None),
        y=alt.Y("permits:Q", title="Permits"),
        color=alt.Color("jurisdiction:N", title="Jurisdiction"),
        xOffset=alt.XOffset("jurisdiction:N"),
        tooltip=[
            alt.Tooltip("jurisdiction:N", title="Jurisdiction"),
            alt.Tooltip("county:N", title="County"),
            alt.Tooltip("year:O", title="Year"),
            alt.Tooltip("permits:Q", title="Permits", format=","),
        ],
    )
)
ui.chart(annual_chart, width="stretch")

# --- Valuation, one panel per publisher ---
valuation = query(*q["valuation_monthly"])
st.subheader("Reported project value, by publisher")
if valuation.empty:
    st.info(f"No publisher in {place} reports a project value.")
else:
    valuation["publisher"] = valuation["source_id"].map(PUBLISHER)
    st.caption(
        "Each publisher defines value differently (estimated cost, building "
        "valuation, job value), so each gets its own panel and scale and they are "
        "never added together. Puyallup and Thurston report no value."
    )
    val_chart = (
        alt.Chart(valuation)
        .mark_line(color="#2f6285")
        .encode(
            x=alt.X("issue_month:T", title=None),
            y=alt.Y("total_valuation:Q", title="Value ($)", axis=alt.Axis(format="~s")),
            tooltip=[
                alt.Tooltip("publisher:N", title="Publisher"),
                alt.Tooltip("valuation_basis:N", title="Definition"),
                alt.Tooltip("issue_month:T", title="Month", format="%b %Y"),
                alt.Tooltip("total_valuation:Q", title="Value", format="$,.0f"),
            ],
        )
        .properties(height=120)
        .facet(row=alt.Row("publisher:N", title=None))
        .resolve_scale(y="independent")
    )
    ui.chart(val_chart, width="stretch")

# --- Permit types, one publisher at a time ---
by_class = query(*q["by_class"])
if not by_class.empty:
    st.subheader("Permit types")
    st.caption("Type labels are each publisher's own, so they're shown one publisher at a time.")
    sources = [s for s in PUBLISHER if s in set(by_class["source_id"])]
    chosen = st.selectbox("Publisher", sources, format_func=lambda s: PUBLISHER[s])
    classes = by_class[by_class["source_id"] == chosen].groupby(
        "permit_class", as_index=False)["permit_count"].sum().nlargest(15, "permit_count")
    class_chart = (
        alt.Chart(classes)
        .mark_bar(color="#4f88a6")
        .encode(
            x=alt.X("permit_count:Q", title="Permits"),
            y=alt.Y("permit_class:N", sort="-x", title=None),
            tooltip=["permit_class", alt.Tooltip("permit_count:Q", title="Permits", format=",")],
        )
    )
    ui.chart(class_chart, width="stretch")

st.divider()

# --- Map ---
points = query(*q["map"])
st.subheader("Where recent permits are issued")
if points.empty:
    st.info(f"No geocoded permits for {place}.")
else:
    st.caption(
        "A sample: each publisher's 2,000 most recent geocoded permits, so smaller "
        "places stay visible next to Seattle. Not a count. Overlapping dots share a location."
    )
    points["publisher"] = points["source_id"].map(PUBLISHER)
    viewport = compute_view(points[["longitude", "latitude"]])
    viewport.zoom = min(viewport.zoom, 12)
    viewport.pitch = 0
    st.pydeck_chart(
        pdk.Deck(
            map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
            initial_view_state=viewport,
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
                "text": "{address}\n{jurisdiction} · {publisher}\n{permit_class}\n"
                        "Permit: {permit_number}\nIssued: {issue_date}"
            },
        )
    )

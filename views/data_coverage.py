"""Make existing source coverage and regional expansion gaps visible."""

import streamlit as st

from app_db import query
from city_config import DATA_SOURCES
from mobility import show_mobility_coverage
from regional_air import air_queries

st.title("Data Coverage")
st.caption(
    "The Puget Sound expansion covers Island, Jefferson, King, Kitsap, Mason, "
    "Pierce, Skagit, Snohomish, Thurston, and Whatcom counties. "
    "Sources are being added by topic; a place in the selector does not mean "
    "every topic has data there."
)
county = st.session_state.get("selected_county")
coverage = query(*air_queries(county)["coverage"])
st.subheader("Air-quality observations currently loaded")
if coverage.empty:
    st.info("No observations are loaded for this selection. Missing coverage is not a zero reading.")
else:
    st.dataframe(coverage, hide_index=True, width="stretch")
st.caption(
    "Dates above are observation dates. Retrieval freshness is not yet tracked. "
    "Monitor observations do not represent uniform coverage of a county."
)
st.subheader("Transit and ferry reporting coverage")
st.caption("The county selector does not allocate these agency-wide totals to a county.")
show_mobility_coverage(is_ferry=False)
show_mobility_coverage(is_ferry=True)
st.subheader("Configured source inventory")
st.caption(
    "This inventory describes the app's configured integrations, not live endpoint "
    "verification or complete county coverage. Civic topics still use the Seattle "
    "sources listed below; other regional civic feeds remain to be verified."
)
topic = st.selectbox("Topic", ["All topics", *sorted({s.topic for s in DATA_SOURCES})])
for source in DATA_SOURCES:
    if topic != "All topics" and source.topic != topic:
        continue
    with st.expander(f"{source.topic} · {source.publisher}"):
        st.write(f"**Coverage:** {source.coverage}")
        st.write(f"**Reporting geography:** {source.geography_kind}")
        st.write(f"**Record grain:** {source.record_grain}")
        st.write(source.limitations)
        st.link_button("Source", source.url)

st.subheader("Still to come")
st.write(
    "City filters, regional weather and water stations, remaining transport "
    "coverage gaps, and civic feeds outside Seattle are tracked in the expansion plan. "
    "Agency totals cannot currently be split into county or city ridership."
)

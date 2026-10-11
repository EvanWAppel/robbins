"""Robbins — an open-data atlas of the Seattle metro."""
import streamlit as st

from city_config import DATA_SOURCES, REGION_COUNTIES
from geography import county_selector
from ui import apply_theme

st.set_page_config(page_title="Robbins | Seattle City Atlas", page_icon="⚓", layout="wide")
apply_theme()

# Keep the existing page routes; group the index by the questions people explore.
sections = {
    "Start here": [
        st.Page("views/overview.py", title="Overview", default=True),
        st.Page("views/ask.py", title="Ask Tiresias"),
        st.Page("views/data_coverage.py", title="Data Coverage"),
    ],
    "City & housing": [
        st.Page("views/building_permits.py", title="Building Permits"),
        st.Page("views/business_licenses.py", title="Business Licenses"),
        st.Page("views/short_term_rentals.py", title="Short-Term Rentals"),
    ],
    "Public life": [
        st.Page("views/crime.py", title="Crime"),
        st.Page("views/fire_911.py", title="Fire 911 Calls"),
        st.Page("views/csr_311.py", title="311 Requests"),
        st.Page("views/restaurants.py", title="Restaurant Inspections"),
    ],
    "Getting around": [
        st.Page("views/transit.py", title="Transit Ridership"),
        st.Page("views/ferry.py", title="Ferry Ridership"),
    ],
    "The natural city": [
        st.Page("views/parks.py", title="Parks"),
        st.Page("views/trees.py", title="Street Trees"),
        st.Page("views/public_art.py", title="Public Art"),
        st.Page("views/weather.py", title="Rain & Records"),
        st.Page("views/air_quality.py", title="Air Quality"),
        st.Page("views/water.py", title="Water"),
    ],
}
page = st.navigation(sections, position="hidden")
with st.sidebar:
    st.html('<div class="brand"><div class="brand-name"><svg class="brand-mark" viewBox="0 0 24 24" fill="none" stroke="#cfe0e6" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="5" r="3"/><line x1="12" y1="22" x2="12" y2="8"/><path d="M5 12H2a10 10 0 0 0 20 0h-3"/></svg> robbins.</div><div class="brand-sub">The Seattle city atlas</div></div>')
    selected_county = county_selector()
    st.caption("Regional filters currently support Air Quality, Rain & Records, Water, and Data Coverage. Other topics are being expanded.")
    for section, entries in sections.items():
        st.caption(section)
        for entry in entries:
            with st.container(key="nav_current" if entry == page else f"nav_{entry.title}"):
                st.page_link(entry, label=entry.title)
    st.html('<div class="sidebar-note">A closer look at the place we call home.<br>Seattle roots · Puget Sound expansion</div>')

st.session_state["_regional_navigation"] = True
if selected_county and page.title not in {"Air Quality", "Rain & Records", "Water", "Data Coverage"}:
    st.title(page.title)
    st.info(
        f"{REGION_COUNTIES[selected_county]} County filtering is not available for this topic yet. "
        "Choose Air Quality or Data Coverage, or select all available data to see "
        "this topic's existing coverage."
    )
else:
    sources = [s for s in DATA_SOURCES if s.topic == page.title]
    if sources:
        st.caption("Configured source scope: " + "; ".join(s.coverage for s in sources))
    page.run()

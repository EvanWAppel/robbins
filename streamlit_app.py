"""Robbins — an open-data atlas of the Seattle metro."""
import streamlit as st

from ui import apply_theme

st.set_page_config(page_title="Robbins | Seattle City Atlas", page_icon="✳", layout="wide")
apply_theme()

# Keep the existing page routes; group the index by the questions people explore.
sections = {
    "Start here": [
        st.Page("views/overview.py", title="Overview", default=True),
        st.Page("views/ask.py", title="Ask the Data"),
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
    st.html('<div class="brand"><div class="brand-name"><span class="brand-mark">✳</span> robbins.</div><div class="brand-sub">The Seattle city atlas</div></div>')
    for section, entries in sections.items():
        st.caption(section)
        for entry in entries:
            with st.container(key="nav_current" if entry == page else f"nav_{entry.title}"):
                st.page_link(entry, label=entry.title)
    st.html('<div class="sidebar-note">A closer look at the place we call home.<br>Seattle · King · Pierce · Snohomish</div>')

page.run()

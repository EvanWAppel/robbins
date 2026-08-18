"""Seattle-Metro Open-Data Explorer — the interactive demo behind the portfolio.

Raw Seattle / King County (+ Pierce & Snohomish) open data is loaded into DuckDB,
modeled with dbt, and served here. This entry point just wires up the multi-page
navigation; each page lives in ``views/`` and queries the dbt marts via
``app_db.query``. Pages are added as their topics land — see TASKS.md (Group TOPIC).
"""

import streamlit as st

st.set_page_config(
    page_title="Seattle-Metro Open-Data Explorer",
    page_icon="🌲",
    layout="wide",
)

pages = [
    st.Page("views/overview.py", title="Overview", icon="🌲", default=True),
    st.Page("views/building_permits.py", title="Building Permits", icon="🏗️"),
    st.Page("views/crime.py", title="Crime", icon="🚨"),
    st.Page("views/fire_911.py", title="Fire 911 Calls", icon="🚒"),
    st.Page("views/csr_311.py", title="311 Requests", icon="📱"),
    st.Page("views/transit.py", title="Transit Ridership", icon="🚌"),
    st.Page("views/ferry.py", title="Ferry Ridership", icon="⛴️"),
    st.Page("views/restaurants.py", title="Restaurant Inspections", icon="🍽️"),
    st.Page("views/short_term_rentals.py", title="Short-Term Rentals", icon="🏠"),
    st.Page("views/business_licenses.py", title="Business Licenses", icon="📋"),
    st.Page("views/public_art.py", title="Public Art", icon="🎨"),
    st.Page("views/parks.py", title="Parks", icon="🌲"),
    st.Page("views/trees.py", title="Street Trees", icon="🌳"),
    st.Page("views/weather.py", title="Rain & Records", icon="🌧️"),
    st.Page("views/air_quality.py", title="Air Quality", icon="💨"),
    st.Page("views/water.py", title="Water", icon="🌊"),
    st.Page("views/ask.py", title="Ask the Data", icon="🤖"),
]

st.navigation(pages).run()

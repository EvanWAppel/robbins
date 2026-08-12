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
    st.Page("views/building_permits.py", title="Building Permits", icon="🏗️", default=True),
]

st.navigation(pages).run()

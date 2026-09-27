"""Shared place selection; unsupported topic scopes must remain explicit."""

import streamlit as st

from city_config import REGION_COUNTIES


def county_selector() -> str | None:
    options = [None, *REGION_COUNTIES]
    if st.session_state.get('selected_county') not in options:
        st.session_state['selected_county'] = None
    value = st.selectbox(
        'County', options,
        index=options.index(st.session_state.get('selected_county')),
        format_func=lambda code: f'{REGION_COUNTIES[code]} County' if code else 'Puget Sound — all available data',
        key='_county_widget',
    )
    st.session_state['selected_county'] = value
    return value

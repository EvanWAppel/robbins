"""Ridership presentation helpers that retain agency-level coverage limits."""

import pandas as pd


def operator_share(operators: pd.DataFrame, name: str) -> float | None:
    """Look up the named operator, never assume the largest row is WSF."""
    values = operators.loc[operators['operator'] == name, 'boardings']
    total = operators['boardings'].sum()
    if values.empty or total <= 0:
        return None
    return float(100 * values.sum() / total)


def show_mobility_coverage(is_ferry: bool) -> None:
    import streamlit as st

    from app_db import query
    from city_config import NTD_MONTHLY_GAPS

    coverage = query(
        'select agency, agency_label, first_month, last_month, months_reported '
        'from main.mart_mobility_coverage where is_ferry = ? order by agency_label',
        (is_ferry,),
    )
    st.caption(
        'Agency-wide boardings, not unique passengers or county/route totals. '
        'Reporting periods and participating operators vary; changes in totals '
        'can reflect coverage as well as changes in ridership.'
    )
    if coverage.empty:
        st.info('No agency observations are loaded for this topic.')
        st.stop()
    st.caption(
        f"Loaded reporting months: {coverage.first_month.min():%b %Y}–"
        f"{coverage.last_month.max():%b %Y}. "
        'These dates describe observations, not the last retrieval time.'
    )
    with st.expander('Agency coverage and reporting periods'):
        st.dataframe(coverage, hide_index=True, width='stretch')
        if not is_ferry:
            st.write('Not present in the verified monthly feed: ' + ', '.join(NTD_MONTHLY_GAPS) + '. These are coverage gaps, not zero ridership.')

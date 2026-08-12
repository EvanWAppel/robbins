"""Public Health food-establishment inspections — scores, results, and violations."""

import altair as alt
import streamlit as st

from app_db import query

st.title("🍽️ Restaurant Inspections")
st.caption(
    "Public Health – Seattle & King County food-establishment inspections. "
    "Note: a higher inspection score means MORE violations (worse), not better."
)

# --- KPIs ---
kpi = query(
    """
    select
        count(*)                     as inspections,
        count(distinct establishment) as establishments,
        round(avg(inspection_score), 1) as avg_score
    from main.mart_inspections
    """
)
c1, c2, c3 = st.columns(3)
c1.metric("Inspections", f"{int(kpi['inspections'][0]):,}")
c2.metric("Establishments", f"{int(kpi['establishments'][0]):,}")
c3.metric("Avg score (higher = worse)", f"{kpi['avg_score'][0]:.1f}")

st.divider()

# --- Inspections per month + avg score ---
monthly = query(
    """
    select inspection_month, inspection_count, avg_score
    from main.mart_inspections_over_time
    order by 1
    """
)
st.subheader("Inspections per month")
count_line = (
    alt.Chart(monthly)
    .mark_area(color="#3f88c5", opacity=0.7)
    .encode(
        x=alt.X("inspection_month:T", title=None),
        y=alt.Y("inspection_count:Q", title="Inspections"),
        tooltip=[
            alt.Tooltip("inspection_month:T", title="Month"),
            alt.Tooltip("inspection_count:Q", title="Inspections", format=","),
        ],
    )
)
st.altair_chart(count_line, width="stretch")

st.subheader("Average inspection score per month")
score_line = (
    alt.Chart(monthly)
    .mark_line(color="#c0392b")
    .encode(
        x=alt.X("inspection_month:T", title=None),
        y=alt.Y("avg_score:Q", title="Avg score (higher = worse)"),
        tooltip=[
            alt.Tooltip("inspection_month:T", title="Month"),
            alt.Tooltip("avg_score:Q", title="Avg score", format=".1f"),
        ],
    )
)
st.altair_chart(score_line, width="stretch")

# --- Results breakdown ---
results = query(
    """
    select inspection_result, inspection_count
    from main.mart_inspection_results
    order by inspection_count desc
    """
)
st.subheader("Inspection results")
results_chart = (
    alt.Chart(results)
    .mark_bar(color="#3f88c5")
    .encode(
        x=alt.X("inspection_count:Q", title="Inspections"),
        y=alt.Y("inspection_result:N", sort="-x", title=None),
        tooltip=[
            "inspection_result",
            alt.Tooltip("inspection_count:Q", title="Inspections", format=","),
        ],
    )
)
st.altair_chart(results_chart, width="stretch")

# --- Top violations ---
violations = query(
    """
    select violation_description, violation_count
    from main.mart_top_violations
    order by violation_count desc
    limit 15
    """
)
st.subheader("Most common violations")
violations_chart = (
    alt.Chart(violations)
    .mark_bar(color="#e67e22")
    .encode(
        x=alt.X("violation_count:Q", title="Occurrences"),
        y=alt.Y("violation_description:N", sort="-x", title=None),
        tooltip=[
            "violation_description",
            alt.Tooltip("violation_count:Q", title="Occurrences", format=","),
        ],
    )
)
st.altair_chart(violations_chart, width="stretch")

st.divider()

# --- Searchable establishments table ---
st.subheader("Establishments (3+ inspections)")
st.caption("Search by name. Sorted by worst average score first.")
worst = query(
    """
    select establishment, inspections, avg_score, total_violations
    from main.mart_worst_establishments
    order by avg_score desc
    """
)
term = st.text_input("Filter by establishment name")
if term:
    worst = worst[worst["establishment"].str.contains(term, case=False, na=False)]
st.dataframe(worst, width="stretch", hide_index=True)

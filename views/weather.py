"""Seattle weather — "Rain & Records" at Sea-Tac (NOAA GHCN-Daily, 1948-present).

Seattle's reputation is rain, so the page leads with the wet-winter / dry-summer
climatology, then the all-time records and the recent daily band. Sourced from
NOAA's keyless GHCN-Daily station file — a third ingestion pattern (federal bulk
CSV) alongside Socrata and ArcGIS.
"""

import altair as alt
import streamlit as st

from app_db import query

st.title("🌧️ Rain & Records")
st.caption(
    "Daily weather at Seattle-Tacoma International Airport since 1948 "
    "(NOAA GHCN-Daily station USW00024233). The wet-winter / dry-summer pattern, "
    "the all-time extremes, and the last two years day by day."
)

normals = query(
    """
    select month_num, month_name, avg_precip_in, avg_tmax_f, avg_tmin_f
    from main.mart_weather_monthly_normals order by month_num
    """
)
annual = query(
    "select year, total_precip_in, rain_days, avg_tmax_f from main.mart_weather_annual order by year"
)
records = query("select record_type, obs_date, value from main.mart_weather_records")
recent = query(
    "select obs_date, tmax_f, tmin_f, precip_in from main.mart_weather_recent order by obs_date"
)

# --- KPIs: the headline records ---
rec = {r.record_type: r for r in records.itertuples()}
# Latest full year for an "annual rainfall" reference point.
full_years = annual[annual["year"] < annual["year"].max()]
last_full = full_years.iloc[-1]

def _on(d) -> str:
    return d.strftime("%b %-d, %Y")


c1, c2, c3, c4 = st.columns(4)
c1.metric("Hottest day", rec["Hottest day"].value, _on(rec["Hottest day"].obs_date),
          delta_color="off")
c2.metric("Wettest day", rec["Wettest day"].value, _on(rec["Wettest day"].obs_date),
          delta_color="off")
c3.metric(f"Rain in {int(last_full.year)}", f"{last_full.total_precip_in:.1f} in")
c4.metric(f"Rainy days in {int(last_full.year)}", f"{int(last_full.rain_days)}")

st.divider()

# --- Climatology: precip by calendar month ---
st.subheader("A wet winter and a dry summer")
st.caption("Average daily precipitation by calendar month, across the full record.")
precip_chart = (
    alt.Chart(normals)
    .mark_bar(color="#2980b9")
    .encode(
        x=alt.X("month_name:N", sort=list(normals["month_name"]), title=None),
        y=alt.Y("avg_precip_in:Q", title="Avg precip (in/day)"),
        tooltip=[
            alt.Tooltip("month_name:N", title="Month"),
            alt.Tooltip("avg_precip_in:Q", title="Avg precip (in/day)", format=".3f"),
        ],
    )
)
st.altair_chart(precip_chart, width="stretch")

# --- Climatology: temperature band by month ---
# The area spans tmin->tmax; Altair domains the axis from the y (tmin) channel
# only, which clips the warmer tmax edge, so set the domain from both explicitly.
st.subheader("Average high and low by month")
normals_temp_domain = [
    float(normals["avg_tmin_f"].min()) - 5,
    float(normals["avg_tmax_f"].max()) + 5,
]
band = (
    alt.Chart(normals)
    .mark_area(opacity=0.3, color="#e67e22")
    .encode(
        x=alt.X("month_name:N", sort=list(normals["month_name"]), title=None),
        y=alt.Y("avg_tmin_f:Q", title="Temperature (°F)",
                scale=alt.Scale(zero=False, domain=normals_temp_domain)),
        y2="avg_tmax_f:Q",
        tooltip=[
            alt.Tooltip("month_name:N", title="Month"),
            alt.Tooltip("avg_tmax_f:Q", title="Avg high (°F)", format=".0f"),
            alt.Tooltip("avg_tmin_f:Q", title="Avg low (°F)", format=".0f"),
        ],
    )
)
st.altair_chart(band, width="stretch")

# --- Annual rainfall trend ---
st.subheader("Total rainfall by year")
st.caption("The current (partial) year is excluded.")
annual_full = annual[annual["year"] < annual["year"].max()]
rain_line = (
    alt.Chart(annual_full)
    .mark_line(point=True, color="#2980b9")
    .encode(
        x=alt.X("year:O", title=None),
        y=alt.Y("total_precip_in:Q", title="Total precip (in)"),
        tooltip=[
            alt.Tooltip("year:O", title="Year"),
            alt.Tooltip("total_precip_in:Q", title="Total precip (in)", format=".1f"),
            alt.Tooltip("rain_days:Q", title="Rainy days"),
        ],
    )
)
st.altair_chart(rain_line, width="stretch")

# --- Recent daily temperature band ---
st.subheader("The last two years, day by day")
st.caption("Daily high and low temperature at Sea-Tac.")
recent_band = (
    alt.Chart(recent)
    .mark_area(opacity=0.4, color="#e67e22")
    .encode(
        x=alt.X("obs_date:T", title=None),
        y=alt.Y("tmin_f:Q", title="Temperature (°F)",
                scale=alt.Scale(zero=False,
                                domain=[float(recent["tmin_f"].min()) - 5,
                                        float(recent["tmax_f"].max()) + 5])),
        y2="tmax_f:Q",
        tooltip=[
            alt.Tooltip("obs_date:T", title="Date"),
            alt.Tooltip("tmax_f:Q", title="High (°F)", format=".0f"),
            alt.Tooltip("tmin_f:Q", title="Low (°F)", format=".0f"),
        ],
    )
)
st.altair_chart(recent_band, width="stretch")

# --- Records table ---
st.subheader("All-time records at Sea-Tac")
records_display = records.rename(
    columns={"record_type": "Record", "obs_date": "Date", "value": "Value"}
)
st.dataframe(records_display, width="stretch", hide_index=True)

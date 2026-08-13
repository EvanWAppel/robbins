"""Seattle water — snowpack, the Cedar River, and Puget Sound sea level.

Three federal feeds tell one connected story: Cascade snowpack (NRCS SNOTEL at
Stampede Pass) melts into the Cedar River (USGS gage at Renton) that Seattle
drinks, while Puget Sound's sea level (NOAA tides at Elliott Bay) creeps up over
the decades. A drought year like 2015 shows up in both the snow and the river.
"""

import altair as alt
import streamlit as st

from app_db import query

st.title("🌊 Water")
st.caption(
    "The Cascade-to-tap-to-Sound water story, from three keyless federal feeds: "
    "snowpack at Stampede Pass (NRCS SNOTEL), Cedar River streamflow at Renton "
    "(USGS), and Seattle sea level (NOAA tides)."
)

snow_peak = query(
    "select water_year, peak_swe_in from main.mart_snowpack_annual_peak order by water_year"
)
snow_recent = query(
    "select obs_date, water_year, swe_in from main.mart_snowpack_recent order by obs_date"
)
river_normals = query(
    "select month_num, month_name, avg_discharge_cfs from main.mart_river_monthly_normals order by month_num"
)
river_annual = query(
    "select year, avg_discharge_cfs, min_discharge_cfs from main.mart_river_annual order by year"
)
tides_annual = query(
    "select year, avg_msl_ft, avg_range_ft, month_count from main.mart_tides_annual order by year"
)

# --- KPIs ---
lowest_snow = snow_peak.loc[snow_peak["peak_swe_in"].idxmin()]
highest_snow = snow_peak.loc[snow_peak["peak_swe_in"].idxmax()]
tides_full = tides_annual[tides_annual["month_count"] >= 12]
sea_rise_in = (tides_full.iloc[-1]["avg_msl_ft"] - tides_full.iloc[0]["avg_msl_ft"]) * 12

c1, c2, c3, c4 = st.columns(4)
c1.metric("Lowest snowpack", f"{lowest_snow.peak_swe_in:.0f} in",
          f"water year {int(lowest_snow.water_year)}", delta_color="off")
c2.metric("Biggest snowpack", f"{highest_snow.peak_swe_in:.0f} in",
          f"water year {int(highest_snow.water_year)}", delta_color="off")
c3.metric("Cedar R. summer low", f"{river_annual['min_discharge_cfs'].min():.0f} cfs")
c4.metric(
    f"Sea level, {int(tides_full.iloc[0].year)}–{int(tides_full.iloc[-1].year)}",
    f"+{sea_rise_in:.1f} in",
)

st.divider()

# --- Snowpack peak by water year ---
st.subheader("Cascade snowpack, year by year")
st.caption(
    "Peak snow-water-equivalent each water year at Stampede Pass. 2015 was a "
    "historic snow-drought — a warm winter dropped rain, not snow."
)
peak_chart = (
    alt.Chart(snow_peak)
    .mark_bar()
    .encode(
        x=alt.X("water_year:O", title="Water year"),
        y=alt.Y("peak_swe_in:Q", title="Peak SWE (in)"),
        color=alt.Color(
            "peak_swe_in:Q",
            scale=alt.Scale(scheme="blues"),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("water_year:O", title="Water year"),
            alt.Tooltip("peak_swe_in:Q", title="Peak SWE (in)", format=".1f"),
        ],
    )
)
st.altair_chart(peak_chart, width="stretch")

# --- Recent daily snowpack ---
st.subheader("The last three winters, day by day")
recent_chart = (
    alt.Chart(snow_recent)
    .mark_line()
    .encode(
        x=alt.X("obs_date:T", title=None),
        y=alt.Y("swe_in:Q", title="Snow water equivalent (in)"),
        color=alt.Color("water_year:N", title="Water year"),
        tooltip=[
            alt.Tooltip("obs_date:T", title="Date"),
            alt.Tooltip("swe_in:Q", title="SWE (in)", format=".1f"),
        ],
    )
)
st.altair_chart(recent_chart, width="stretch")

# --- Cedar River seasonal signature ---
st.subheader("The Cedar River through the year")
st.caption("Average daily streamflow by month — high with winter rain and spring melt, low by late summer.")
river_chart = (
    alt.Chart(river_normals)
    .mark_area(color="#16a085", opacity=0.7, line={"color": "#16a085"})
    .encode(
        x=alt.X("month_name:N", sort=list(river_normals["month_name"]), title=None),
        y=alt.Y("avg_discharge_cfs:Q", title="Avg discharge (cfs)"),
        tooltip=[
            alt.Tooltip("month_name:N", title="Month"),
            alt.Tooltip("avg_discharge_cfs:Q", title="Avg discharge (cfs)", format=",.0f"),
        ],
    )
)
st.altair_chart(river_chart, width="stretch")

# --- Sea level trend ---
st.subheader("Puget Sound is rising")
st.caption("Average annual sea level at Seattle (NOAA datum, feet). The current partial year is excluded.")
sea_chart = (
    alt.Chart(tides_full)
    .mark_line(point=True, color="#2980b9")
    .encode(
        x=alt.X("year:O", title=None),
        y=alt.Y("avg_msl_ft:Q", title="Mean sea level (ft)", scale=alt.Scale(zero=False)),
        tooltip=[
            alt.Tooltip("year:O", title="Year"),
            alt.Tooltip("avg_msl_ft:Q", title="Mean sea level (ft)", format=".3f"),
        ],
    )
)
trend = sea_chart.transform_regression("year", "avg_msl_ft").mark_line(
    color="#e74c3c", strokeDash=[5, 5]
)
st.altair_chart(sea_chart + trend, width="stretch")

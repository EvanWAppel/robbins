"""Overview — the landing page. A guided tour of every topic in one screen.

Pulls one or two headline numbers from each topic's marts so a visitor sees the
whole Seattle-metro picture at a glance, then clicks through to the detail pages.
Everything here is an aggregate of marts that already exist — no new sources.
"""

import streamlit as st

from app_db import query

st.title("🌲 Seattle-Metro Open-Data Explorer")
st.markdown(
    "Public data from across the Seattle metro — the city, King/Pierce/Snohomish "
    "counties, and federal feeds — loaded into DuckDB, modeled with **dbt**, and "
    "served here. Eleven topics, drawn through **three ingestion patterns**: the "
    "Socrata SODA API, ArcGIS FeatureServers, and keyless federal bulk files."
)


def scalar(sql: str):
    """First column of the first row of a query."""
    return query(sql).iloc[0, 0]


# Headline totals.
permits = scalar("select sum(permit_count) from main.mart_permits_monthly")
permit_value = scalar("select sum(total_valuation) from main.mart_permits_monthly")
crime = scalar("select sum(incident_count) from main.mart_crime_monthly")
fire = scalar("select sum(call_count) from main.mart_fire_monthly")
inspections = scalar("select count(*) from main.mart_inspections")
establishments = scalar("select count(distinct establishment) from main.mart_inspections")
sat_pct = scalar(
    """
    select round(100.0 * count(*) filter (where inspection_result = 'Satisfactory')
        / nullif(count(*) filter (where inspection_result in ('Satisfactory','Unsatisfactory')), 0))
    from main.mart_inspections
    """
)
str_active = scalar(
    "select sum(license_count) from main.mart_str_by_status where lower(licensestatus) = 'active'"
)
licenses = scalar("select sum(license_count) from main.mart_licenses_by_industry")
art = scalar("select sum(artwork_count) from main.mart_art_by_type")
parks = scalar("select count(*) from main.mart_parks_points")
park_acres = scalar("select sum(area_acres) from main.mart_parks_points")
air_good = scalar(
    """
    select round(100.0 * sum(day_count) filter (where aqi_category in ('Good','Moderate'))
        / sum(day_count))
    from main.mart_air_category_days
    """
)
worst_aqi = scalar("select max(max_aqi) from main.mart_air_worst_days")
annual_rain = scalar(
    "select avg(total_precip_in) from main.mart_weather_annual where year < (select max(year) from main.mart_weather_annual)"
)
wettest = scalar("select value from main.mart_weather_records where record_type = 'Wettest day'")
snow_low = scalar("select min(peak_swe_in) from main.mart_snowpack_annual_peak")
tides = query("select year, avg_msl_ft, month_count from main.mart_tides_annual order by year")
tides_full = tides[tides["month_count"] >= 12]
sea_rise_in = (tides_full.iloc[-1]["avg_msl_ft"] - tides_full.iloc[0]["avg_msl_ft"]) * 12

total_records = (
    int(permits) + int(crime) + int(fire) + int(inspections)
    + int(licenses) + int(art) + int(parks)
)
c = st.columns(3)
c[0].metric("Records in the warehouse", f"{total_records / 1e6:.1f}M+")
c[1].metric("Topics", "11")
c[2].metric("Data sources", "Socrata · ArcGIS · Federal")

st.divider()

# --- City & Housing ---
st.subheader("🏗️ City & Housing")
a, b, d = st.columns(3)
a.metric("Permits issued", f"{int(permits):,}", f"${permit_value / 1e9:.0f}B valuation",
         delta_color="off")
b.metric("Active business licenses", f"{int(licenses):,}")
d.metric("Short-term rentals", f"{int(str_active):,}", "active", delta_color="off")
lc = st.columns(3)
lc[0].page_link("views/building_permits.py", label="Building Permits", icon="🏗️")
lc[1].page_link("views/business_licenses.py", label="Business Licenses", icon="📋")
lc[2].page_link("views/short_term_rentals.py", label="Short-Term Rentals", icon="🏠")

st.divider()

# --- Public Safety ---
st.subheader("🚨 Public Safety")
a, b = st.columns(2)
a.metric("Police offenses", f"{int(crime):,}", "since 2019", delta_color="off")
b.metric("Fire 911 dispatches", f"{int(fire):,}", "since 2019", delta_color="off")
sc = st.columns(2)
sc[0].page_link("views/crime.py", label="Crime", icon="🚨")
sc[1].page_link("views/fire_911.py", label="Fire 911 Calls", icon="🚒")

st.divider()

# --- Health & Food ---
st.subheader("🍽️ Health & Food")
a, b = st.columns(2)
a.metric("Restaurant inspections", f"{int(inspections):,}", f"{int(establishments):,} establishments",
         delta_color="off")
b.metric("Satisfactory result", f"{int(sat_pct)}%")
st.columns(2)[0].page_link("views/restaurants.py", label="Restaurant Inspections", icon="🍽️")

st.divider()

# --- Environment ---
st.subheader("🌦️ Environment")
a, b, d = st.columns(3)
a.metric("Air Good or Moderate", f"{int(air_good)}%", f"worst AQI {int(worst_aqi)}", delta_color="off")
b.metric("Avg annual rainfall", f"{annual_rain:.0f} in", f"wettest day {wettest}", delta_color="off")
d.metric("Sea level since 2000", f"+{sea_rise_in:.1f} in", f"2015 snowpack {snow_low:.0f} in",
         delta_color="off")
ec = st.columns(3)
ec[0].page_link("views/air_quality.py", label="Air Quality", icon="💨")
ec[1].page_link("views/weather.py", label="Rain & Records", icon="🌧️")
ec[2].page_link("views/water.py", label="Water", icon="🌊")

st.divider()

# --- Culture & Recreation ---
st.subheader("🎨 Culture & Recreation")
a, b = st.columns(2)
a.metric("Parks", f"{int(parks):,}", f"{int(park_acres):,} acres", delta_color="off")
b.metric("Public artworks", f"{int(art):,}")
rc = st.columns(2)
rc[0].page_link("views/parks.py", label="Parks", icon="🌲")
rc[1].page_link("views/public_art.py", label="Public Art", icon="🎨")

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
    "served here. Fifteen topics, drawn through **three ingestion patterns**: the "
    "Socrata SODA API, ArcGIS FeatureServers, and keyless federal bulk files."
)

# Data-freshness surface: build time + total records come from mart_build_info,
# frozen in at `dbt build`. In production the warehouse is baked from scratch on
# every deploy, so built_at is an honest "data loaded" timestamp.
_build = query("select built_at, total_records from main.mart_build_info").iloc[0]
_total_records = int(_build["total_records"])
st.caption(
    f"🕓 Warehouse built {_build['built_at']:%b %-d, %Y} · "
    f"{_total_records:,} records · rebuilt fresh on every deploy"
)


def scalar(sql: str):
    """First column of the first row of a query."""
    return query(sql).iloc[0, 0]


# The semantic layer: headline numbers are read by name from mart_metrics (generated
# from metrics.yml), so each metric is defined in exactly one place — not re-derived
# with ad-hoc SQL here. See metrics.yml.
_metrics = query("select metric_name, value from main.mart_metrics")
_metric_values = dict(zip(_metrics["metric_name"], _metrics["value"], strict=True))


def metric(name: str) -> float:
    """Look up a metric value by name from the semantic layer (mart_metrics)."""
    if name not in _metric_values:
        raise KeyError(f"Unknown metric {name!r} — is it defined in metrics.yml?")
    return _metric_values[name]


# Headline totals — the ones below come through the semantic layer (metrics.yml).
permits = metric("total_permits")
permit_value = metric("total_permit_valuation")
crime = metric("total_crime_offenses")
fire = metric("total_fire_calls")
csr = metric("total_311_requests")
csr_app_pct = scalar(
    """
    select round(100.0 * sum(request_count) filter (where method_received ilike '%find it fix it%')
        / sum(request_count))
    from main.mart_csr_by_method
    """
)
inspections = metric("total_inspections")
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
trees = metric("total_street_trees")
tree_species = scalar("select distinct_species from main.mart_trees_summary")
transit_total = metric("total_transit_boardings")
ferry_total = metric("total_ferry_boardings")
air_good = metric("pct_good_or_moderate_air_days")
worst_aqi = scalar("select max(max_aqi) from main.mart_air_worst_days")
annual_rain = scalar(
    "select avg(total_precip_in) from main.mart_weather_annual where year < (select max(year) from main.mart_weather_annual)"
)
wettest = scalar("select value from main.mart_weather_records where record_type = 'Wettest day'")
snow_low = scalar("select min(peak_swe_in) from main.mart_snowpack_annual_peak")
tides = query("select year, avg_msl_ft, month_count from main.mart_tides_annual order by year")
tides_full = tides[tides["month_count"] >= 12]
sea_rise_in = (tides_full.iloc[-1]["avg_msl_ft"] - tides_full.iloc[0]["avg_msl_ft"]) * 12

# total records come from mart_build_info (the nine grain counts, defined once there)
c = st.columns(3)
c[0].metric("Records in the warehouse", f"{_total_records / 1e6:.1f}M+")
c[1].metric("Topics", "15")
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
st.subheader("🚨 Public Safety & City Services")
a, b, d = st.columns(3)
a.metric("Police offenses", f"{int(crime):,}", "since 2019", delta_color="off")
b.metric("Fire 911 dispatches", f"{int(fire):,}", "since 2019", delta_color="off")
d.metric("311 requests", f"{int(csr):,}", f"{int(csr_app_pct)}% via app", delta_color="off")
sc = st.columns(3)
sc[0].page_link("views/crime.py", label="Crime", icon="🚨")
sc[1].page_link("views/fire_911.py", label="Fire 911 Calls", icon="🚒")
sc[2].page_link("views/csr_311.py", label="311 Requests", icon="📱")

st.divider()

# --- Getting Around ---
st.subheader("🚌 Getting Around")
a, b = st.columns(2)
a.metric("Transit boardings", f"{transit_total / 1e9:.1f}B", "since 2015", delta_color="off")
b.metric("Ferry boardings", f"{ferry_total / 1e6:.0f}M", "since 2015", delta_color="off")
gc = st.columns(2)
gc[0].page_link("views/transit.py", label="Transit Ridership", icon="🚌")
gc[1].page_link("views/ferry.py", label="Ferry Ridership", icon="⛴️")

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
a, b, d = st.columns(3)
a.metric("Parks", f"{int(parks):,}", f"{int(park_acres):,} acres", delta_color="off")
b.metric("Street trees", f"{int(trees):,}", f"{int(tree_species):,} species", delta_color="off")
d.metric("Public artworks", f"{int(art):,}")
rc = st.columns(3)
rc[0].page_link("views/parks.py", label="Parks", icon="🌲")
rc[1].page_link("views/trees.py", label="Street Trees", icon="🌳")
rc[2].page_link("views/public_art.py", label="Public Art", icon="🎨")

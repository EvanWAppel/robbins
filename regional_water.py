"""Parameterized summaries over regional water observations (river, tide, snow).

Three federal networks, each with real per-county gaps: rivers in 8/10 counties
(no gage in Island/Kitsap), tide gauges only in the 5 saltwater-front counties,
snow only in the 7 mountainous ones. Charts use each county's headline station;
maps and the coverage summary use every station. Filtering is applied before every
aggregation, so absence surfaces as empty — never extrapolated from a neighbor.
"""


def water_queries(county_fips: str | None = None) -> dict[str, tuple[str, tuple]]:
    hi = " and county_fips = ?" if county_fips else ""
    allw = "where county_fips = ?" if county_fips else ""
    one = (county_fips,) if county_fips else ()

    river = "main.mart_river_observations"
    tides = "main.mart_tides_observations"
    snow = "main.mart_snow_observations"

    queries: dict[str, tuple[str, tuple]] = {
        # ---- River (USGS streamflow) --------------------------------------
        "river_monthly": (
            f"""select county_fips, county, station_name,
                extract(month from obs_date) as month_num,
                strftime(make_date(2000, extract(month from obs_date)::int, 1), '%b') as month_name,
                avg(discharge_cfs) as avg_discharge_cfs
                from {river} where is_headline{hi}
                group by 1, 2, 3, 4, 5 order by county, month_num""",
            one,
        ),
        "river_annual": (
            f"""select county_fips, county, station_name,
                extract(year from obs_date) as year,
                avg(discharge_cfs) as avg_discharge_cfs,
                min(discharge_cfs) as min_discharge_cfs
                from {river} where is_headline{hi}
                group by 1, 2, 3, 4 order by county, year""",
            one,
        ),
        "river_stations": (
            f"""select site_no, any_value(station_name) as station_name,
                county_fips, any_value(county) as county,
                avg(latitude) as latitude, avg(longitude) as longitude,
                bool_or(is_headline) as is_headline, avg(discharge_cfs) as avg_discharge_cfs,
                min(obs_date) as first_date, max(obs_date) as last_date, count(*) as day_count
                from {river} {allw}
                group by site_no, county_fips order by county_fips, site_no""",
            one,
        ),
        # ---- Tide (NOAA sea-level datums) ---------------------------------
        "tides_annual": (
            f"""select county_fips, county, station_name, year,
                avg(msl_ft) as avg_msl_ft, avg(range_ft) as avg_range_ft, count(*) as month_count
                from {tides} where is_headline{hi}
                group by 1, 2, 3, 4 order by county, year""",
            one,
        ),
        "tides_stations": (
            f"""select station_id, any_value(station_name) as station_name,
                county_fips, any_value(county) as county,
                avg(latitude) as latitude, avg(longitude) as longitude,
                bool_or(is_headline) as is_headline, count(*) as month_count,
                min(obs_month) as first_month, max(obs_month) as last_month
                from {tides} {allw}
                group by station_id, county_fips order by county_fips, station_id""",
            one,
        ),
        # ---- Snow (NRCS SNOTEL) -------------------------------------------
        # A water year (Oct 1 - Sep 30) counts once its data reaches April 1,
        # around peak snowpack; before then (e.g. an October build) the barely
        # started year would chart as a near-zero "record drought".
        "snow_annual_peak": (
            f"""with h as (select * from {snow} where is_headline{hi} and swe_in is not null)
                select county_fips, county, station_name, water_year,
                max(swe_in) as peak_swe_in
                from h
                group by 1, 2, 3, 4
                having max(obs_date) >= make_date(water_year, 4, 1)
                order by county, water_year""",
            one,
        ),
        "snow_recent": (
            f"""with h0 as (select * from {snow} where is_headline{hi} and swe_in is not null),
                winters as (select county_fips, water_year from h0
                    group by 1, 2 having max(obs_date) >= make_date(water_year, 4, 1)),
                h as (select h0.* from h0 join winters using (county_fips, water_year)),
                cutoff as (select max(water_year) - 2 as start_wy from h)
                select county_fips, county, station_name, obs_date, water_year, swe_in
                from h, cutoff where water_year >= cutoff.start_wy
                order by county, obs_date""",
            one,
        ),
        "snow_stations": (
            f"""select station_triplet, any_value(station_name) as station_name,
                county_fips, any_value(county) as county,
                avg(latitude) as latitude, avg(longitude) as longitude,
                bool_or(is_headline) as is_headline, max(swe_in) as peak_swe_in,
                min(obs_date) as first_date, max(obs_date) as last_date, count(*) as day_count
                from {snow} {allw}
                group by station_triplet, county_fips order by county_fips, station_triplet""",
            one,
        ),
        # ---- Combined coverage across the three networks ------------------
        "coverage": (
            f"""select 'River' as network, county_fips, county,
                    count(distinct site_no) as station_count,
                    min(obs_date) as first_date, max(obs_date) as last_date
                from {river} {allw} group by county_fips, county
                union all
                select 'Tide', county_fips, county, count(distinct station_id),
                    min(obs_month), max(obs_month)
                from {tides} {allw} group by county_fips, county
                union all
                select 'Snow', county_fips, county, count(distinct station_triplet),
                    min(obs_date), max(obs_date)
                from {snow} {allw} group by county_fips, county
                order by network, county""",
            one * 3,
        ),
    }
    return queries

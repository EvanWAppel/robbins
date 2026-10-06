"""Parameterized summaries over regional weather observations.

Charts read each county's headline station (one clean series per county); the map
and coverage summary read every station. County filtering is applied before every
aggregation — mirroring :mod:`regional_air` — so a selection never silently falls
back to Seattle and an unmonitored county resolves to empty, not zero.
"""


def weather_queries(county_fips: str | None = None) -> dict[str, tuple[str, tuple]]:
    # Headline-series clause (charts) vs. all-station clause (map/coverage).
    hi = " and county_fips = ?" if county_fips else ""
    allw = "where county_fips = ?" if county_fips else ""
    one = (county_fips,) if county_fips else ()

    obs = "main.mart_weather_observations"
    queries: dict[str, tuple[str, tuple]] = {
        "monthly_normals": (
            f"""select county_fips, county, station_name,
                extract(month from obs_date) as month_num,
                strftime(make_date(2000, extract(month from obs_date)::int, 1), '%b') as month_name,
                avg(precip_in) as avg_precip_in,
                avg(tmax_f) as avg_tmax_f, avg(tmin_f) as avg_tmin_f
                from {obs} where is_headline{hi}
                group by 1, 2, 3, 4, 5 order by county, month_num""",
            one,
        ),
        "annual": (
            f"""select county_fips, county, station_name,
                extract(year from obs_date) as year,
                sum(precip_in) as total_precip_in,
                count(*) filter (where precip_in > 0.01) as rain_days,
                avg(tmax_f) as avg_tmax_f, avg(tmin_f) as avg_tmin_f
                from {obs} where is_headline{hi}
                group by 1, 2, 3, 4 order by county, year""",
            one,
        ),
        "recent": (
            f"""with h as (select * from {obs} where is_headline{hi}),
                cutoff as (select max(obs_date) - interval 2 year as start_date from h)
                select county_fips, county, station_name, obs_date, tmax_f, tmin_f, precip_in
                from h, cutoff where obs_date >= cutoff.start_date
                order by county, obs_date""",
            one,
        ),
        "records": (
            f"""with h as (select * from {obs} where is_headline{hi}),
                hottest as (select county_fips, county, 1 as sort_order, 'Hottest day' as record_type,
                    obs_date, cast(round(tmax_f, 0) as integer) || ' °F' as value from h
                    where tmax_f is not null
                    qualify row_number() over (partition by county_fips order by tmax_f desc) = 1),
                coldest as (select county_fips, county, 2, 'Coldest day',
                    obs_date, cast(round(tmin_f, 0) as integer) || ' °F' from h
                    where tmin_f is not null
                    qualify row_number() over (partition by county_fips order by tmin_f asc) = 1),
                wettest as (select county_fips, county, 3, 'Wettest day',
                    obs_date, round(precip_in, 2) || ' in' from h
                    where precip_in is not null
                    qualify row_number() over (partition by county_fips order by precip_in desc) = 1),
                snowiest as (select county_fips, county, 4, 'Snowiest day',
                    obs_date, round(snow_in, 1) || ' in' from h
                    where snow_in is not null and snow_in > 0
                    qualify row_number() over (partition by county_fips order by snow_in desc) = 1)
                select county_fips, county, record_type, obs_date, value
                from (select * from hottest union all select * from coldest
                      union all select * from wettest union all select * from snowiest)
                order by county, sort_order""",
            one,
        ),
        "stations": (
            f"""select station_id, any_value(station_name) as station_name,
                county_fips, any_value(county) as county,
                avg(latitude) as latitude, avg(longitude) as longitude,
                bool_or(is_headline) as is_headline,
                avg(tmax_f) as avg_tmax_f,
                min(obs_date) as first_date, max(obs_date) as last_date, count(*) as day_count
                from {obs} {allw}
                group by station_id, county_fips order by county_fips, station_id""",
            one,
        ),
        "coverage": (
            f"""select county_fips, county,
                max(station_name) filter (where is_headline) as headline_station,
                count(distinct station_id) as station_count,
                min(obs_date) as first_date, max(obs_date) as last_date
                from {obs} {allw}
                group by county_fips, county order by county""",
            one,
        ),
    }
    return queries

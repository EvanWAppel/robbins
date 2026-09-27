"""Parameterized summaries over the same selected monitor observations."""


def air_queries(county_fips: str | None = None) -> dict[str, tuple[str, tuple]]:
    where = 'where county_fips = ?' if county_fips else ''
    params = (county_fips,) if county_fips else ()
    base = f'''with selected as (
        select * from main.mart_air_observations {where}
    ), pm as (select * from selected where pollutant like 'PM2.5%'),
    daily as (
        select * from pm
        qualify row_number() over (
            partition by obs_date order by aqi desc, site_id
        ) = 1
    ) '''
    queries = {
        'categories': '''select aqi_category, count(*) as day_count,
            case aqi_category when 'Good' then 1 when 'Moderate' then 2
            when 'Unhealthy for Sensitive Groups' then 3 when 'Unhealthy' then 4
            when 'Very Unhealthy' then 5 when 'Hazardous' then 6 end as severity
            from daily group by aqi_category order by severity''',
        'worst': '''select obs_date, aqi as max_aqi, aqi_category, site, county
            from daily order by aqi desc, obs_date desc limit 15''',
        'monthly': '''select date_trunc('month', obs_date) as obs_month, pollutant,
            avg(aqi) as avg_aqi, max(aqi) as max_aqi, count(*) as reading_count
            from selected group by 1, 2 order by 1, 2''',
        'sites': '''select site_id, max(site) as site, county,
            avg(latitude) as latitude, avg(longitude) as longitude,
            round(avg(aqi)) as avg_aqi, max(aqi) as max_aqi, count(*) as day_count
            from pm group by site_id, county order by site_id''',
        'coverage': '''select county_fips, county, pollutant,
            min(obs_date) as first_date, max(obs_date) as last_date,
            count(distinct site_id) as monitor_count, count(*) as reading_count
            from selected group by 1, 2, 3 order by 2, 3''',
    }
    return {name: (base + sql, params) for name, sql in queries.items()}

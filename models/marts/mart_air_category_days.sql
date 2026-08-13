-- How often is the metro's air Good / Moderate / worse? One row per AQI category,
-- counting days by the worst PM2.5 reading anywhere in the metro that day, so the
-- rare smoke days show up rather than being averaged away.

with pm as (
    select * from {{ ref('stg_air_quality') }}
    where pollutant like 'PM2.5%'
),

metro_daily as (
    select obs_date, aqi_category
    from pm
    qualify row_number() over (partition by obs_date order by aqi desc) = 1
)

select
    aqi_category,
    count(*) as day_count,
    case aqi_category
        when 'Good' then 1
        when 'Moderate' then 2
        when 'Unhealthy for Sensitive Groups' then 3
        when 'Unhealthy' then 4
        when 'Very Unhealthy' then 5
        when 'Hazardous' then 6
    end as severity
from metro_daily
group by 1
order by severity

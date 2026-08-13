-- The metro's worst air days: for each date, the single highest PM2.5 AQI across
-- all monitors, with the site that recorded it. These are almost all smoke days.

with pm as (
    select * from {{ ref('stg_air_quality') }}
    where pollutant like 'PM2.5%'
)

select
    obs_date,
    aqi          as max_aqi,
    aqi_category,
    site,
    county
from pm
qualify row_number() over (partition by obs_date order by aqi desc) = 1
order by max_aqi desc
limit 15

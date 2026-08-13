-- One row per PM2.5 monitor for the map: location plus its average and worst AQI
-- across the loaded window. Coordinates are averaged (they're fixed per site).

with pm as (
    select * from {{ ref('stg_air_quality') }}
    where pollutant like 'PM2.5%'
)

select
    site,
    county,
    avg(latitude)   as latitude,
    avg(longitude)  as longitude,
    round(avg(aqi)) as avg_aqi,
    max(aqi)        as max_aqi,
    count(*)        as day_count
from pm
group by site, county
order by avg_aqi desc

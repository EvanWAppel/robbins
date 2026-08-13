-- Monthly average and peak AQI by pollutant — the trend that surfaces the late-
-- summer / early-fall wildfire-smoke spikes (Sept 2020, Oct 2022, ...).

with aq as (
    select * from {{ ref('stg_air_quality') }}
)

select
    date_trunc('month', obs_date) as obs_month,
    pollutant,
    avg(aqi)                       as avg_aqi,
    max(aqi)                       as max_aqi,
    count(*)                       as reading_count
from aq
group by 1, 2
order by 1, 2

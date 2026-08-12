{{ config(materialized='table') }}

-- Hour-of-day x weekday grid for a fire 911 heatmap.

with fire as (
    select * from {{ ref('stg_fire_911') }}
    where hour_of_day is not null and weekday is not null
)

select
    weekday,
    hour_of_day,
    count(*) as call_count
from fire
group by 1, 2
order by 1, 2

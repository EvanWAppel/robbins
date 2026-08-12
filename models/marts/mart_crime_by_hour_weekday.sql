{{ config(materialized='table') }}

-- Hour-of-day x weekday grid for a crime heatmap.

with crime as (
    select * from {{ ref('stg_crime') }}
    where hour_of_day is not null and weekday is not null
)

select
    weekday,
    hour_of_day,
    count(*) as incident_count
from crime
group by 1, 2
order by 1, 2

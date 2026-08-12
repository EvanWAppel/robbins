{{ config(materialized='table') }}

with fire as (
    select * from {{ ref('stg_fire_911') }}
    where call_datetime is not null
)

select
    date_trunc('month', call_datetime) as call_month,
    count(*)                           as call_count
from fire
group by 1
order by 1

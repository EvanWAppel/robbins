{{ config(materialized='table') }}

with fire as (
    select * from {{ ref('stg_fire_911') }}
    where call_type is not null
)

select
    call_type,
    count(*) as call_count
from fire
group by 1
order by call_count desc

{{ config(materialized='table') }}

with inspections as (
    select * from {{ ref('mart_inspections') }}
    where inspection_result is not null
)

select
    inspection_result,
    count(*) as inspection_count
from inspections
group by 1
order by inspection_count desc

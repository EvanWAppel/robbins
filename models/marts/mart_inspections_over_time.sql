{{ config(materialized='table') }}

with inspections as (
    select * from {{ ref('mart_inspections') }}
    where inspection_date is not null
)

select
    date_trunc('month', inspection_date) as inspection_month,
    count(*)                             as inspection_count,
    round(avg(inspection_score), 1)      as avg_score
from inspections
group by 1
order by 1

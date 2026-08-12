{{ config(materialized='table') }}

-- Higher inspection score = worse (more violation points) in this dataset.

with inspections as (
    select * from {{ ref('mart_inspections') }}
)

select
    establishment,
    count(*)                        as inspections,
    round(avg(inspection_score), 1) as avg_score,
    sum(violation_count)            as total_violations
from inspections
group by establishment
having count(*) >= 3
order by avg_score desc

{{ config(materialized='table') }}

-- From the per-violation staging rows.

with violations as (
    select * from {{ ref('stg_food_inspections') }}
    where violation_description is not null
      and violation_description <> ''
)

select
    violation_description,
    count(*) as violation_count
from violations
group by 1
order by violation_count desc

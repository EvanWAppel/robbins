{{ config(materialized='table') }}

with permits as (
    select * from {{ ref('stg_building_permits') }}
)

select
    coalesce(permit_class, 'Unknown') as permit_class,
    count(*)                          as permit_count,
    sum(valuation)                    as total_valuation,
    round(avg(valuation), 0)          as avg_valuation
from permits
group by 1
order by permit_count desc

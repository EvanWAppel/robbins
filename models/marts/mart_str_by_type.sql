{{ config(materialized='table') }}

with rentals as (
    select * from {{ ref('stg_short_term_rentals') }}
)

select
    coalesce(propertytype, 'Unknown') as propertytype,
    count(*)                          as license_count
from rentals
group by 1
order by license_count desc

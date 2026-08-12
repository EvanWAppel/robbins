{{ config(materialized='table') }}

with rentals as (
    select * from {{ ref('stg_short_term_rentals') }}
)

select
    coalesce(geographicregion, 'Unknown') as geographicregion,
    count(*)                              as license_count
from rentals
group by 1
order by license_count desc

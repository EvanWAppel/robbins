{{ config(materialized='table') }}

with rentals as (
    select * from {{ ref('stg_short_term_rentals') }}
)

select
    licensestatus,
    count(*) as license_count
from rentals
where licensestatus is not null
group by 1
order by license_count desc

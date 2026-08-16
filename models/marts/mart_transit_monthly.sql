{{ config(materialized='table') }}

-- Total monthly boardings across all Puget Sound land-transit modes (excludes
-- ferries). The pandemic collapse and recovery is the headline.

with transit as (
    select * from {{ ref('stg_ntd_ridership') }}
    where not is_ferry
)

select
    ridership_month,
    sum(upt) as boardings
from transit
group by 1
order by 1

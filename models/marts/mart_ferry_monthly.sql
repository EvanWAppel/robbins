{{ config(materialized='table') }}

-- Total monthly ferry ridership across Puget Sound (Washington State Ferries +
-- King County Water Taxi). Strong summer seasonality plus the pandemic dip.

with ferry as (
    select * from {{ ref('stg_ntd_ridership') }}
    where is_ferry
)

select
    ridership_month,
    sum(upt) as boardings
from ferry
group by 1
order by 1

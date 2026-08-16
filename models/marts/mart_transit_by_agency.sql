{{ config(materialized='table') }}

with transit as (
    select * from {{ ref('stg_ntd_ridership') }}
    where not is_ferry
)

select
    agency_label,
    sum(upt) as boardings
from transit
group by 1
order by boardings desc

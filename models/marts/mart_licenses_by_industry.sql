{{ config(materialized='table') }}

with licenses as (
    select * from {{ ref('stg_business_licenses') }}
)

select
    coalesce(naics_description, 'Unknown') as naics_description,
    count(*)                               as license_count
from licenses
group by 1
order by license_count desc

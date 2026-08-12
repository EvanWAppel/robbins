{{ config(materialized='table') }}

with licenses as (
    select * from {{ ref('stg_business_licenses') }}
)

select
    coalesce(ownership_type, 'Unknown') as ownership_type,
    count(*)                            as license_count
from licenses
group by 1
order by license_count desc

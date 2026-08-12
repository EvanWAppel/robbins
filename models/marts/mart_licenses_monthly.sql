{{ config(materialized='table') }}

with licenses as (
    select * from {{ ref('stg_business_licenses') }}
    where start_date is not null
      and start_date >= '2005-01-01'
)

select
    date_trunc('month', start_date) as license_month,
    count(*)                        as license_count
from licenses
group by 1
order by 1

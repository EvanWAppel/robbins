{{ config(materialized='table') }}

with crime as (
    select * from {{ ref('stg_crime') }}
    where report_datetime is not null
)

select
    date_trunc('month', report_datetime) as crime_month,
    count(*)                             as incident_count
from crime
group by 1
order by 1

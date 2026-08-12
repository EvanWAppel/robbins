{{ config(materialized='table') }}

with crime as (
    select * from {{ ref('stg_crime') }}
    where offense_category is not null
)

select
    offense_category,
    count(*) as incident_count
from crime
group by 1
order by incident_count desc

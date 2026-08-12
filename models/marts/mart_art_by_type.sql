{{ config(materialized='table') }}

with art as (
    select * from {{ ref('stg_public_art') }}
)

select
    coalesce(nullif(trim(classification), ''), 'Unknown') as classification,
    count(*) as artwork_count
from art
group by 1
order by artwork_count desc

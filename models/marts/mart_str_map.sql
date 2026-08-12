{{ config(materialized='table') }}

with rentals as (
    select * from {{ ref('stg_short_term_rentals') }}
)

select
    licenseid,
    licensestatus,
    propertytype,
    geographicregion,
    latitude,
    longitude
from rentals
where latitude between 47.0 and 48.5
  and longitude between -122.6 and -121.5

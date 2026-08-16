{{ config(materialized='table') }}

-- A capped random sample of geolocated trees for the hexbin map. The full table
-- is ~212k points; we down-sample to a representative set clipped to Seattle.

with trees as (
    select
        scientific_name,
        genus,
        condition,
        is_heritage,
        latitude,
        longitude
    from {{ ref('stg_trees') }}
    where latitude between 47.4 and 47.8
      and longitude between -122.5 and -122.2
)

select * from trees using sample 15000 rows

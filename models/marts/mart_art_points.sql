{{ config(materialized='table') }}

-- Geocoded artworks for the map. Filtered to the Seattle-metro bounding box.

with art as (
    select * from {{ ref('stg_public_art') }}
    where latitude between 47.0 and 48.5
      and longitude between -122.6 and -121.5
)

select
    title,
    artist,
    classification,
    medium,
    dated,
    location,
    latitude,
    longitude
from art

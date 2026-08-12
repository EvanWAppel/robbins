{{ config(materialized='table') }}

-- A capped random sample of geolocated calls for the hexbin map. The full
-- table is too many points to render client-side, so we down-sample to a
-- representative set. Filters missing/out-of-range geo to the Seattle-metro
-- bounding box.

with fire as (
    select
        call_type,
        call_datetime,
        address,
        latitude,
        longitude
    from {{ ref('stg_fire_911') }}
    where latitude between 47.0 and 48.5
      and longitude between -122.6 and -121.5
)

select * from fire using sample 12000 rows

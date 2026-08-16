{{ config(materialized='table') }}

-- A capped random sample of geolocated requests for the hexbin map. The full
-- table is ~1.6M rows — too many to render client-side — so we down-sample to a
-- representative set, clipped to the Seattle-metro bounding box.

with csr as (
    select
        request_number,
        request_type,
        department,
        created_at,
        address,
        latitude,
        longitude
    from {{ ref('stg_csr_311') }}
    where latitude between 47.0 and 48.5
      and longitude between -122.6 and -121.5
)

select * from csr using sample 12000 rows

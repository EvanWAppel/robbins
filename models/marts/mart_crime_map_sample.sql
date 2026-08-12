{{ config(materialized='table') }}

-- A capped random sample of geolocated offenses for the hexbin map. The full
-- table is ~500k valid-geo points — too many to render client-side — so we
-- down-sample to a representative set. Filters the '-1.0'/REDACTED missing geo
-- to the Seattle-metro bounding box.

with crime as (
    select
        report_number,
        offense_category,
        offense_description,
        report_datetime,
        address,
        latitude,
        longitude
    from {{ ref('stg_crime') }}
    where latitude between 47.0 and 48.5
      and longitude between -122.6 and -121.5
)

select * from crime using sample 12000 rows

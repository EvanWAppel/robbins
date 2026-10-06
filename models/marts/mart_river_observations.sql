-- One row per gage-day of regional streamflow. Aggregated at query time
-- (per-county headline gage for charts; all gages for the map).

select
    obs_date,
    site_no,
    station_name,
    county,
    county_fips,
    latitude,
    longitude,
    is_headline,
    discharge_cfs
from {{ ref('stg_river') }}

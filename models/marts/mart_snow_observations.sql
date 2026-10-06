-- One row per station-day of regional snowpack. Aggregated at query time
-- (per-county headline station's peak SWE by water year; all stations for the map).

select
    obs_date,
    water_year,
    station_triplet,
    station_name,
    county,
    county_fips,
    latitude,
    longitude,
    is_headline,
    swe_in,
    snow_depth_in
from {{ ref('stg_snow') }}

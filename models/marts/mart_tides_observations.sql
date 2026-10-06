-- One row per station-month of regional tide datums (the five saltwater-front
-- county gauges). Aggregated at query time.

select
    obs_month,
    year,
    month,
    station_id,
    station_name,
    county,
    county_fips,
    latitude,
    longitude,
    is_headline,
    msl_ft,
    mhhw_ft,
    mllw_ft,
    range_ft,
    highest_ft,
    lowest_ft
from {{ ref('stg_tides') }}

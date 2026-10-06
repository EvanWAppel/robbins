-- One row per station-day of regional weather. The app aggregates this at query
-- time (per-county headline series for charts; all stations for the density map),
-- exactly as air quality does — so county filtering and station labeling stay
-- honest and there is a single source of truth for the topic.

select
    obs_date,
    station_id,
    station_name,
    county,
    county_fips,
    latitude,
    longitude,
    is_headline,
    precip_in,
    tmax_f,
    tmin_f,
    snow_in,
    snow_depth_in
from {{ ref('stg_weather') }}

-- Geography-preserving observations for consistent regional/county summaries.
-- This is the same collapsed daily AQI used by legacy air marts, with stable
-- EPA site IDs so identically named monitors cannot merge across counties.
select county_fips, county, site_id, site, latitude, longitude,
       obs_date, pollutant, aqi, aqi_category
from {{ ref('stg_air_quality') }}

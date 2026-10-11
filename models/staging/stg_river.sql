-- Regional daily streamflow (USGS NWIS). One row per gage-day across every active
-- daily-discharge gage in the region's counties (Island & Kitsap have none). Each
-- row carries the gage id, name, coordinates, county, and the per-county headline
-- flag (the gage with the most valid discharge days). obs_date arrives as an ISO timestamp.

with source as (
    select * from {{ source('raw', 'river') }}
)

select
    try_cast(left(obs_date, 10) as date) as obs_date,
    site_no,
    station_name,
    county                               as county_fips,
    county_name                          as county,
    try_cast(lat as double)              as latitude,
    try_cast(lon as double)              as longitude,
    is_headline,
    try_cast(discharge_cfs as double)    as discharge_cfs
from source
where try_cast(discharge_cfs as double) is not null
  -- USGS uses large negative sentinels for no-data; discharge is never negative.
  and try_cast(discharge_cfs as double) >= 0
  and try_cast(left(obs_date, 10) as date) is not null

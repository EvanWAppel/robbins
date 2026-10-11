-- Regional daily weather (NOAA GHCN-Daily). One row per station-day across every
-- temperature-reporting station in the ten-county region, 2014 onward. GHCN stores precip in tenths of a mm and
-- temperatures in tenths of a degree C (SNOW/SNWD already in mm); we divide and
-- surface US units. Station identity + county + the per-county headline flag are
-- carried through so the app can filter and label honestly.

with source as (
    select * from {{ source('raw', 'weather') }}
)

select
    try_cast("DATE" as date)                              as obs_date,
    "STATION"                                             as station_id,
    "NAME"                                                as station_name,
    county                                                as county_fips,
    county_name                                           as county,
    try_cast("LATITUDE" as double)                        as latitude,
    try_cast("LONGITUDE" as double)                       as longitude,
    is_headline,
    try_cast(trim("PRCP") as double) / 10.0 / 25.4        as precip_in,
    try_cast(trim("TMAX") as double) / 10.0 * 9 / 5 + 32  as tmax_f,
    try_cast(trim("TMIN") as double) / 10.0 * 9 / 5 + 32  as tmin_f,
    try_cast(trim("SNOW") as double) / 25.4               as snow_in,
    try_cast(trim("SNWD") as double) / 25.4               as snow_depth_in
from source
where try_cast("DATE" as date) is not null

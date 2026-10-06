-- Regional monthly tide datums (NOAA CO-OPS monthly_mean). One row per station-
-- month for the five saltwater-front region counties (only those have a long-
-- record gauge). MSL = mean sea level, GT the great diurnal range (MHHW - MLLW),
-- all in feet. Station identity + county + headline flag carried through.

with source as (
    select * from {{ source('raw', 'tides') }}
)

select
    try_cast(year as integer)                                            as year,
    try_cast(month as integer)                                           as month,
    make_date(try_cast(year as integer), try_cast(month as integer), 1)  as obs_month,
    station_id,
    station_name,
    county                                                               as county_fips,
    county_name                                                          as county,
    try_cast(lat as double)                                              as latitude,
    try_cast(lon as double)                                              as longitude,
    is_headline,
    try_cast("MSL" as double)                                            as msl_ft,
    try_cast("MHHW" as double)                                           as mhhw_ft,
    try_cast("MLLW" as double)                                           as mllw_ft,
    try_cast("GT" as double)                                             as range_ft,
    try_cast(highest as double)                                          as highest_ft,
    try_cast(lowest as double)                                           as lowest_ft
from source
where try_cast(year as integer) is not null

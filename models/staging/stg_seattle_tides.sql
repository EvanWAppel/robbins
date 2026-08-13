-- Seattle (Elliott Bay) monthly tide datums (NOAA CO-OPS 9447130). One row per
-- month; MSL is mean sea level, GT the great diurnal range (MHHW - MLLW). All
-- feet, all text from the JSON load.

with source as (
    select * from {{ source('raw', 'seattle_tides') }}
)

select
    try_cast(year as integer)                             as year,
    try_cast(month as integer)                            as month,
    make_date(try_cast(year as integer), try_cast(month as integer), 1) as obs_month,
    try_cast("MSL" as double)                             as msl_ft,
    try_cast("MHHW" as double)                            as mhhw_ft,
    try_cast("MLLW" as double)                            as mllw_ft,
    try_cast("GT" as double)                              as range_ft,
    try_cast(highest as double)                           as highest_ft,
    try_cast(lowest as double)                            as lowest_ft
from source
where try_cast(year as integer) is not null

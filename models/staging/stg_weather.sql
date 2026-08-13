-- Sea-Tac daily weather (NOAA GHCN-Daily station USW00024233, 1948-present).
-- Everything arrives as space-padded text from the CSV load. GHCN stores precip
-- in tenths of a mm and temperatures in tenths of a degree C, so divide by 10;
-- we surface both metric and Fahrenheit/inches for a US audience.

with source as (
    select * from {{ source('raw', 'weather') }}
)

select
    try_cast("DATE" as date)                          as obs_date,
    try_cast(trim("PRCP") as double) / 10.0           as precip_mm,
    try_cast(trim("PRCP") as double) / 10.0 / 25.4    as precip_in,
    try_cast(trim("SNOW") as double)                  as snow_mm,
    try_cast(trim("SNWD") as double)                  as snow_depth_mm,
    try_cast(trim("TMAX") as double) / 10.0           as tmax_c,
    try_cast(trim("TMIN") as double) / 10.0           as tmin_c,
    try_cast(trim("TMAX") as double) / 10.0 * 9 / 5 + 32 as tmax_f,
    try_cast(trim("TMIN") as double) / 10.0 * 9 / 5 + 32 as tmin_f
from source
where try_cast("DATE" as date) is not null

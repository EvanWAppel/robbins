-- Regional daily snowpack (NRCS SNOTEL). One row per station-day across every
-- active WA SNOTEL station the AWDB inventory places in a region county (lowland
-- Island/Kitsap/Thurston have none). Snow-water-equivalent and depth in inches.
-- A water year runs Oct 1 - Sep 30, so months >= October belong to the next
-- calendar year's water year. Station identity + county + headline flag carried.

with source as (
    select * from {{ source('raw', 'snow') }}
),

typed as (
    select
        try_cast(obs_date as date)        as obs_date,
        station_triplet,
        station_name,
        county                            as county_fips,
        county_name                       as county,
        try_cast(lat as double)           as latitude,
        try_cast(lon as double)           as longitude,
        is_headline,
        try_cast(swe_in as double)        as swe_in,
        try_cast(snow_depth_in as double) as snow_depth_in
    from source
    where try_cast(obs_date as date) is not null
)

select
    *,
    case
        when extract(month from obs_date) >= 10
            then extract(year from obs_date) + 1
        else extract(year from obs_date)
    end as water_year
from typed

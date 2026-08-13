-- Stampede Pass daily snowpack (NRCS SNOTEL 791:WA:SNTL). Snow water equivalent
-- and depth in inches. A water year runs Oct 1 - Sep 30, so months >= October
-- belong to the *next* calendar year's water year.

with source as (
    select * from {{ source('raw', 'snowpack') }}
),

typed as (
    select
        try_cast(obs_date as date)        as obs_date,
        try_cast(swe_in as double)        as swe_in,
        try_cast(snow_depth_in as double) as snow_depth_in
    from source
    where try_cast(obs_date as date) is not null
)

select
    obs_date,
    swe_in,
    snow_depth_in,
    case
        when extract(month from obs_date) >= 10
            then extract(year from obs_date) + 1
        else extract(year from obs_date)
    end as water_year
from typed

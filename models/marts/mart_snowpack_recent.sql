-- Daily snow-water-equivalent for the most recent three water years — the
-- accumulate-through-winter, melt-through-spring cycle, year over year.

with snow as (
    select * from {{ ref('stg_snowpack') }}
    where swe_in is not null
),

cutoff as (
    select max(water_year) - 2 as start_wy from snow
)

select
    obs_date,
    water_year,
    swe_in
from snow, cutoff
where water_year >= cutoff.start_wy
order by obs_date

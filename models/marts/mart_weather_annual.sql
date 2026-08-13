-- Annual totals: how wet was each year, and how many days actually saw rain.
-- Excludes the current (partial) year at the view layer so the trend isn't
-- misread. One row per calendar year.

with daily as (
    select * from {{ ref('stg_weather') }}
)

select
    extract(year from obs_date)                       as year,
    sum(precip_in)                                     as total_precip_in,
    count(*) filter (where precip_in > 0.01)           as rain_days,
    avg(tmax_f)                                         as avg_tmax_f,
    avg(tmin_f)                                         as avg_tmin_f
from daily
group by 1
order by 1

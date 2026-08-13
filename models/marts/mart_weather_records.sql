-- Notable extremes across the whole Sea-Tac record — the "Records" half of the
-- page. One row per record type, each carrying the date it was set and a
-- display-ready value string.

with daily as (
    select * from {{ ref('stg_weather') }}
),

hottest as (
    select 1 as sort_order, 'Hottest day' as record_type, obs_date,
           cast(round(tmax_f, 0) as integer) || ' °F' as value
    from daily where tmax_f is not null order by tmax_f desc limit 1
),

coldest as (
    select 2 as sort_order, 'Coldest day' as record_type, obs_date,
           cast(round(tmin_f, 0) as integer) || ' °F' as value
    from daily where tmin_f is not null order by tmin_f asc limit 1
),

wettest as (
    select 3 as sort_order, 'Wettest day' as record_type, obs_date,
           round(precip_in, 2) || ' in' as value
    from daily where precip_in is not null order by precip_in desc limit 1
),

snowiest as (
    select 4 as sort_order, 'Snowiest day' as record_type, obs_date,
           round(snow_mm / 25.4, 1) || ' in' as value
    from daily where snow_mm is not null order by snow_mm desc limit 1
)

select record_type, obs_date, value
from (
    select * from hottest
    union all select * from coldest
    union all select * from wettest
    union all select * from snowiest
)
order by sort_order

-- Climatology: average precip and high/low temperature by calendar month across
-- the full record. This is the chart that shows Seattle's wet-winter / dry-summer
-- signature. One row per calendar month (1-12).

with daily as (
    select * from {{ ref('stg_weather') }}
),

by_month as (
    select
        extract(month from obs_date)        as month_num,
        obs_date,
        precip_in,
        tmax_f,
        tmin_f
    from daily
)

select
    month_num,
    strftime(make_date(2000, month_num, 1), '%b')   as month_name,
    avg(precip_in)                                   as avg_precip_in,
    avg(tmax_f)                                      as avg_tmax_f,
    avg(tmin_f)                                      as avg_tmin_f
from by_month
group by 1
order by 1

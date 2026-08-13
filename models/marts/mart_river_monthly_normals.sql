-- Cedar River's seasonal signature: average daily discharge by calendar month,
-- across the record. High in the wet/snowmelt months, low in late summer.

with flow as (
    select * from {{ ref('stg_cedar_river_flow') }}
)

select
    extract(month from obs_date)                    as month_num,
    strftime(make_date(2000, extract(month from obs_date)::int, 1), '%b') as month_name,
    avg(discharge_cfs)                              as avg_discharge_cfs
from flow
group by 1, 2
order by 1

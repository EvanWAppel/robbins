-- Cedar River discharge by calendar year: the mean and the summer-low minimum.
-- Low-flow years line up with low-snowpack years (e.g. 2015).

with flow as (
    select * from {{ ref('stg_cedar_river_flow') }}
)

select
    extract(year from obs_date)  as year,
    avg(discharge_cfs)           as avg_discharge_cfs,
    min(discharge_cfs)           as min_discharge_cfs
from flow
group by 1
order by 1

-- Seattle sea level by year: average monthly MSL (the long-run trend) and the
-- average great-diurnal tidal range. Partial current year is kept; the view
-- drops it from the trend line.

with tides as (
    select * from {{ ref('stg_seattle_tides') }}
)

select
    year,
    avg(msl_ft)   as avg_msl_ft,
    avg(range_ft) as avg_range_ft,
    count(*)      as month_count
from tides
group by 1
order by 1

-- Peak snow-water-equivalent per water year at Stampede Pass — the headline
-- snowpack number. The 2015 collapse (a statewide snow-drought) stands out.

with snow as (
    select * from {{ ref('stg_snowpack') }}
    where swe_in is not null
)

select
    water_year,
    max(swe_in) as peak_swe_in
from snow
group by 1
order by 1

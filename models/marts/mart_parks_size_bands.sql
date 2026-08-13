-- Park counts by size band — Seattle's system is mostly small neighborhood parks
-- with a handful of large flagships.

with parks as (
    select * from {{ ref('stg_parks') }}
),

banded as (
    select
        case
            when area_acres < 0.5 then 'Pocket (<0.5 ac)'
            when area_acres < 5   then 'Small (0.5-5 ac)'
            when area_acres < 20  then 'Medium (5-20 ac)'
            when area_acres < 100 then 'Large (20-100 ac)'
            else 'Flagship (100+ ac)'
        end as size_band,
        case
            when area_acres < 0.5 then 1
            when area_acres < 5   then 2
            when area_acres < 20  then 3
            when area_acres < 100 then 4
            else 5
        end as sort_order
    from parks
)

select
    size_band,
    count(*) as park_count,
    sort_order
from banded
group by size_band, sort_order
order by sort_order

-- The biggest parks in the system (Discovery, Magnuson, Seward, ...).

with parks as (
    select * from {{ ref('stg_parks') }}
)

select
    name,
    round(area_acres, 1) as area_acres,
    is_water_name
from parks
order by area_acres desc
limit 15

-- One row per park for the map and the browsable list.

with parks as (
    select * from {{ ref('stg_parks') }}
)

select
    name,
    round(area_acres, 2) as area_acres,
    latitude,
    longitude,
    is_water_name
from parks
order by area_acres desc

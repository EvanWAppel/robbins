-- Seattle Parks & Recreation park boundaries (ArcGIS point layer). Area arrives
-- in square feet; convert to acres. The water flag is name-derived (attached at
-- fetch time) — the boundary layer has no amenity attributes.

with source as (
    select * from {{ source('raw', 'parks') }}
)

select
    name                                    as name,
    try_cast(area_sqft as double)           as area_sqft,
    try_cast(area_sqft as double) / 43560.0  as area_acres,
    try_cast(latitude as double)            as latitude,
    try_cast(longitude as double)           as longitude,
    cast(is_water_name as boolean)          as is_water_name
from source
where try_cast(area_sqft as double) > 0
  and try_cast(latitude as double) is not null
  and try_cast(longitude as double) is not null

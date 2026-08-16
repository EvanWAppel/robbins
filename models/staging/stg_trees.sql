-- SDOT active street trees (ArcGIS SDOT_Trees_(Active)). Genus is derived at
-- fetch time (name-derived, TDD'd). PLANTED_DATE arrives as epoch milliseconds;
-- convert to a date here and null out the obvious pre-1900 sentinel. Y/N flags
-- become booleans. Rows without geometry are filtered downstream in the map mart.

with source as (
    select * from {{ source('raw', 'trees') }}
)

select
    scientific_name                                as scientific_name,
    genus                                          as genus,
    nullif(condition, '')                          as condition,
    heritage = 'Y'                                 as is_heritage,
    exceptional = 'Y'                              as is_exceptional,
    district                                       as district,
    case
        when try_cast(planted_epoch_ms as bigint) is null then null
        when to_timestamp(try_cast(planted_epoch_ms as bigint) / 1000) < '1900-01-01'
            then null
        else cast(to_timestamp(try_cast(planted_epoch_ms as bigint) / 1000) as date)
    end                                            as planted_date,
    try_cast(latitude as double)                   as latitude,
    try_cast(longitude as double)                  as longitude
from source

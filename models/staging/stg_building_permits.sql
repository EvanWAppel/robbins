-- Regional structure permits, 2016 onward, one row per permit (PS-TOPICS-04).
-- raw.building_permits is already normalized across nine publishers by
-- regional_permits.normalize_permits (structure-permit rule, date window,
-- source-qualified permit_key, no personal names); this view only types it.
-- valuation keeps each publisher's own definition (valuation_basis): never sum
-- it across source_id.

with source as (
    select * from {{ source('raw', 'building_permits') }}
)

select
    permit_key,
    source_id,
    permit_number,
    jurisdiction,
    county_fips,
    county,
    coverage,
    scope,
    permit_class,
    status,
    try_cast(applied_date as date)          as applied_date,
    try_cast(issue_date as date)            as issue_date,
    try_cast(valuation as double)           as valuation,
    valuation_basis,
    try_cast(housing_units as integer)      as housing_units,
    address,
    try_cast(latitude as double)            as latitude,
    try_cast(longitude as double)           as longitude
from source

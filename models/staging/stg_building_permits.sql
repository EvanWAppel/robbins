-- Seattle DCI building permits (Socrata 76t5-zqzr) — light normalize of raw.

with source as (
    select * from {{ source('raw', 'building_permits') }}
)

select
    permitnum                                   as permit_number,
    permitclass                                 as permit_class,
    permitclassmapped                           as permit_class_mapped,
    permittypemapped                            as permit_type_mapped,
    permittypedesc                              as permit_type_desc,
    description                                  as description,
    try_cast(housingunitsadded as integer)      as housing_units_added,
    try_cast(estprojectcost as double)          as valuation,
    try_cast(applieddate as timestamp)::date    as applied_date,
    try_cast(issueddate as timestamp)::date     as issue_date,
    try_cast(completeddate as timestamp)::date  as completed_date,
    statuscurrent                               as status,
    originaladdress1                            as address,
    originalcity                                as city,
    originalzip                                 as zip,
    try_cast(latitude as double)                as latitude,
    try_cast(longitude as double)               as longitude
from source

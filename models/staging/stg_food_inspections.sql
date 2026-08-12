-- Public Health – Seattle & King County food establishment inspections.
-- ONE ROW PER VIOLATION; clean inspections are a single row with null violation fields.

with source as (
    select * from {{ source('raw', 'food_inspections') }}
)

select
    name                                            as establishment,
    try_cast(inspection_date as timestamp)::date    as inspection_date,
    city                                            as city,
    zip_code                                        as zip_code,
    inspection_type                                 as inspection_type,
    inspection_result                               as inspection_result,
    grade                                           as grade,
    risk_category                                   as risk_category,
    try_cast(inspection_score as double)            as inspection_score,
    violation_type                                  as violation_type,
    violation_description                           as violation_description,
    try_cast(violation_points as integer)           as violation_points,
    inspection_serial_num                           as inspection_serial_num,
    business_id                                     as business_id
from source

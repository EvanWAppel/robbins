{{ config(materialized='table') }}

-- ONE ROW PER INSPECTION: collapse the per-violation staging rows.

with inspections as (
    select * from {{ ref('stg_food_inspections') }}
    where inspection_serial_num is not null
)

select
    inspection_serial_num,
    establishment,
    inspection_date,
    inspection_result,
    grade,
    max(inspection_score)      as inspection_score,
    count(violation_type)      as violation_count
from inspections
group by inspection_serial_num, establishment, inspection_date, inspection_result, grade

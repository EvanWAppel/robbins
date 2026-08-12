-- SPD crime offenses (Socrata tazs-3rd5), recent years. Everything arrives as
-- text from the CSV load; cast here. Missing geo ('-1.0' sentinel or 'REDACTED')
-- casts to null/-1 and is filtered downstream in the map mart.

with source as (
    select * from {{ source('raw', 'crime') }}
)

select
    report_number                              as report_number,
    offense_id                                 as offense_id,
    try_cast(report_date_time as timestamp)    as report_datetime,
    try_cast(offense_date as timestamp)        as offense_datetime,
    offense_category                           as offense_category,
    offense_sub_category                       as offense_sub_category,
    nibrs_offense_code_description             as offense_description,
    nibrs_crime_against_category               as crime_against,
    block_address                              as address,
    neighborhood                               as neighborhood,
    beat                                       as beat,
    precinct                                   as precinct,
    try_cast(latitude as double)               as latitude,
    try_cast(longitude as double)              as longitude,
    dayname(try_cast(report_date_time as timestamp))            as weekday,
    extract(hour from try_cast(report_date_time as timestamp))  as hour_of_day
from source

-- Seattle 311 / Find-It-Fix-It service requests (Socrata 5ngg-rpne), recent
-- years. Everything arrives as text from the CSV load; cast here. A handful of
-- rows carry no geo — filtered downstream in the map mart.

with source as (
    select * from {{ source('raw', 'csr_311') }}
)

select
    servicerequestnumber                       as request_number,
    webintakeservicerequests                   as request_type,
    departmentname                             as department,
    methodreceivedname                         as method_received,
    servicerequeststatusname                   as status,
    try_cast(createddate as timestamp)         as created_at,
    location                                   as address,
    zipcode                                    as zipcode,
    councildistrict                            as council_district,
    policeprecinct                             as police_precinct,
    community_reporting_area                   as reporting_area,
    try_cast(latitude as double)               as latitude,
    try_cast(longitude as double)              as longitude,
    dayname(try_cast(createddate as timestamp))            as weekday,
    extract(hour from try_cast(createddate as timestamp))  as hour_of_day
from source

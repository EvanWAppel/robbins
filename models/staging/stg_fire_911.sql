-- Seattle Fire Department 911 dispatch calls. Everything arrives as text from
-- the CSV load; cast here. Latitude/longitude are mostly valid text with a
-- small % null, filtered downstream in the map mart.

with source as (
    select * from {{ source('raw', 'fire_911') }}
)

select
    incident_number                            as incident_number,
    type                                       as call_type,
    try_cast(datetime as timestamp)            as call_datetime,
    address                                    as address,
    try_cast(latitude as double)               as latitude,
    try_cast(longitude as double)              as longitude,
    dayname(try_cast(datetime as timestamp))            as weekday,
    extract(hour from try_cast(datetime as timestamp))  as hour_of_day
from source

-- EPA AQS daily PM2.5 + Ozone for the Seattle metro. A monitor can report a few
-- rows per day (multiple POCs); collapse to one value per site/day/pollutant by
-- averaging, then bucket the AQI into the EPA category bands.

with source as (
    select * from {{ source('raw', 'air_quality') }}
),

deduped as (
    select
        county_name                              as county,
        local_site_name                          as site,
        try_cast(latitude as double)             as latitude,
        try_cast(longitude as double)            as longitude,
        try_cast(date_local as date)             as obs_date,
        parameter_name                           as pollutant,
        max(units)                               as units,
        avg(try_cast(arithmetic_mean as double)) as concentration,
        avg(try_cast(aqi as double))             as aqi
    from source
    group by 1, 2, 3, 4, 5, 6
)

select
    county,
    site,
    latitude,
    longitude,
    obs_date,
    pollutant,
    units,
    concentration,
    round(aqi)                                   as aqi,
    case
        when aqi <= 50  then 'Good'
        when aqi <= 100 then 'Moderate'
        when aqi <= 150 then 'Unhealthy for Sensitive Groups'
        when aqi <= 200 then 'Unhealthy'
        when aqi <= 300 then 'Very Unhealthy'
        else 'Hazardous'
    end                                          as aqi_category
from deduped
where obs_date is not null

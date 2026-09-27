-- EPA AQS daily PM2.5 + Ozone for configured Puget Sound counties. A monitor can report a few
-- rows per day (multiple POCs); collapse to one value per site/day/pollutant by
-- averaging, then bucket the AQI into the EPA category bands.

with source as (
    select * from {{ source('raw', 'air_quality') }}
),

deduped as (
    select
        lpad(cast(try_cast(state_code as integer) as varchar), 2, '0') ||
        lpad(cast(try_cast(county_code as integer) as varchar), 3, '0') as county_fips,
        lpad(cast(try_cast(state_code as integer) as varchar), 2, '0') ||
        lpad(cast(try_cast(county_code as integer) as varchar), 3, '0') ||
        lpad(cast(try_cast(site_num as integer) as varchar), 4, '0') as site_id,
        max(county_name)                         as county,
        max(local_site_name)                     as site,
        avg(try_cast(latitude as double))        as latitude,
        avg(try_cast(longitude as double))       as longitude,
        try_cast(date_local as date)             as obs_date,
        parameter_name                           as pollutant,
        max(units)                               as units,
        avg(try_cast(arithmetic_mean as double)) as concentration,
        avg(try_cast(aqi as double))             as aqi
    from source
    group by 1, 2, 7, 8
)

select
    county_fips,
    site_id,
    county,
    coalesce(nullif(site, ''), site_id) as site,
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
where obs_date is not null and aqi is not null

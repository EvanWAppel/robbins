-- Seattle short-term rental licenses — light normalize of raw.

with source as (
    select * from {{ source('raw', 'short_term_rentals') }}
)

select
    licenseid                                          as licenseid,
    licensestatus                                      as licensestatus,
    try_cast(licenseexpirationdate as timestamp)::date as expiration_date,
    propertytype                                       as propertytype,
    geographicregion                                   as geographicregion,
    primaryresidence                                   as primaryresidence,
    city                                               as city,
    zipcode                                            as zipcode,
    try_cast(latitude as double)                       as latitude,
    try_cast(longitude as double)                      as longitude
from source

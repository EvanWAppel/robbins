-- Seattle active business license tax certificates — light normalize of raw.

with source as (
    select * from {{ source('raw', 'business_licenses') }}
)

select
    business_legal_name                                                as business_legal_name,
    trade_name                                                         as trade_name,
    ownership_type                                                     as ownership_type,
    naics_code                                                         as naics_code,
    naics_description                                                  as naics_description,
    try_cast(strptime(nullif(license_start_date, ''), '%Y%m%d') as date) as start_date,
    city                                                               as city,
    zip                                                                as zip
from source

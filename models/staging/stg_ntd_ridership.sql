-- Puget Sound monthly ridership (FTA NTD). Source agency/mode/service-type/month records. The
-- friendly agency label, human mode label, and ferry flag are attached at fetch
-- time; here we just cast. upt = unlinked passenger trips (boardings).

with source as (
    select * from {{ source('raw', 'ntd_ridership') }}
)

select
    agency                                     as agency,
    agency_label                               as agency_label,
    mode                                       as mode_code,
    tos                                        as service_type,
    mode_label                                 as mode_label,
    cast(is_ferry as boolean)                  as is_ferry,
    cast(try_cast(date as timestamp) as date)  as ridership_month,
    try_cast(upt as bigint)                    as upt
from source
where try_cast(upt as bigint) is not null

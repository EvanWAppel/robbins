{{ config(materialized='table') }}

-- Ferry ridership by operator. Washington State Ferries is the nation's largest
-- ferry system; everything else here is the King County Water Taxi (some of which
-- NTD reports under the King County agency), so non-WSF ferry rolls up to it.

with ferry as (
    select * from {{ ref('stg_ntd_ridership') }}
    where is_ferry
)

select
    case
        when agency = 'Washington State Ferries' then 'Washington State Ferries'
        else 'King County Water Taxi'
    end      as operator,
    sum(upt) as boardings
from ferry
group by 1
order by boardings desc

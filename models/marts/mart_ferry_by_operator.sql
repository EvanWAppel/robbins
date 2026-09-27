{{ config(materialized='table') }}

-- Preserve each operator; only the two known King County reporting names
-- map to Water Taxi. Never collapse new ferry systems into that operator.

with ferry as (
    select * from {{ ref('stg_ntd_ridership') }}
    where is_ferry
)

select
    case
        when agency in ('King County', 'King County Ferry District') then 'King County Water Taxi'
        else agency_label
    end      as operator,
    sum(upt) as boardings
from ferry
group by 1
order by boardings desc

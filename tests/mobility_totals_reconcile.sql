-- All valid source boardings must land in exactly one of land transit or ferries.
with source_total as (
    select sum(try_cast(upt as bigint)) as boardings
    from {{ source('raw', 'ntd_ridership') }}
), mart_total as (
    select (select sum(boardings) from {{ ref('mart_transit_monthly') }})
         + (select sum(boardings) from {{ ref('mart_ferry_monthly') }}) as boardings
)
select source_total.boardings as source_boardings, mart_total.boardings as mart_boardings
from source_total cross join mart_total
where source_total.boardings is distinct from mart_total.boardings

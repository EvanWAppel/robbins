{{ config(materialized='table') }}

-- Sound Transit Link light rail, monthly — the metro's clearest post-pandemic
-- growth story as new stations (Northgate, East Link) opened. Kept separate from
-- the bus-dominated total so the rail trajectory is legible.

with rail as (
    select * from {{ ref('stg_ntd_ridership') }}
    where mode_code = 'LR'
)

select
    ridership_month,
    sum(upt) as boardings
from rail
group by 1
order by 1

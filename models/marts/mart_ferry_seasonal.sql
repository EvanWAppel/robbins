{{ config(materialized='table') }}

-- Average ridership by calendar month — the summer-tourism seasonality that makes
-- ferries a useful Puget Sound travel proxy (the dropped Tourism topic's stand-in).

with ferry as (
    select * from {{ ref('stg_ntd_ridership') }}
    where is_ferry
),

monthly as (
    select
        ridership_month,
        sum(upt) as boardings
    from ferry
    group by 1
)

select
    extract(month from ridership_month) as month_of_year,
    avg(boardings)                      as avg_boardings
from monthly
group by 1
order by 1

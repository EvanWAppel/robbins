{{ config(materialized='table') }}

-- Annual ferry ridership. The current (partial) year is flagged so the view can
-- avoid drawing a misleading short bar.

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
    extract(year from ridership_month) as ridership_year,
    sum(boardings)                     as boardings,
    count(*)                           as months_reported
from monthly
group by 1
order by 1

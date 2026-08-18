{{
    config(
        materialized='incremental',
        unique_key='issue_month',
        incremental_strategy='delete+insert',
    )
}}

-- Incremental rollup of building permits per month.
--
-- Full refresh builds every month; an incremental run reprocesses only the
-- trailing window (current + prior month) to catch permits whose issue_date lands
-- late, then delete+insert swaps those months in by unique_key. Idempotent. See
-- the note in mart_crime_monthly on the full-refresh-in-production build model.

with permits as (
    select * from {{ ref('stg_building_permits') }}
    where issue_date is not null
    {% if is_incremental() %}
      and issue_date >= (select max(issue_month) - interval 1 month from {{ this }})
    {% endif %}
)

select
    date_trunc('month', issue_date) as issue_month,
    count(*)                        as permit_count,
    sum(valuation)                  as total_valuation,
    round(avg(valuation), 0)        as avg_valuation
from permits
group by 1
order by 1

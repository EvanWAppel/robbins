{{
    config(
        materialized='incremental',
        unique_key='crime_month',
        incremental_strategy='delete+insert',
    )
}}

-- Incremental time-series rollup of offenses per month.
--
-- Full refresh builds every month; an incremental run reprocesses only the
-- trailing window (the current + prior month) so late-arriving offenses are
-- picked up, then delete+insert swaps just those months back in by unique_key.
-- Idempotent — re-running never double-counts.
--
-- NB: in production the warehouse is baked from scratch on every deploy
-- (build_warehouse.py + Dockerfile), so this always runs as a full refresh
-- there. The incremental path is real and exercised locally; it demonstrates
-- the pattern (idempotency, late-data, backfills) honestly. See mart_build_info.

with crime as (
    select * from {{ ref('stg_crime') }}
    where report_datetime is not null
    {% if is_incremental() %}
      and report_datetime >= (select max(crime_month) - interval 1 month from {{ this }})
    {% endif %}
)

select
    date_trunc('month', report_datetime) as crime_month,
    count(*)                             as incident_count
from crime
group by 1
order by 1

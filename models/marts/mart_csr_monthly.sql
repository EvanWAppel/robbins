{{
    config(
        materialized='incremental',
        unique_key='request_month',
        incremental_strategy='delete+insert',
    )
}}

-- Incremental rollup of 311 requests per month (~1.65M source rows).
--
-- Full refresh builds every month; an incremental run reprocesses only the
-- trailing window (current + prior month) to catch late-arriving requests, then
-- delete+insert swaps those months in by unique_key. Idempotent. See the note in
-- mart_crime_monthly on the full-refresh-in-production build model.

with csr as (
    select * from {{ ref('stg_csr_311') }}
    where created_at is not null
    {% if is_incremental() %}
      and created_at >= (select max(request_month) - interval 1 month from {{ this }})
    {% endif %}
)

select
    date_trunc('month', created_at) as request_month,
    count(*)                        as request_count
from csr
group by 1
order by 1

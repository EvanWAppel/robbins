{{ config(materialized='table') }}

with csr as (
    select * from {{ ref('stg_csr_311') }}
    where created_at is not null
)

select
    date_trunc('month', created_at) as request_month,
    count(*)                        as request_count
from csr
group by 1
order by 1

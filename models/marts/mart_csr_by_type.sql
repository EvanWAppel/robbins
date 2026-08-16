{{ config(materialized='table') }}

with csr as (
    select * from {{ ref('stg_csr_311') }}
    where request_type is not null
)

select
    request_type,
    count(*) as request_count
from csr
group by 1
order by request_count desc

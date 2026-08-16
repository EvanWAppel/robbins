{{ config(materialized='table') }}

with csr as (
    select * from {{ ref('stg_csr_311') }}
    where department is not null
)

select
    department,
    count(*) as request_count
from csr
group by 1
order by request_count desc

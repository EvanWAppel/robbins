{{ config(materialized='table') }}

-- How residents file requests — the Find-It-Fix-It mobile app vs. web vs. phone.
-- Tells the "digital civic engagement" story behind the topic.

with csr as (
    select * from {{ ref('stg_csr_311') }}
    where method_received is not null
)

select
    method_received,
    count(*) as request_count
from csr
group by 1
order by request_count desc

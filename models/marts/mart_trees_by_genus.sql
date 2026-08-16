{{ config(materialized='table') }}

with trees as (
    select * from {{ ref('stg_trees') }}
    where genus is not null
)

select
    genus,
    count(*) as tree_count
from trees
group by 1
order by tree_count desc

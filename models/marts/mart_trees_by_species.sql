{{ config(materialized='table') }}

with trees as (
    select * from {{ ref('stg_trees') }}
    where scientific_name is not null
)

select
    scientific_name,
    count(*) as tree_count
from trees
group by 1
order by tree_count desc

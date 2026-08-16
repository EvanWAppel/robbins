{{ config(materialized='table') }}

-- Condition is only recorded for a subset of the inventory; the null bucket is
-- kept as "Not assessed" so the share of assessed trees is visible.

with trees as (
    select * from {{ ref('stg_trees') }}
)

select
    coalesce(condition, 'Not assessed') as condition,
    count(*)                            as tree_count
from trees
group by 1
order by tree_count desc

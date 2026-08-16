{{ config(materialized='table') }}

-- Recorded planting year (only a portion of trees carry a planted date). Capped
-- to 1970+ so the chart reflects the modern street-tree program, not stragglers.

with trees as (
    select * from {{ ref('stg_trees') }}
    where planted_date is not null
      and planted_date >= '1970-01-01'
      and planted_date <= current_date  -- a few rows carry future (planned) dates
)

select
    extract(year from planted_date) as plant_year,
    count(*)                        as tree_count
from trees
group by 1
order by 1

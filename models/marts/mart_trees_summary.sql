{{ config(materialized='table') }}

-- One-row headline summary for the KPI cards.

with trees as (
    select * from {{ ref('stg_trees') }}
)

select
    count(*)                                       as total_trees,
    count(distinct scientific_name)                as distinct_species,
    count(distinct genus)                          as distinct_genera,
    sum(case when is_heritage then 1 else 0 end)   as heritage_trees,
    sum(case when is_exceptional then 1 else 0 end) as exceptional_trees
from trees

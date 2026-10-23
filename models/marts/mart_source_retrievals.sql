{{ config(materialized='table') }}

-- Retrieval freshness per raw source table — the "when was this fetched" surface
-- the Data Coverage page shows next to observation dates. One row per raw table,
-- keeping the latest retrieval should a source ever be recorded twice.

select
    source_id,
    max(retrieved_at)                    as retrieved_at,
    arg_max(row_count, retrieved_at)     as row_count
from {{ ref('stg_source_retrievals') }}
group by source_id

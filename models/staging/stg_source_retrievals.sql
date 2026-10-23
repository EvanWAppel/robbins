-- When each raw table was retrieved. build_warehouse.record_retrieval writes one
-- row per raw table (source_id = raw table name) as it loads it, so this is the
-- upstream-fetch time, distinct from observation dates and from mart_build_info's
-- dbt build time. Timestamps are UTC.

with source as (
    select * from {{ source('raw', 'source_retrievals') }}
)

select
    source_id,
    cast(retrieved_at as timestamp) as retrieved_at,
    cast(row_count as bigint)       as row_count
from source

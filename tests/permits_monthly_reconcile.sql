-- Every issued staging permit lands in exactly one monthly bucket, per publisher.
with staged as (
    select source_id, count(*) as permits
    from {{ ref('stg_building_permits') }}
    where issue_date is not null
    group by source_id
), mart as (
    select source_id, sum(permit_count) as permits
    from {{ ref('mart_permits_monthly') }}
    group by source_id
)
select coalesce(s.source_id, m.source_id) as source_id,
       s.permits as staged_permits, m.permits as mart_permits
from staged s full outer join mart m using (source_id)
where s.permits is distinct from m.permits

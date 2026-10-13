{{ config(severity='warn') }}
-- Per-publisher freshness: the source-level freshness check takes max(issue_date)
-- over all nine publishers, so a fresh Seattle would hide a frozen feed (the
-- reason Auburn was rejected). Warn when any one publisher stops issuing.
-- TRPC (Thurston) is compiled from jurisdictions annually, so it gets a year+.
select source_id, max(issue_date) as last_issued
from {{ ref('stg_building_permits') }}
group by source_id
having max(issue_date) < current_date - (
    case when source_id = 'trpc.permits' then 400 else 90 end
) * interval 1 day

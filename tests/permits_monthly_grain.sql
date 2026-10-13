-- mart_permits_monthly is one row per month x publisher x jurisdiction.
select issue_month, source_id, jurisdiction, count(*) as n
from {{ ref('mart_permits_monthly') }}
group by 1, 2, 3
having count(*) > 1

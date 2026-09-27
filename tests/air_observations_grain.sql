-- One observation per stable monitor/day/pollutant, regardless of name changes.
select site_id, obs_date, pollutant, count(*) as records
from {{ ref('mart_air_observations') }}
group by 1, 2, 3
having count(*) > 1

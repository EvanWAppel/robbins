-- Cedar River at Renton daily streamflow (USGS NWIS 12119000). obs_date arrives
-- as an ISO timestamp string; keep the date, cast discharge to a number.

with source as (
    select * from {{ source('raw', 'cedar_river_flow') }}
)

select
    try_cast(left(obs_date, 10) as date) as obs_date,
    try_cast(value as double)            as discharge_cfs
from source
where try_cast(value as double) is not null
  and try_cast(left(obs_date, 10) as date) is not null

{{ config(materialized='table') }}

-- Recent geocoded permits for the PyDeck map. Bounded to keep the layer light
-- and filtered to plausible Seattle-metro coordinates.
with permits as (
    select * from {{ ref('stg_building_permits') }}
    where issue_date is not null
      and latitude between 47.0 and 48.5
      and longitude between -122.6 and -121.5
)

select
    permit_number,
    permit_class,
    permit_type_desc,
    valuation,
    issue_date,
    address,
    latitude,
    longitude
from permits
order by issue_date desc
limit 5000

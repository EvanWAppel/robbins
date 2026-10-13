{{ config(materialized='table') }}

-- Recent geocoded permits for the PyDeck map: the 2,000 most recent per
-- publisher, so small jurisdictions stay represented next to Seattle. A sample,
-- not a count — never aggregate it. Out-of-region coordinates were nulled at
-- ingest, so no bounding box is needed here.
with permits as (
    select
        *,
        row_number() over (
            partition by source_id order by issue_date desc, permit_key
        ) as recency_rank
    from {{ ref('stg_building_permits') }}
    where issue_date is not null
      and latitude is not null
      and longitude is not null
)

select
    permit_key,
    source_id,
    permit_number,
    jurisdiction,
    county_fips,
    county,
    permit_class,
    valuation,
    valuation_basis,
    issue_date,
    address,
    latitude,
    longitude
from permits
where recency_rank <= 2000
order by issue_date desc

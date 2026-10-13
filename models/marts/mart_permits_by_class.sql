{{ config(materialized='table') }}

-- Issued structure permits by the publisher's own permit type label, per
-- jurisdiction. Labels are not harmonized across publishers (each has its own
-- vocabulary), so compare classes within one source_id.

with permits as (
    select * from {{ ref('stg_building_permits') }}
    where issue_date is not null
)

select
    source_id,
    jurisdiction,
    county_fips,
    any_value(county)                 as county,
    coalesce(permit_class, 'Unknown') as permit_class,
    any_value(valuation_basis)        as valuation_basis,
    count(*)                          as permit_count,
    sum(valuation)                    as total_valuation,
    round(avg(valuation), 0)          as avg_valuation
from permits
group by source_id, jurisdiction, county_fips, coalesce(permit_class, 'Unknown')
order by permit_count desc

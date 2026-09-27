{{ config(materialized='table') }}

-- Coverage of loaded agency reports, not county-level ridership allocation.
select agency,
       case when is_ferry and agency in ('King County', 'King County Ferry District')
            then 'King County Water Taxi' else agency_label end as agency_label,
       is_ferry,
       min(ridership_month) as first_month,
       max(ridership_month) as last_month,
       count(distinct ridership_month) as months_reported,
       sum(upt) as boardings
from {{ ref('stg_ntd_ridership') }}
group by 1, 2, 3

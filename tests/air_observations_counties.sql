-- Approved administrative scope; other Washington counties must not leak in.
select county_fips
from {{ ref('mart_air_observations') }}
where county_fips not in (
    '53029', '53031', '53033', '53035', '53045',
    '53053', '53057', '53061', '53067', '53073'
)

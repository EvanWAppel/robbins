-- GENERATED from metrics.yml by generate_metrics_model.py — do not edit by hand.
-- The semantic layer: each metric is declared once in metrics.yml and compiled
-- here, so dbt builds/tests/documents it and the app reads it by name.
{{ config(materialized='table') }}

select
    'total_permits' as metric_name,
    'Building permits' as label,
    'Total building permits issued in the loaded window.' as description,
    'count' as unit,
    (select cast(sum(permit_count) as double) from {{ ref('mart_permits_monthly') }}) as value
union all
select
    'total_permit_valuation' as metric_name,
    'Permit valuation' as label,
    'Summed estimated project cost across issued permits (USD).' as description,
    'usd' as unit,
    (select cast(sum(total_valuation) as double) from {{ ref('mart_permits_monthly') }}) as value
union all
select
    'total_crime_offenses' as metric_name,
    'Crime offenses' as label,
    'Total SPD offenses reported in the loaded window.' as description,
    'count' as unit,
    (select cast(sum(incident_count) as double) from {{ ref('mart_crime_monthly') }}) as value
union all
select
    'total_fire_calls' as metric_name,
    'Fire 911 calls' as label,
    'Total Seattle Fire 911 dispatches in the loaded window.' as description,
    'count' as unit,
    (select cast(sum(call_count) as double) from {{ ref('mart_fire_monthly') }}) as value
union all
select
    'total_311_requests' as metric_name,
    '311 requests' as label,
    'Total Find-It-Fix-It / customer service requests in the loaded window.' as description,
    'count' as unit,
    (select cast(sum(request_count) as double) from {{ ref('mart_csr_monthly') }}) as value
union all
select
    'total_inspections' as metric_name,
    'Food inspections' as label,
    'Total food-establishment inspections on record.' as description,
    'count' as unit,
    (select cast(count(*) as double) from {{ ref('mart_inspections') }}) as value
union all
select
    'total_street_trees' as metric_name,
    'Street trees' as label,
    'Trees in the SDOT active street-tree inventory.' as description,
    'count' as unit,
    (select cast(max(total_trees) as double) from {{ ref('mart_trees_summary') }}) as value
union all
select
    'pct_good_or_moderate_air_days' as metric_name,
    'Good/Moderate air days' as label,
    'Share of metro-days whose worst PM2.5 reading was Good or Moderate.' as description,
    'percent' as unit,
    (select cast(round(100.0 * sum(day_count) filter (where aqi_category in ('Good', 'Moderate')) / nullif(sum(day_count), 0)) as double) from {{ ref('mart_air_category_days') }}) as value
union all
select
    'total_transit_boardings' as metric_name,
    'Transit boardings' as label,
    'Total land-transit boardings (UPT) across Puget Sound agencies.' as description,
    'count' as unit,
    (select cast(sum(boardings) as double) from {{ ref('mart_transit_by_agency') }}) as value
union all
select
    'total_ferry_boardings' as metric_name,
    'Ferry boardings' as label,
    'Total ferry boardings (UPT) across Puget Sound operators.' as description,
    'count' as unit,
    (select cast(sum(boardings) as double) from {{ ref('mart_ferry_by_operator') }}) as value
order by metric_name

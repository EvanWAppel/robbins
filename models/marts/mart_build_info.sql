{{ config(materialized='table') }}

-- Warehouse build metadata — the data-freshness surface. One row, read by the
-- Overview page for its "Warehouse built <date> · N records" banner and available
-- to any AI agent grounding on the catalog (see catalog/).
--
-- built_at is dbt's run_started_at (the moment this `dbt build` began), rendered
-- as a literal so it's frozen into the baked warehouse. Because production rebuilds
-- the warehouse from scratch on every deploy, built_at is genuinely "when this
-- deploy's data was loaded" — an honest freshness signal, not a stored clock.
--
-- total_records reuses the exact nine grain counts the Overview headline reports,
-- so the number is defined here once instead of re-summed in Python.

select
    cast('{{ run_started_at.strftime("%Y-%m-%dT%H:%M:%S") }}' as timestamp) as built_at,
    (
        (select sum(permit_count)  from {{ ref('mart_permits_monthly') }})
      + (select sum(incident_count) from {{ ref('mart_crime_monthly') }})
      + (select sum(call_count)     from {{ ref('mart_fire_monthly') }})
      + (select count(*)            from {{ ref('mart_inspections') }})
      + (select sum(request_count)  from {{ ref('mart_csr_monthly') }})
      + (select sum(license_count)  from {{ ref('mart_licenses_by_industry') }})
      + (select sum(artwork_count)  from {{ ref('mart_art_by_type') }})
      + (select count(*)            from {{ ref('mart_parks_points') }})
      + (select total_trees         from {{ ref('mart_trees_summary') }})
    ) as total_records

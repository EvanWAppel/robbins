-- Crime density by SPD MCPP neighborhood. Every geolocated offense is assigned
-- to a neighborhood by point-in-polygon (spatial extension), then normalized by
-- the neighborhood's area. The bbox prefilter (lon/lat BETWEEN min/max) keeps
-- ST_Contains to ~one candidate polygon per point, so the join stays fast even
-- over the full offense table. Neighborhoods with no offenses stay at 0.
with mcpp as (
    select * from {{ source('raw', 'mcpp') }}
),

poly as (
    select
        neighborhood,
        minx, miny, maxx, maxy,
        ST_GeomFromGeoJSON(geojson) as geom
    from mcpp
),

pts as (
    select longitude as lon, latitude as lat
    from {{ ref('stg_crime') }}
    where latitude between 47.0 and 48.5
      and longitude between -122.6 and -121.5
),

counts as (
    select n.neighborhood, count(*) as incident_count
    from pts p
    join poly n
      on p.lon between n.minx and n.maxx
     and p.lat between n.miny and n.maxy
     and ST_Contains(n.geom, ST_Point(p.lon, p.lat))
    group by 1
)

select
    m.neighborhood,
    m.precinct,
    m.area_sq_miles,
    m.rings_json,
    m.centroid_lon,
    m.centroid_lat,
    coalesce(c.incident_count, 0)                              as incident_count,
    coalesce(c.incident_count, 0) / nullif(m.area_sq_miles, 0) as incidents_per_sq_mile
from mcpp m
left join counts c using (neighborhood)
order by incidents_per_sq_mile desc

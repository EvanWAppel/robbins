-- Seattle public art (ArcGIS PublicArt2). Coordinates are geometry-derived
-- (source LAT/LON attrs were 0 and dropped at fetch time).

with source as (
    select * from {{ source('raw', 'public_art') }}
)

select
    "TITLE"       as title,
    "ARTIST_NAM"  as artist,
    "CLASSIFICA"  as classification,
    "MEDIUM"      as medium,
    "DATED"       as dated,
    "LOCATION__"  as location,
    "DESCRIPTIO"  as description,
    latitude      as latitude,
    longitude     as longitude
from source

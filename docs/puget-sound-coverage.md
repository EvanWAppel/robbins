# Puget Sound source coverage audit

Updated 2026-10-12. This matrix audits configured integrations, not live data
completeness. See Data Coverage in the app for loaded air observations and dates.

**Codes:** S = Seattle-only integration (partial King County); K = King County
inspection jurisdiction; A = county filter configured for EPA monitors (actual
pollutant/date coverage must be checked); T = agency totals, county allocation
unavailable; P = station series, broader coverage unverified; M = some municipal or
county publishers integrated (partial — see the gap note); G = searched 2026-10-11, no
usable public machine-readable source found; U = regional source not yet verified or
integrated. U does not mean no public source exists.

| Topic | Island | Jefferson | King | Kitsap | Mason | Pierce | Skagit | Snohomish | Thurston | Whatcom |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 311 Requests | U | U | S | U | U | U | U | U | U | U |
| Air Quality | A | A | A | A | A | A | A | A | A | A |
| Building Permits | G | G | M | M | G | M | G | M | M | M |
| Business Licenses | U | U | S | U | U | U | U | U | U | U |
| Crime | U | U | S | U | U | U | U | U | U | U |
| Ferry Ridership | T | T | T | T | T | T | T | T | T | T |
| Fire 911 Calls | U | U | S | U | U | U | U | U | U | U |
| Parks | U | U | S | U | U | U | U | U | U | U |
| Public Art | U | U | S | U | U | U | U | U | U | U |
| Rain & Records | U | U | P | U | U | U | U | U | U | U |
| Restaurant Inspections | U | U | K | U | U | U | U | U | U | U |
| Short-Term Rentals | U | U | S | U | U | U | U | U | U | U |
| Street Trees | U | U | S | U | U | U | U | U | U | U |
| Transit Ridership | T | T | T | T | T | T | T | T | T | T |
| Water | U | U | P | U | U | U | U | U | U | U |

The station row identifies the existing Seattle-area series, not an assertion
that every station is assigned to King County. Station-to-county crosswalks remain
to be verified. Ferry/transit agencies may serve multiple counties; their totals
are intentionally not added to county totals.

## Source verification for the first slice

- County IDs: [Census county code reference](https://www2.census.gov/geo/docs/reference/codes2020/national_county2020.txt), checked 2026-09-27.
- EPA file availability: [AirData downloads](https://aqs.epa.gov/aqsweb/airdata/download_files.html), checked 2026-09-27.
- Schema/grain: [EPA file documentation](https://aqs.epa.gov/aqsweb/airdata/FileFormats.html), checked 2026-09-27. Stable monitor identifiers use state, county, and site codes.
- Existing integration metadata and limitations: `city_config.DATA_SOURCES`.

## Remaining discovery

For each U cell, verify official publisher, URL, reuse terms, record grain,
observation period, update cadence, and overlap before adding a source. For each
A/P/T cell, verify extent and comparability before calling it county-wide coverage.
Reuse terms and source completeness beyond the existing integrations remain open.
The first release does not promise city filters or regional civic completeness.


## Local air rebuild validation — 2026-09-27

The EPA refresh completed in approximately 6 minutes 25 seconds and loaded
46,193 AQI-bearing raw records across the configured years/pollutants. The
normalized mart has observations in King, Kitsap, Pierce, Skagit, Snohomish,
Thurston, and Whatcom. Island, Jefferson, and Mason have no loaded observations
for this source configuration; this is not a claim that those counties have no
monitoring or no pollution. Observations currently extend through February 2026,
so this release is a historical explorer, not a current-conditions service.

Selected dbt build: 7 models and 18 data tests passed. Synthetic/parser/UI suite:
98 tests passed. The 55 summary queries (five summaries × region plus ten county
selections) took 1.206 seconds in one local read-only benchmark; the warehouse was
270.5 MiB. This is not a production latency SLA, full-app build benchmark, or
peak-memory measurement.

Browser checks verified regional and Kitsap summaries, Island's missing-data
state, selection persistence across topic navigation, source inventory, and the
390×844 mobile layout including Kitsap's single-monitor map. Production deployment,
full Docker rehearsal, and live Ask the Data API validation were not performed.


## Mobility continuation — 2026-09-27

The official [FTA monthly ridership feed](https://data.transportation.gov/d/8bui-9xvu)
was queried for Washington agency names, aggregate record counts, and reporting
windows before changing configuration. Five additional reporting agencies are
now integrated: Kitsap Transit, Skagit Transit, Whatcom Transportation Authority,
Intercity Transit, and County of Pierce (Pierce County Ferry). Official agency
references include [Kitsap](https://www.transit.dot.gov/ntd/transit-agency-profiles/kitsap-transit),
[Skagit](https://www.transit.dot.gov/ntd/transit-agency-profiles/skagit-transit),
[Whatcom](https://www.transit.dot.gov/ntd/transit-agency-profiles/whatcom-transportation-authority),
and [Pierce County Ferry](https://www.piercecountywa.gov/ferry).

Island Transit, Jefferson Transit Authority, and Mason Transit were absent from
the monthly feed's 2015+ Washington agency inventory. Their annual reports or
other datasets require separate discovery; absence from this feed is not zero
ridership. The T cells above remain agency totals without county allocation.

The local rebuild loaded 6,053 source rows across 13 reporting agencies. Combined
transit/ferry mart boardings reconcile to the source aggregate. Ferry aggregation
now preserves WSF, Water Taxi, Kitsap Transit, and Pierce County Ferry separately;
only the two known King County reporting names share the Water Taxi label.
Reporting windows and distinct month counts appear in both pages and Data Coverage.
Twelve observed calendar months do not establish complete reporting by every operator.

Mobility validation: 102 pytest tests, Ruff, and ty passed; 19 selected dbt
model/test steps plus the source-total reconciliation test passed. The two King
County ferry reporting names have no overlapping loaded months. Transit, ferry,
and Data Coverage page smoke checks passed; browser inspection confirmed the
four-operator ferry chart and coverage labels. No deployment performed.

## Building permits (PS-TOPICS-04) — sources searched 2026-10-11

Integrated (structure permits, issued 2016+; rules in `city_config.PERMIT_SOURCES`):
Seattle DCI, Bellevue (King); unincorporated Pierce County, Tacoma, Puyallup (Pierce);
Everett (Snohomish); Bellingham (Whatcom); unincorporated Kitsap County, submissions
since 2020 (Kitsap); Thurston Regional Planning Council — unincorporated Thurston plus
Lacey, Olympia, Tumwater, Yelm and smaller jurisdictions, residential new construction
and demolition only (Thurston).

Gaps (per-county notes in `city_config.PERMIT_GAPS`, shown on the page): no
machine-readable permit history for unincorporated King County, Kent, Federal Way,
Redmond, Kirkland, Lakewood, Bremerton, Mount Vernon and most other cities; Snohomish,
Skagit and Island counties publish only active-permit snapshots; Whatcom and Mason
county services require a login token; Jefferson County publishes septic permits only;
Auburn's feed stopped updating in 2025-02 and has no coordinates; Renton and SeaTac
publish active permits only. Duplicate copies (Pierce's ArcGIS mirror, Bellevue's
archive layer, Everett's derived views) are deliberately not loaded.

## Parks, trees and public art (PS-TOPICS-05) — sources searched 2026-10-22

Research only. Nothing below is wired, and the matrix codes above are unchanged.
Every row is a *candidate*: a public, keyless, machine-readable endpoint that answered
on 2026-10-22. None is verified for completeness, and none has an owner decision on
definitions, windows or overlap. The Parks, Public Art and Street Trees rows stay `U`
outside Seattle. `U` means "not yet verified or integrated", and that is still true.
No cell moved to `G`. Where nothing turned up (see the gaps below), the search did not
reach every county or city server, so it is not evidence of absence.

**Method.** ArcGIS Online item search (`/sharing/rest/search`, bounding box
-124.0,46.75,-121.2,49.0, title terms park/tree/art/mural/sculpture). Hub search API
(`/api/search/v1/collections/all/items`) on each county and city open-data hub found.
Socrata Discovery API (`api.us.socrata.com/api/catalog/v1`) for WA domains, plus direct
REST directory scans of the Whatcom, Mason, Bellingham and Olympia ArcGIS servers. Each
candidate was checked for metadata only: layer schema, `returnCountOnly` record count,
`editingInfo.lastEditDate`, and the item's license/disclaimer text. Raw records were
not inspected. **Count** is the feature count on 2026-10-22. **Last edit** is the
layer's last data edit where the server reports one. "—" means it doesn't report one.

**Reuse terms (all ArcGIS candidates).** None carries an explicit open license. Item
`licenseInfo` is a liability disclaimer ("as is", "not for legal boundaries"), or a
link to the publisher's terms (King County GIS terms; Pierce County "Terms of Use";
Thurston County "By accessing any Data…"). The only explicit grant found is the State
Art Collection on data.wa.gov, which is **Public Domain**. The existing Seattle
integrations have the same disclaimer-only status. Whether disclaimer-only public feeds
are acceptable is an owner call, recorded below under Open questions.

### Parks

| County | Publisher | Endpoint (FeatureServer layer) | Grain / geometry | Count | Last edit | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| All 10 | WA State Parks and Recreation Commission | `services5.arcgis.com/4LKAHwqnBooVDUlX/.../ParkBoundaries/FeatureServer/2` | State park unit, polygon | 207 | 2026-10-12 | Statewide, so it needs a county clip. `Category`, `Acres`, `ParkRegion`. State-managed land only. |
| King | King County GIS (multi-owner compilation) | `services.arcgis.com/Ej0PsM5Aw677QF1W/.../PARK_AREA_228/FeatureServer/0` | Park site, polygon | 1,546 | 2026-10-14 | Has `OWNER`/`OWNERTYPE`/`MANAGER`. It includes Seattle and city parks, so it **overlaps Seattle Parks** (`seattle.parks`). Dedupe by owner, or use it only outside Seattle. |
| King | City of Bellevue | `services1.arcgis.com/EYzEZbDhXZjURPbP/.../Park_Sites/FeatureServer/268` | Park site, polygon | 154 | 2026-10-22 | Amenity flags. It's also covered by the King County layer above. |
| King | City of Kirkland | `services2.arcgis.com/loGMwowmR0OPlOQb/.../ALL_Parks/FeatureServer/0` | Park parcel, polygon | 116 | 2026-10-01 | `CATEGORY`. Overlaps King County. |
| King | City of Federal Way | `geoportal.cityoffederalway.com/res/rest/services/FW_Land/parks/FeatureServer/0` | Park, polygon | 45 | — | Overlaps King County. |
| King | City of Kenmore; Renton; Auburn | Kenmore `gwa.kenmorewa.gov/.../Parks/FeatureServer`; Renton `gismaps.rentonwa.gov/as03/.../ParksAndRecreation/MapServer`; Auburn `gis.auburnwa.gov/hosting/.../BoundariesB/MapServer/0` | Park, polygon | not counted | — | Found but not probed. They're probably subsumed by the King County layer. |
| Pierce | Pierce County | `services2.arcgis.com/1UvBaQ5y1ubjUPmd/.../Parks_polygons/FeatureServer/1` (and the `Parks_points` twin) | Park, polygon/point | 298 | 2024-10-17 | Multi-owner (`Owner`, `Manager`, `ParkType`, amenity flags). Points and polygons are the same 298 parks, so load one. |
| Pierce | Metro Parks Tacoma | `services1.arcgis.com/WGzzp37bqYMLyzDR/.../MPT_Parks_and_Facilities/FeatureServer/0` | Park/facility, point | 90 | 2023-04-25 | Probably overlaps the Pierce County layer. |
| Pierce | City of Lakewood | `services3.arcgis.com/DP7cu0aLwEbmib3H/.../Parks_Recreation/FeatureServer/0` | Park, polygon | 24 | 2026-10-21 | Copyright "City of Lakewood GIS, Pierce County GIS". Probably overlaps Pierce County. |
| Snohomish | Snohomish County | `services6.arcgis.com/z6WYi9VRHfgwgtyW/.../County_Park/FeatureServer/0` | County park, polygon | 234 | 2026-09-22 | **County-owned parks only.** `STATUS`, `CLASS_DESC`, `ACRES_DOC`. |
| Snohomish | City of Everett | Socrata `data.everettwa.gov` `b299-63zi` | City park, polygon | 53 | 2025-05-10 (rows) | No license field set. `type`, `condition`, `installdate`. |
| Snohomish | City of Lynnwood | `services2.arcgis.com/W2b0jYHWnOivta60/.../Parks_layers_public/FeatureServer` | Park layers | not counted | 2021-10-07 | Stale item. |
| Kitsap | Kitsap County | `services6.arcgis.com/qt3UCV9x5kB4CwRA/.../Park_Locations/FeatureServer/0` | Park, point | 131 | 2025-10-08 | Only `NAME`, `TYPE`. Owner coverage unknown. |
| Thurston | Thurston County (GeoData Center) | `tconline.co.thurston.wa.us/server/rest/services/ThurstonExt/Thurston_Parks/FeatureServer/0` | Park, polygon | 191 | — (has `EDIT_DATE`) | Multi-owner (`Owner`). Amenity flags include `PublicArt`. |
| Thurston | City of Olympia | `services.arcgis.com/a83cWFJpXhezKJzd/.../Parks_Point_view/FeatureServer/0` | Park, point (story-map schema) | 47 | 2026-02-27 | Built for a story map, not as an asset inventory. Overlaps Thurston. |
| Island | Island County | `services6.arcgis.com/Q2crTJYujvn27IJC/.../Parks/FeatureServer/0` | Park parcel, polygon | 94 | 2026-10-22 | `OWNER`, `Inv_Cat`, `Acres`, amenity flags. |
| Whatcom | City of Bellingham | `maps.cob.org/arcgis3/rest/services/Parks/ParksResources/MapServer/9` | Park, polygon | 393 | — | Includes `ShowPublic`, which suggests a filter. The same server hosts the integrated Bellingham permits. |

### Street trees (managed inventories — not canopy, not all trees)

| County | Publisher | Endpoint | Grain | Count | Last edit | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| King | City of Seattle (combined) | `services.arcgis.com/ZOyb2t4B0UYuYNYH/.../Combined_Tree_Point/FeatureServer/0` | Tree, point | 240,281 | 2026-10-22 | `SOURCE_DEPT` across SDOT/SPR/SDCI/SPU. It is a **superset of the integrated SDOT layer** (`seattle.trees`), so choose one and don't load both. |
| King | Seattle Parks (SPR) | `.../SPR_Tree_View/FeatureServer/0` | Park tree, point | 23,356 | 2026-08-03 | It's also inside Combined Tree Point. |
| King | City of Bellevue | `services1.arcgis.com/EYzEZbDhXZjURPbP/.../City_Trees/FeatureServer/29` | City-managed tree, point | 10,456 | 2026-10-22 | `TreeStatus`, `YearPlanted`, `Management`, species, DBH. |
| King | City of Kirkland | `services2.arcgis.com/loGMwowmR0OPlOQb/.../Trees_-_Public_View/FeatureServer/0` | Tree, point | 49,205 | 2026-10-01 | Ownership/status fields aren't exposed, so whether it's managed-only is **unverified**. |
| King | City of Kenmore | `gwa.kenmorewa.gov/arcgis/rest/services/Public_Trees/FeatureServer/22` | Public tree, point | 12,435 | — | `MaintBy`, `SiteType`. |
| King | City of SeaTac | `services3.arcgis.com/DLryYCwhA8W7Jq7Q/.../Trees/FeatureServer/0` | Tree, point | 1,624 | 2026-04-01 | `OwnedBy`/`ManagedBy`. |
| King | City of Burien | `services6.arcgis.com/pZ4CUxkTrr0NFJXS/.../Trees/FeatureServer/8` | Tree, point | 2,185 | 2024-02-28 | Has inspection fields. Stale? |
| Pierce | City of Puyallup | `services8.arcgis.com/5K6vnOH0GkPyJs6A/.../City_Maintained_Street_Trees/FeatureServer/0` | City-maintained street tree, point | 812 | 2026-01-06 | Same org as the integrated Puyallup permits. |
| Thurston | City of Tumwater | `services6.arcgis.com/ovypB8ighP2NPfFE/.../Street_Trees/FeatureServer/0` | Street tree, point | 7,682 | 2026-09-09 | Lucity asset export, with condition and DBH. There are also `Street_Trees1` and a 2025 list. Pick the canonical one with the owner. |
| Snohomish | City of Snohomish | `services9.arcgis.com/hUiJ0kKwHN6Cf0DY/.../Tree_Point_Inventory_City_Snohomish/FeatureServer/11` | Tree, point | 8,882 | 2026-09-10 | `ROW`, `status`, `planted_by`/`removed_by`. |
| Snohomish | City of Mukilteo | `services2.arcgis.com/csauTsCJzwR6Erxa/.../Tree_Inventory/FeatureServer/2` | Tree, point | 21 | 2021-12-29 | Too small and stale to be an inventory. Not a candidate. |
| Whatcom | City of Bellingham | `maps.cob.org/arcgis3/rest/services/Parks/NotableTrees/MapServer/0` | Tree, point | 8,937 | — | The service is titled "NotableTrees", but its fields (`StreetTreeList`, `Ownership`, `MaintainedBy`) suggest a broader managed inventory. Needs confirmation. |

Canopy (not inventory; record separately and never add it to tree counts): King County
"Tree Canopy 2021" is an index of 79 LiDAR tiles, not a feature dataset. Tacoma's
"Community Trees 2017/2024" holds canopy percentages by block group. Its copyright reads
"Washington Department of Natural Resources" and NV5, which points to a WA DNR urban tree
canopy assessment. The official statewide DNR feed was not located, and the only copy
found was a Gig Harbor mirror. Seattle's 2016/2021 canopy assessments were not searched.

### Public art

| County | Publisher | Endpoint | Grain | Count | Last edit | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| All 10 | Washington State Arts Commission (State Art Collection) | Socrata `data.wa.gov` `pmxk-qxai` | Artwork, lat/lon | 5,165 (statewide) | 2024-07-16 (rows) | **Public Domain.** Posting frequency is "bi-annually", the period is 2024, and there's no update since 2024-07. Only state-owned art at schools and agencies. Has `city` but no county, so county needs a spatial join. It overlaps none of the municipal collections. |
| Pierce | City of Tacoma | `services3.arcgis.com/SCwJH1pD8WSn5T5y/.../Public_Art_Updated_with_County_Data_Editing/FeatureServer/0` | Artwork, point | 190 | 2026-10-22 | `data_source` splits it: City of Tacoma 177, Pierce County 13. Includes 1 Lakewood and 1 University Place record. Same org as the integrated Tacoma permits. |
| King | City of Renton | `services1.arcgis.com/slSNGMtvwLJi21om/.../Public_Art_Locations/FeatureServer/13` | Artwork, point | 61 | 2026-04-22 | There's also a `City_Art_Baseline` layer that wasn't probed. |
| King | City of Kent | `services3.arcgis.com/AME2ELqJ7UG0JjrU/.../Parks_PublicArtInventory_View/FeatureServer/2` | Artwork, point | 103 | 2026-10-01 | Minimal schema (`name`, location, description). |
| King | City of Issaquah | `apps.issaquahwa.gov/server/rest/services/General_Mapservices/public_art/FeatureServer/0` | Artwork, point | 41 | — | Artist, type, lat/lon. |
| King | City of Kenmore | `gwa.kenmorewa.gov/arcgis/rest/services/Art_Installations/FeatureServer/0` | Artwork, point | 40 | — | |
| Thurston | City of Olympia | `services.arcgis.com/a83cWFJpXhezKJzd/.../OlympicPublicArt_view/FeatureServer/0` (+ `Murals_Diag_1` layer 1, 120 murals) | Artwork, point (story-map schema) | 75 | 2026-09-10 | Murals are a separate layer. Whether murals count as public art is a definition call. |
| Thurston | City of Lacey | `services2.arcgis.com/iupFdNb5KkJ6t83r/.../City_of_Lacey_Public_Art_Installations/FeatureServer/0` | Artwork, point | 8 | 2021-06-03 | Stale and small. |
| Snohomish | City of Arlington | `services3.arcgis.com/nPsPH23NWoWmXQgb/.../Art_AGOL/FeatureServer/0` | Artwork, point | 136 | 2024-07-23 | Has `STATUS` and `RETIREDATE`, so retired works need a rule. |
| Whatcom | City of Bellingham | `services1.arcgis.com/mg5xPlZs10O6tWPP/.../sculpturePoints_gdb/FeatureServer/0` | Sculpture, point | 89 | 2025-12-19 | Sculptures only. Western Washington University publishes its own campus sculpture layers. They're not a government collection, so they aren't candidates. |

### Gaps and overlaps

- **No candidate found.** Parks: Skagit, Mason and Jefferson have nothing beyond the
  State Parks layer. Street trees: Kitsap, Island, Skagit, Mason and Jefferson. Public
  art: Kitsap, Island, Skagit, Mason and Jefferson; and in King County (4Culture)
  outside the cities listed. Skagit and Jefferson county GIS servers weren't found at
  guessed hostnames. Mason's server (`gis.masoncountywa.gov`) exposes folders, but no
  park/tree/art layers turned up. These stay `U`, not `G`, until a deliberate search of
  each publisher's site is done.
- **Overlaps that need a dedupe rule before any load:** King County parks ⊃
  Seattle/Bellevue/Kirkland/Federal Way parks. Pierce County parks probably ⊃ Metro Parks
  Tacoma and Lakewood. Thurston parks ⊃ Olympia parks. Seattle Combined Tree Point ⊃
  SDOT trees (already integrated). Tacoma public art already merges 13 Pierce County
  records.
- **Different grains under one topic.** Parks mix site polygons, parcel or
  property-interest polygons (King County `PARK_PROPERTY_AREA_233`, 4,037 records;
  don't use it for counts), and points. "County parks only" (Snohomish) differs from
  multi-owner compilations (King, Pierce, Thurston, Island).

### Open questions for the owner (before any PS-TOPICS-05 integration)

1. Are disclaimer-only public ArcGIS feeds acceptable for reuse, as they already are for
   the Seattle layers? Or is an explicit license required?
2. Parks unit: one row per park site (polygon or point), counted by owner type? And
   should State Parks be included or shown separately?
3. Trees: only city-managed inventories (Bellevue, Kenmore, Puyallup, Tumwater, SeaTac)?
   Or also mixed ones (Kirkland, Bellingham), with a caveat?
4. Art: do murals and traffic-box wraps count? Do retired works count? Is the State Art
   Collection shown as a separate publisher layer?
5. Is canopy in scope at all, as a separate measure? The PRD's distinction between
   managed inventory and canopy stands either way.

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

## Restaurant inspections (PS-TOPICS-06) — sources searched 2026-10-22

Research only. Nothing below is wired, and the matrix codes above are unchanged.
Retail food inspection is a county (or health-district) function in Washington, so the
search went one health jurisdiction at a time. King County stays `K` (the integrated
`king.inspections` feed). The other nine stay `U`: one has a machine-readable
*candidate*, and eight publish inspections only as a search UI, PDFs or on request.
Nothing moved to `G`. The `G` code is defined by the 2026-10-11 permits search, and
whether "search UI only" counts as "no usable source" is an owner call (see Open
questions below).

**Method.** The WA Department of Health's list of county inspection sites
(`doh.wa.gov/community-and-environment/food/restaurant-inspections`, which is also the
target of the data.wa.gov `7ktr-3bhb` "Restaurant Inspections" link item). Each
jurisdiction's food-safety page was fetched with `curl` and its links scanned for
exports, APIs and vendor portals. The Socrata Discovery API was searched for
"food inspection", "restaurant inspection", "food establishment" and "health
inspection" on WA domains. ArcGIS Online item search used the same terms plus each
county or health-district name. A web search covered Whatcom, whose site returns 403
to `curl`. Candidates were checked for metadata only: layer schema,
`returnCountOnly` count, `editingInfo.lastEditDate`, min/max date statistics, and
item license text. Raw records were not inspected.

### Per health jurisdiction

| County | Health jurisdiction | What is published | Machine-readable? | Notes |
| --- | --- | --- | --- | --- |
| King | Public Health — Seattle & King County | Socrata `data.kingcounty.gov` `r878-4sxa` (**integrated** as `king.inspections`) | Yes | **Public Domain.** One row per violation within an inspection (inspection rows repeat). 110,068 rows, 2021-01-04 to 2026-10-21, refreshed 2026-10-22. See the King copies below. |
| Kitsap | Kitsap Public Health District | ArcGIS `services3.arcgis.com/rM2bN63KIgsKua6J/arcgis/rest/services/Emoji_Food_Map_(Public_Map)/FeatureServer/0` ("Open Food Establisments") | Yes — **candidate** | One row per **open establishment**, point. 1,334 features. Last edit 2026-09-11, though the app says "updated daily". Has `LastScore` and `SafetyCategory` (Kitsap's emoji rating), **not inspection events**, so it is a current snapshot with no history. The item has no license text. It backs the district's "Food Establishment Inspections Map" (Experience `df34c4c6…`). |
| Kitsap | Kitsap Public Health District | ArcGIS `services3.arcgis.com/rM2bN63KIgsKua6J/arcgis/rest/services/Foodinspections/FeatureServer/0` | Yes — superseded | Same establishment grain (`LastScore`, no `SafetyCategory`). 1,409 features, last edit 2025-11-01. Item license reads **"Non-commercial use only"**. It looks like the predecessor of the layer above, so don't load both. |
| Pierce | Tacoma-Pierce County Health Department | Accela Citizen Access property lookup (`aca-prod.accela.com/TPCHD/...PropertyLookUp.aspx?isFoodFacility=Y`) | No | Per-facility search UI. Accela offers an in-session "Export" of search results, but that is not a feed. No TPCHD inspection layer turned up on ArcGIS Online (its `TPCHDFoodAssets_PublicView` is food-access sites, not inspections). |
| Snohomish | Snohomish County Health Department | EnvisionConnect public search (`snohomishonline.envisionconnect.com/#/pa1/search`) | No | Search UI behind reCAPTCHA. No open-data item found. |
| Thurston | Thurston County Public Health & Social Services | Classic ASP lookup (`co.thurston.wa.us/apps/eh-food-inspections/`), with an "All Inspections — Last 90 Days" list | No (HTML only) | The 90-day list is event-grain HTML. Scraping it would be the only route, which is a design call and not a published feed. |
| Island | Island County Public Health | myhealthdepartment.com portal (`inspections.myhealthdepartment.com/wa_islandcounty/`) | No | The portal returns 403 to `curl`. No documented export. |
| Mason | Mason County Public Health | inspect2go public index (`mason.inspect2go33.com/Public/Index`), plus monthly PDF report bundles for 2023–2026 on `masoncountywa.gov` | No (PDF) | Monthly PDFs have gaps (for example, no 2025-09 or 2025-12 link). |
| Jefferson | Jefferson County Public Health | Tyler EnerGov self-service portal (`selfservice-op.jeffcowa.us/energov_prod/selfservice`) | No | Per-permit lookup. The county says results appear about two weeks after the inspection. |
| Skagit | Skagit County Public Health | Nothing online | No | The county's food-establishment page says: "We do not currently have inspection reports available online." Reports are available by public records request. This is the strongest evidence of absence found. |
| Whatcom | Whatcom County Health and Community Services | A "Restaurant Inspection" page (`whatcomcounty.us/3239`) says a searchable database exists | Unknown | The site returns 403 to `curl`, so the portal vendor and any export were not identified. It needs a manual look (Evan) or another route. |

### King County copies (overlap — do not load alongside `r878-4sxa`)

- `services.arcgis.com/Ej0PsM5Aw677QF1W/.../RESTAURANT_INSPECTIONS_POINT_857/FeatureServer/0`
  (also `gisdata.kingcounty.gov/.../pubsafe__restaurant_inspections_point/MapServer/857`).
  It has the same violation grain with coordinates. 260,845 rows, inspection dates
  2006-01-02 to 2024-03-30, layer edited 2026-10-14. King County GIS terms apply.
  It is an older, longer history (2006–2024) of the same records. It could backfill
  pre-2021 history, which is an owner decision about the time window. It is not a new
  jurisdiction.
- `.../King_County_Restaurant_Inspection_and_Violation_Records_SEARCH_view/FeatureServer/0`:
  12,311 business points (record ID, name, address, parcel). It's a lookup index, not
  inspections.
- Socrata filter views on `r878-4sxa`/`j2pu-r4ru` (`sgr5-u9rw`, `29us-kypr`, `mzbk-wwns`)
  are derived views, not sources.

### Grain and scoring differences (must be preserved if anything is integrated)

- **King**: violation-level rows that roll up to inspection events. The score is
  violation points (red/blue), and King also publishes a 4-tier emoji rating (`grade`).
- **Kitsap**: one row per establishment with only the *last* score and an emoji safety
  category. There's no event history, so inspection counts or trends cannot be built
  from it, and Kitsap scores must not be pooled with King points without an owner
  rule.
- The other jurisdictions all run the WA Food Code inspection form (priority/core
  violation points), but none publishes it machine-readably.

### Open questions for the owner (before any PS-TOPICS-06 integration)

1. Is a Kitsap **establishment snapshot** (last score only, no events) acceptable for an
   "Inspections" page whose King grain is inspection events? Or should Kitsap be shown
   as a separate "current ratings" view? Also, the older Kitsap layer says
   "non-commercial use only" and the current one has no license text. Is that
   acceptable?
2. Should jurisdictions with only search UIs, PDFs or records requests (Pierce,
   Snohomish, Thurston, Island, Mason, Jefferson, Skagit) move from `U` to `G`? Doing
   so means redefining `G` beyond the 2026-10-11 permits search. Scraping any of the
   portals is out of scope unless you decide otherwise.
3. Should King history be backfilled before 2021 from the ArcGIS copy (2006–2024)? If
   so, what is the dedupe key against `r878-4sxa` for the overlapping 2021–2024 years?
4. Whatcom: can you identify the portal behind `whatcomcounty.us/3239` (it's blocked to
   `curl`)?

## Licenses, STR, crime, fire and 311 (PS-TOPICS-07/08) — sources searched 2026-10-22

Research only. Nothing below is wired, and the matrix codes above are unchanged. Every
row is a *candidate*: a public, keyless, machine-readable endpoint that answered on
2026-10-22. None is verified for completeness, and none has an owner decision on
definitions, windows, grain or overlap. The Business Licenses, Short-Term Rentals,
Crime, Fire 911 Calls and 311 Requests rows stay `S` for King and `U` elsewhere. No
cell moved to `G`. Where nothing turned up, the search did not reach every city
server, so that is not evidence of absence.

**Method.** Socrata Discovery API (`api.us.socrata.com/api/catalog/v1`) by keyword
("business license", "short term rental", "vacation rental", "crime", "police
incidents", "911", "fire incidents", "NFIRS", "fire marshal", "service requests", "311",
"SeeClickFix", "code enforcement", "calls for service", "lodging tax") and a full
listing of `data.wa.gov`, `data.everettwa.gov`, `internal.open.piercecountywa.gov`,
`data.auburnwa.gov` and `data.kingcounty.gov`. ArcGIS Online item search for the same
terms, once region-wide and once per county and major city (33 place names), plus a
listing of the City of Tacoma open-data owner's items. Web search for county STR
rules, 911 dispatch-center feeds and city police statistics pages. Candidates were
checked for metadata only: schema, `count(*)`/`returnCountOnly`, min/max date
statistics, distinct/grouped counts of categorical columns (county, agency, status,
NAICS description), `editingInfo.lastEditDate`, and license text. Raw records were not
inspected. **Count** is the record count on 2026-10-22.

**Reuse terms.** Explicit **Public Domain**: Everett Police Incidents, Auburn Crimes,
and Seattle's own feeds. Pierce County Socrata items point to the county's "Terms of
Use" story page. Tacoma items link a "Disclaimer | City of Tacoma Open Data" page whose
host (`data.cityoftacoma.org`) did not resolve from here, so its text is unread.
Bellevue items carry a no-warranty disclaimer only. The rest have no license text.
Whether disclaimer-only feeds are acceptable is the same owner call as for parks.

### Crime

| County | Publisher | Endpoint | Grain | Count / period | Notes |
| --- | --- | --- | --- | --- | --- |
| All 10 | WA OFM Statistical Analysis Center (WASPC NIBRS) | Socrata `data.wa.gov` `vvfu-ry7f` | **Agency × year** offense counts (crimes against persons / property / society, by offense), with population and rate | 3,471 rows, 2012–2024, 270 locations; posting "Yearly", last update 2025-11 | **The only region-wide candidate.** Every Puget Sound county is present (King 42 agencies, Snohomish 24, Pierce 21, Whatcom 11, Thurston 10, Skagit 8, Kitsap 7, Island 5, Jefferson 3, Mason 3). Each county also has a `COUNTY TOTAL` row, which must not be summed with its agencies. Agency counts grow while agencies convert to NIBRS (King: 19 in 2012, 28 in 2015–2017, 42 from 2018), so early years are partial. Publisher says NIBRS and SRS counts "cannot be compared". No license text. |
| All 10 | WA OFM SAC (SRS) | Socrata `data.wa.gov` `6njs-53y5` | Agency × year, Part I offenses | 1990–2018 | Legacy method. Not comparable with NIBRS (publisher's note). Only relevant if pre-2012 history is wanted. |
| Pierce | Pierce County (Finance, from OFM) | Socrata `internal.open.piercecountywa.gov` `u3gb-kmc7` | Location × year | 91 rows, 2012–2024, 3 locations | A subset copy of the OFM NIBRS table. **Overlap — don't load alongside `vvfu-ry7f`.** |
| Pierce | Pierce County Sheriff | Socrata `internal.open.piercecountywa.gov` `9ik3-ebpg` (also ArcGIS `services2.arcgis.com/1UvBaQ5y1ubjUPmd/.../Crime_Data/FeatureServer/1`) | Offense point (approximate location) | 16,386 rows, 2025-10-01 to 2026-09-30 | **Rolling 12-month window**, monthly refresh. Covers unincorporated Pierce plus Bonney Lake, Eatonville, Edgewood, Gig Harbor, Puyallup, South Prairie, University Place. History would have to be accumulated by snapshotting, which is a design call. The two endpoints are copies. |
| Pierce | City of Tacoma Police | ArcGIS `services3.arcgis.com/SCwJH1pD8WSn5T5y/arcgis/rest/services/TPD_RMS_Crime/FeatureServer/0` (table, lat/lon fields) | Offense description per report | 232,543 rows, 2018-01-01 to 2026-10-21, edited 2026-10-22 | Publisher: "neither NIBRS compliant nor UCR compliant and should not be compared to any report or data source using either standard". It excludes sexual offenses. |
| King | City of Auburn | Socrata `data.auburnwa.gov` `8g4u-7zzy` | Offense per case (no coordinates; address + reporting district) | 199,901 rows, 2014-01-01 to 2026-10-20 | **Public Domain.** Auburn spans King and Pierce. Also on `gis.auburnwa.gov/hosting/rest/services/Police/Police/MapServer/0` (copy). |
| King | City of Bellevue Police | ArcGIS `services1.arcgis.com/EYzEZbDhXZjURPbP/arcgis/rest/services/Offenses/FeatureServer/1` | Offense point with `NIBRS_CODE` | 76,563 rows, reported 2019-01-01 to 2026-10-20 | Daily refresh. The item says "2017 to present" but the reported-date range starts 2019. An older `Crime_Cases_By_100_Block` layer (2,820 rows, last edit 2022-06) is stale. |
| Snohomish | City of Everett Police | Socrata `data.everettwa.gov` `szww-y224` | Police case (report) per row | 170,613 rows, 2015-01-01 to 2026-10-21 | Excludes DV, child-abuse and minor sex-offense cases. No license text. |
| Skagit | Skagit County Sheriff (multi-agency) | ArcGIS `gis.skagitcountywa.gov/arcgis/rest/services/Sheriff/CrimeRelatedIncidentsForAGOL/FeatureServer/0` | Crime-related incident point (`NatureDesc`, `Category`) | 1,251,537 rows, 2005-01-01 to 2026-10-21 | Five agencies: Mount Vernon PD 425,929, Sheriff 338,423, Burlington 182,417, Anacortes 163,177, Sedro-Woolley 141,591. The AGOL item was last modified 2021, but the data is current. No license text. "Crime-related incidents" may include calls that are not offenses; definition unverified. |
| Kitsap | City of Bremerton Police | `bremertonwa.gov/991/Statistics` (Document Center) | Monthly XLSX with incident, arrest and citation tabs | Monthly files 2025-01 to 2026-09, older years in the Document Center | File-per-month spreadsheets, not an API. Schema stability across months is unverified. |
| King | City of Kirkland | `maps.kirklandwa.gov/host/rest/services/Hosted/CrimeAnalysis_(Public)/FeatureServer` | Unknown | — | Returns a Cloudflare challenge to `curl`. Not assessable without a browser. |

Apart from the OFM table, nothing open was found for the King County Sheriff, Kitsap
County Sheriff, or any Thurston, Island, Mason, Jefferson or Whatcom agency. Bellingham
offers neighborhood statistics and daily activity pages, which are search/HTML only.

### Police calls for service (not offenses)

These are CAD/dispatch records. They are a different grain from crime reports and must
not be pooled with them.

| County | Publisher | Endpoint | Count / period | Notes |
| --- | --- | --- | --- | --- |
| Snohomish | Everett PD / SNO911 | Socrata `data.everettwa.gov` `f6vp-3svh` | 1,619,466 rows, 2015-01-01 onward | **Public Domain.** All police responses, including officer-initiated activity; locations rounded to the 100 block. Max `datetimereceived` is 2026-12-20, a future date, so some timestamps are wrong. |
| Pierce | City of Tacoma Police | ArcGIS `.../SCwJH1pD8WSn5T5y/.../Tacoma_CAD/FeatureServer/0` (table) | 1,691,485 rows, 2018-01-01 to 2026-10-22 | Agency field is TPD only. |
| King | City of Bellevue Police | ArcGIS `.../EYzEZbDhXZjURPbP/.../Incidents/FeatureServer/0` | 395,971 rows, 2021-01-01 to 2026-10-21 | Daily refresh. Has call-received and dispatch response seconds. |
| Pierce | South Sound 911 | Socrata `internal.open.piercecountywa.gov` `ff4w-c69w` | 583,563 rows, 2016-01-01 to 2021-12-31 | One-off snapshot posted 2022-06 by the County Council; not updated. |
| Thurston | Thurston County Sheriff / TCOMM 911 | `thurstoncountywa.gov/911-incident-responses` | Rolling 24 h | Daily HTML incident log only. Not a feed. |

Seattle also publishes SPD Call Data (`33kz-ixgy`, 11.1M rows, 2009-06 to 2026-10,
Public Domain). It is not integrated today and would be a new Seattle source, not a
regional one.

### Fire / EMS 911

| County | Publisher | Endpoint | Grain | Count / period | Notes |
| --- | --- | --- | --- | --- | --- |
| Snohomish | Everett Fire / SNO911 | Socrata `data.everettwa.gov` `w35j-83t3` | **Unit dispatch** (several rows per incident) | 1,063,586 rows, 266,583 distinct incidents, 2015-10-26 to 2026-08-31 | Includes responses outside city limits by Everett units. Seattle's `kzjm-xkqj` is one row per incident, so the two need an incident-level rollup before comparison. No license text. Last data is 2026-08-31, about seven weeks behind. |

No other open fire/EMS incident feed was found for any Puget Sound fire department,
fire district or regional dispatch center (South Sound 911 fire, Kitsap 911, TCOMM,
WhatComm, Skagit 911, ICOM, JeffCom, MACECOM, NORCOM, Valley Com). Statewide fire
incident (NFIRS / State Fire Marshal) data was not found on `data.wa.gov`. The only WA
fire-district incident tables there are eastern Washington (Asotin, Blue Mountain).

### 311 / service requests

| County | Publisher | Endpoint | Count / period | Notes |
| --- | --- | --- | --- | --- |
| Pierce | City of Tacoma (Tacoma FIRST 311, SeeClickFix) | ArcGIS `.../SCwJH1pD8WSn5T5y/.../SeeClickFix_Requests/FeatureServer/0` (points) | 156,515 rows, created 2022-06-17 to 2026-10-22 | All requests regardless of status. Category set is SeeClickFix's, not Seattle's. |
| King | City of Bellevue (MyBellevue, PublicStuff) | ArcGIS `.../EYzEZbDhXZjURPbP/.../MyBellevue_311/FeatureServer/0` (points) | 34,663 rows, created 2021-06-15 to 2026-10-22 | Web and mobile submissions only (not phone). Bellevue disclaimer. |
| Pierce | Pierce County Planning & Public Works | Socrata `internal.open.piercecountywa.gov` `9wmg-abtz` | Quarterly aggregates since 2017 | Nuisance code-enforcement counts, not requests. Not comparable. |

Seattle's `43nw-pkdq` (Customer Service Request Tracking Data) is a status-history
companion to the integrated `5ngg-rpne`, not a new source.

### Business licenses

| County | Publisher | Endpoint | Grain | Count / dates | Notes |
| --- | --- | --- | --- | --- | --- |
| Pierce | City of Tacoma | ArcGIS `.../SCwJH1pD8WSn5T5y/.../Business_Licenses/FeatureServer/0` (table, x/y) | License | 22,138 rows; `Business_Open_Date` 1893-01-07 to 2027-02-01, a string field with out-of-range values | Some rows are "Not Mapped". Whether it holds only current licenses is unverified. |
| King | City of Bellevue | ArcGIS `.../EYzEZbDhXZjURPbP/.../Business_Licenses_(All)/FeatureServer/3` | Registered business, with `CancelDate` | 82,274 rows; `IssueDate` 1950-01-01 to 2026-10-16; daily refresh | Includes cancelled licenses (status rule needed). |
| Snohomish | City of Everett | Socrata `data.everettwa.gov` `qvfa-2v26` | License | 11,573 rows; `issuedate` 1900-01-01 to 2087-03-16 (sentinel/out-of-range values) | Active vs. expired status is not a column. No license text. |
| King | City of Seattle | ArcGIS `services.arcgis.com/ZOyb2t4B0UYuYNYH/.../Seattle_Business_License/FeatureServer` | — | — | A copy of the integrated `wnbq-64tb`. **Overlap — don't load.** |

Many Washington cities (Bellingham included) license through the state Business
Licensing Service (DOR). Its public lookup is search-only, and no bulk BLS or UBI
dataset for the region was found on `data.wa.gov` (only an Asotin County UBI table).
Renton's 2023 ArcGIS layers (`Vista_Business_Licenses`, day-care licenses) are
special-purpose and stale.

### Short-term rentals

No STR-specific registry or permit feed was found outside Seattle (`s7df-xba4`, already
integrated). Related, but **not** STR inventories:

- **Tacoma — Business Licenses for Rental Activity**: ArcGIS
  `.../SCwJH1pD8WSn5T5y/.../Business_Licenses_Rental_Activity/FeatureServer/0` (table,
  8,843 rows, 8,252 with `Current_License = Yes`). It is mostly long-term rentals
  (7,417 "Lessors of Residential Buildings" and 1,192 nonresidential). Only 55 rows are
  NAICS "All Other Traveler Accommodation", and whether NAICS identifies STRs is
  unverified.
- **Bellingham — Rental Registrations**: ArcGIS
  `services1.arcgis.com/mg5xPlZs10O6tWPP/.../Plan_RentalRegistrations/FeatureServer/1`
  (5,386 locations, type "RENTAL REGISTRATION", 5,295 active; edited 2026-10-12). This is
  the long-term rental-safety program, not STRs.
- **Pierce County LTAC** lodging-tax revenue tables (`pet7-x8tm`, `rvg5-atcq`) are
  revenue, not licenses.

County STR rules that would create a permit list exist (Whatcom County vacation-rental
permits, Jefferson County's 2025 permit cap, Kitsap's 2016 code with deferred
enforcement), but none publishes the permits as data.

### Open questions for the owner (before any PS-TOPICS-07/08 integration)

1. **Crime:** is the OFM/WASPC NIBRS table (agency × year, 2012–2024) acceptable as the
   regional crime layer, next to Seattle's offense-level SPD feed? That means a separate
   annual agency-level view, excluding `COUNTY TOTAL` rows or using only them, and
   deciding how to show years before each agency moved to NIBRS. Should incident-level
   city feeds (Tacoma, Bellevue, Everett, Auburn, Skagit) be added as well, given that
   Tacoma says its feed is not NIBRS/UCR comparable?
2. **Calls vs. offenses:** should police calls for service (Everett, Tacoma, Bellevue)
   be in scope at all, and if so as a separate page? Seattle's own Call Data would then
   also be a candidate.
3. **Fire:** Everett's unit-dispatch feed is the only regional fire candidate. Integrate
   it with an incident-level rollup, or leave Fire 911 as Seattle-only?
4. **311:** Tacoma (SeeClickFix) and Bellevue (MyBellevue, web/app only) categories differ
   from Seattle's. Show them per city without a harmonized category, or harmonize?
5. **Licenses:** what status rule defines "a license" (current only, or including
   cancelled/expired), and how should out-of-range dates (1893, 1900, 2087) be handled?
   Are disclaimer-only or no-license-text feeds acceptable?
6. **STR:** with no regional STR feed, should Short-Term Rentals stay Seattle-only?
   Should cells move to `G`? That needs a definition of `G` beyond the permits search.
7. **Rolling windows:** Pierce Sheriff publishes a 12-month window only. Is accumulating
   snapshots across builds acceptable, or should it be shown as "last 12 months" only?
8. **Kirkland:** its crime layer sits behind a Cloudflare challenge. Can you check
   whether it is a public open-data service, or should it be skipped?

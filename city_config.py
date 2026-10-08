"""Seattle-metro configuration — the single "which city" surface for Robbins.

Every Seattle-specific value lives here: Socrata domains + dataset ids, ArcGIS
roots, EPA AQS FIPS codes, the NOAA weather station, and source URLs / year
ranges. ``build_warehouse.py`` imports from this module, so porting Robbins to
another metro is (ideally) a one-file change.

Discipline: a dataset id only appears here once its source has been **verified
live and machine-readable** (see PRD "Verify every source before wiring it").
Topics still being sourced are listed under ``UNVERIFIED`` as a to-do, not wired.

No real secrets. A Socrata app token is OPTIONAL (it only raises rate limits);
anonymous access works for the volumes here. If set, keep it here — it is not a
protected secret.
"""

from __future__ import annotations

from source_registry import Source, validate_sources

# --------------------------------------------------------------------------- #
# Socrata (SODA API) — City of Seattle + King County open-data portals         #
# --------------------------------------------------------------------------- #
SEATTLE_SOCRATA = "data.seattle.gov"
KINGCOUNTY_SOCRATA = "data.kingcounty.gov"

# Optional Socrata app token (raises throttling limits; anonymous still works).
# Not a protected secret. Leave None for anonymous access.
SOCRATA_APP_TOKEN: str | None = None

# Verified-live Socrata dataset ids (domain, dataset_id). Verified 2026-08-11.
PERMITS = (SEATTLE_SOCRATA, "76t5-zqzr")        # Seattle DCI Building Permits, ~192k rows
SPD_CRIME = (SEATTLE_SOCRATA, "tazs-3rd5")      # SPD Crime 2008-Present, ~1.55M rows (CSV export)
SFD_911 = (SEATTLE_SOCRATA, "kzjm-xkqj")        # Seattle Real-Time Fire 911 Calls, ~2.2M rows
FOOD_INSPECTIONS = (KINGCOUNTY_SOCRATA, "r878-4sxa")  # PH Seattle-KC food inspections, ~106k rows
SHORT_TERM_RENTALS = (SEATTLE_SOCRATA, "s7df-xba4")   # Seattle STR licenses, ~11.4k rows (spatial)
BUSINESS_LICENSES = (SEATTLE_SOCRATA, "wnbq-64tb")    # Active business license certs, ~84k (non-spatial)
CSR_311 = (SEATTLE_SOCRATA, "5ngg-rpne")        # Customer Service Requests (Find It, Fix It), ~2.46M rows (CSV export)

# SPD crime + Fire 911 are huge (full history is millions of rows); cap the baked
# warehouse to recent years for lean, fast builds (Elvis precedent). Filter is a
# SoQL $where on the datetime field.
CRIME_START = "2019-01-01"   # ~630k rows since 2019
FIRE_START = "2019-01-01"
# Customer Service Requests span 2013-present (~2.46M); cap to recent years for a
# lean build. 2020+ is ~1.65M rows and covers the pandemic + Find-It-Fix-It era.
CSR_311_START = "2020-01-01"

# SPD crime uses a -1.0 sentinel (not null) for missing lat/lon (~11% of rows);
# staging must filter these before they plot at (-1, -1). Very recent SPD rows
# (~last 30 days) arrive with REDACTED geo until finalized.
SPD_CRIME_GEO_SENTINEL = -1.0

# --------------------------------------------------------------------------- #
# Federal NTD — National Transit Database monthly ridership (Socrata)          #
# --------------------------------------------------------------------------- #
# The FTA's National Transit Database publishes monthly unlinked passenger trips
# (UPT) for every U.S. transit agency, hosted on the federal Socrata portal. It
# is the machine-readable source for both Puget Sound transit ridership AND
# Washington State Ferries ridership (mode FB). We curate the Seattle-metro
# agencies and give each a friendly label; ferry vs. land transit splits on mode.
NTD_RIDERSHIP = ("data.transportation.gov", "8bui-9xvu")  # Complete Monthly Ridership

# NTD agency name (exact, as published) -> friendly label. This is the metro's
# transit + ferry operator set; anything not here is excluded at fetch time.
NTD_AGENCIES = {
    "King County": "King County Metro",
    "Central Puget Sound Regional Transit Authority": "Sound Transit",
    "Snohomish County Public Transportation Benefit Area Corporation": "Community Transit",
    "Pierce County Transportation Benefit Area Authority": "Pierce Transit",
    "City of Everett": "Everett Transit",
    "City of Seattle": "Seattle Streetcar",
    "Washington State Ferries": "Washington State Ferries",
    "King County Ferry District": "King County Water Taxi",
    # Verified in FTA monthly agency coverage on 2026-09-27.
    "Kitsap County Public Transportation Benefit Area Authority": "Kitsap Transit",
    "Skagit Transit": "Skagit Transit",
    "Whatcom Transportation Authority": "Whatcom Transportation Authority",
    "Intercity Transit": "Intercity Transit",
    "County of Pierce": "Pierce County Ferry",
}
# Cap to a recent decade — long enough to frame the pre-pandemic peak, the 2020
# collapse, and the ongoing recovery, while keeping the fetch small.
NTD_START = "2015-01-01"
# These operators were absent from the WA monthly feed's 2015+ agency inventory.
# Absence here is not evidence of zero ridership or absence from annual NTD data.
NTD_MONTHLY_GAPS = ("Island Transit", "Jefferson Transit Authority", "Mason Transit")

# --------------------------------------------------------------------------- #
# ArcGIS FeatureServers — City of Seattle / King County GIS (spatial layers)   #
# --------------------------------------------------------------------------- #
SEATTLE_ARCGIS = "https://services.arcgis.com/ZOyb2t4B0UYuYNYH/ArcGIS/rest/services"

# Public art is ArcGIS-only (no Socrata dataset). The PublicArt2 layer's LAT/LON
# attribute columns are all 0 — read coordinates from feature geometry (out_sr=4326).
PUBLIC_ART = (SEATTLE_ARCGIS, "PublicArt2", 0)  # (org, service, layer) — ~758 points

# Seattle Parks & Recreation park boundaries (ArcGIS, point geometry despite the
# name — one point per park). NAME + PARKSBND_AREA (square feet). ~511 parks.
PARK_BOUNDARIES = (SEATTLE_ARCGIS, "Park_Boundaries", 0)

# SDOT active street-tree inventory (ArcGIS, ~212k points). SCIENTIFIC_NAME,
# CONDITION (GOOD/FAIR), HERITAGE / EXCEPTIONAL (Y/N), PLANTED_DATE (epoch ms),
# PRIMARYDISTRICTCD (council district). Coordinates from feature geometry.
SDOT_TREES = (SEATTLE_ARCGIS, "SDOT_Trees_(Active)", 0)

# SPD Micro Community Policing Plan (MCPP) neighborhoods — 58 polygons, the
# geography SPD crime is tagged with. We use these polygons for the neighborhood
# choropleths: crime, fire 911, and 311 incidents are assigned to a neighborhood
# by point-in-polygon at build time. `neighborhood` (name) + `precinct`, and
# `Shape__Area` in square feet (State Plane WA). Polygon geometry, out_sr=4326.
MCPP_NEIGHBORHOODS = (SEATTLE_ARCGIS, "MCPP", 0)

# Substrings (matched case-insensitively against a park's name) that flag a
# water-associated park. The boundary layer has no amenity attributes, so this
# name heuristic is our "water feature" signal — approximate, labeled as such.
PARK_WATER_KEYWORDS = (
    "beach", "lake", "pond", "bay", "cove", "waterfront", "lagoon", "creek",
    "river", "falls", "spring", "inlet", "harbor", "marina", "boat", "tidelands",
    "wading", "spray", "waterway", "shore",
)

# Seattle-metro bounding box (King + Pierce + Snohomish) for filtering stray geo.
METRO_BBOX = {"lat": (46.9, 48.4), "lon": (-122.7, -121.3)}

# --------------------------------------------------------------------------- #
# EPA AQS — keyless pre-generated daily bulk files                             #
# --------------------------------------------------------------------------- #
# Administrative launch scope confirmed 2026-09-27. County codes verified at:
# https://www2.census.gov/geo/docs/reference/codes2020/national_county2020.txt
REGION_NAME = "Puget Sound"
REGION_COUNTIES = {
    "53029": "Island", "53031": "Jefferson", "53033": "King",
    "53035": "Kitsap", "53045": "Mason", "53053": "Pierce",
    "53057": "Skagit", "53061": "Snohomish", "53067": "Thurston",
    "53073": "Whatcom",
}
AQS_STATE = "53"
AQS_COUNTIES = {fips[2:]: name for fips, name in REGION_COUNTIES.items()}
AQS_PARAMS = {"88101": "PM2.5", "44201": "Ozone"}  # param code -> label
# The national daily bulk files are large and EPA's server is slow (~20-35s each),
# so — like crime/fire — the baked warehouse caps to recent years for lean builds.
# 2019 still spans the 2020 & 2022/2023 wildfire-smoke seasons.
AQS_START_YEAR = 2019
AQS_END_YEAR = 2026  # inclusive; the current year's file is partial but published

# --------------------------------------------------------------------------- #
# NOAA GHCN-Daily — keyless station CSV                                        #
# --------------------------------------------------------------------------- #
# Seattle-Tacoma International Airport (Sea-Tac) — the original Seattle station.
# Headlines are now chosen per county by data completeness (stations module),
# not pinned here. The regional expansion (PS-TOPICS-02) also
# discovers every other temperature-reporting GHCN station in the region.
NOAA_STATION = "USW00024233"

# Ten-county bounding box (min_lat, max_lat, min_lon, max_lon) for discovering
# GHCN weather stations from the national inventory. NOAA does not county-tag
# stations, so the build filters the inventory to this box, then assigns each
# surviving station to a county by a spatial join against county boundaries.
# Verified 2026-09-27 against the region's outer county extents (Whatcom north,
# Thurston/Mason south, Pacific coast west, Cascade crest east).
REGION_BBOX = (46.0, 49.1, -124.8, -120.5)
GHCN_ELEMENT = "TMAX"                 # the discovery element (temperature stations)
GHCN_MIN_LAST_YEAR = 2024             # only stations still reporting recently
GHCN_INVENTORY_URL = (
    "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt"
)
WEATHER_REGIONAL_START_YEAR = 2014    # uniform per-station history window across
                                      # every station (incl. Sea-Tac) for a lean
                                      # build; older years are not ingested

# --------------------------------------------------------------------------- #
# Signature water body — four keyless federal networks, now region-wide        #
# --------------------------------------------------------------------------- #
# River: USGS NWIS streamflow. Cedar River at Renton was the Seattle-era gage;
# headlines are now chosen by data completeness, and the build also pulls every active daily-discharge gage in each county by
# countyCd (verified 2026-09-27: gages in 8/10 counties; Island & Kitsap none).
USGS_CEDAR_RIVER_SITE = "12119000"   # USGS NWIS — Cedar River at Renton, WA
USGS_FLOW_PARAM = "00060"            # discharge, cubic feet per second
USGS_STATE = "WA"

# Tide: NOAA CO-OPS monthly-mean sea-level datums. Only the five saltwater-front
# region counties have a long-record water-level gauge (verified 2026-09-27).
# station_id -> (county_fips, display_name). Seattle 9447130 is the King headline.
NOAA_TIDES_STATION = "9447130"       # Seattle, WA (King headline; kept for compat)
# station_id -> (county_fips, display_name, latitude, longitude). Coordinates
# verified 2026-09-27 from the CO-OPS station list (used for the tide-gauge map).
NOAA_TIDE_STATIONS = {
    "9449424": ("53073", "Cherry Point", 48.863, -122.759),   # Whatcom
    "9444900": ("53031", "Port Townsend", 48.111, -122.760),  # Jefferson
    "9447130": ("53033", "Seattle", 47.603, -122.339),        # King
    "9445958": ("53035", "Bremerton", 47.562, -122.623),      # Kitsap
    "9446484": ("53053", "Tacoma", 47.267, -122.413),         # Pierce
}

# Snow: NRCS SNOTEL snow-water-equivalent. Stampede Pass was the Seattle-era
# station; headlines are now chosen by data completeness, and the build pulls every active WA SNTL station and keeps those the AWDB API
# assigns to a region county (verified 2026-09-27: stations in 7/10 counties;
# Island, Kitsap & Thurston are lowland, none).
SNOTEL_STATION = "791:WA:SNTL"       # Stampede Pass (Seattle-era station; kept for compat)
SNOTEL_NETWORK = "SNTL"
SNOTEL_STATE = "WA"

# Census TIGERweb Counties layer — WGS84 county polygons carrying GEOID (5-digit
# state+county FIPS). Used to assign GHCN weather stations (which carry no county)
# to a county by point-in-polygon; stations outside the ten region counties drop.
COUNTY_BOUNDARY = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/"
    "TIGERweb/State_County/MapServer/13"
)

WATER_START_YEAR = 2014              # from 2014 so water year 2015 (the historic
                                     # snow-drought) is fully captured; lean enough
TIDES_START_YEAR = 2000             # tides go back further — sea-level trend

# --------------------------------------------------------------------------- #
# Sources still being verified before they get wired (see TASKS.md Group TOPIC)#
# --------------------------------------------------------------------------- #
# Placeholders only — do NOT fetch these until each is confirmed live and its
# dataset id / layer path recorded above.
UNVERIFIED: tuple[str, ...] = ()
# All core topics are now verified+wired or explicitly dropped:
#   weather (NOAA GHCN-Daily USW00024233) — VERIFIED + WIRED 2026-08-11.
#   air_quality (EPA AQS bulk, WA 53 / 033 / 053 / 061) — VERIFIED + WIRED 2026-08-11.
#   parks (Seattle ArcGIS Park_Boundaries) — VERIFIED + WIRED 2026-08-12.
#   water_body (USGS 12119000 + NOAA 9447130 + SNOTEL 791:WA:SNTL) — WIRED 2026-08-12.
#
# Topics DROPPED for lack of a machine-readable Seattle source (logged, per the
# data-discipline rule "drop any topic Seattle doesn't publish"):
#   marriage_licenses — no Seattle/King County open feed.
#   tourism — no Sea-Tac passenger feed on any open-data portal. Other cities
#     publish airport traffic (NY Port Authority 8pkr-4b7t, LAX g3qu-7q2u), but
#     the Port of Seattle does not; BTS T-100 is form/POST-only (not a clean GET).
#     Checked 2026-08-12. A pivot to WSDOT ferry ridership could stand in for a
#     Puget Sound travel page if desired.

# Configured coverage, audited from the pipeline on 2026-09-27. These entries
# describe existing integrations, not newly verified endpoints or launch scope.
# Keep retrieval timestamps and observed date ranges in build metadata.
def _soda_page(source: tuple[str, str]) -> str:
    return f"https://{source[0]}/d/{source[1]}"


def _arcgis_layer(source: tuple[str, str, int]) -> str:
    return f"{source[0]}/{source[1]}/FeatureServer/{source[2]}"


DATA_SOURCES = (
    Source("seattle.permits", "Building Permits", "Seattle DCI", _soda_page(PERMITS),
           "municipality", "City of Seattle", "One permit",
           "Issued permits; map shows the most recent 5,000 geocoded records."),
    Source("seattle.crime", "Crime", "Seattle Police Department", _soda_page(SPD_CRIME),
           "municipality", "City of Seattle", "Source crime record",
           "2019 onward; missing/redacted locations are excluded from maps. Not county-wide."),
    Source("seattle.fire", "Fire 911 Calls", "Seattle Fire Department", _soda_page(SFD_911),
           "municipality", "Seattle Fire dispatch reporting area", "Source dispatch record",
           "2019 onward; dispatch records are not a count of unique emergencies."),
    Source("king.inspections", "Restaurant Inspections", "Public Health — Seattle & King County",
           _soda_page(FOOD_INSPECTIONS), "county", "King County reporting jurisdiction",
           "Source inspection record", "Repeat inspections are not unique establishments; scoring is jurisdiction-specific."),
    Source("seattle.str", "Short-Term Rentals", "City of Seattle", _soda_page(SHORT_TERM_RENTALS),
           "municipality", "City of Seattle", "Source rental license record",
           "Licensed inventory does not represent all operating rentals."),
    Source("seattle.business", "Business Licenses", "City of Seattle", _soda_page(BUSINESS_LICENSES),
           "municipality", "Seattle business licensing jurisdiction", "Source business license record",
           "Licensing jurisdiction is not necessarily the business location; not all regional businesses."),
    Source("seattle.311", "311 Requests", "City of Seattle", _soda_page(CSR_311),
           "municipality", "City of Seattle", "One service request",
           "2020 onward; requests reflect reporting behavior, not the prevalence of problems."),
    Source("seattle.parks", "Parks", "Seattle Parks and Recreation", _arcgis_layer(PARK_BOUNDARIES),
           "municipality", "Seattle parks inventory", "Source park feature",
           "Not all regional public lands; water association is inferred from park names."),
    Source("seattle.art", "Public Art", "Seattle Office of Arts & Culture", _arcgis_layer(PUBLIC_ART),
           "municipality", "Seattle public art inventory", "Source artwork feature",
           "Not a comprehensive inventory of art across the region."),
    Source("seattle.trees", "Street Trees", "Seattle Department of Transportation", _arcgis_layer(SDOT_TREES),
           "municipality", "Seattle managed street-tree inventory", "One inventory tree",
           "Not canopy coverage or all trees; map shows a sample of up to 15,000 trees."),
    Source("epa.air", "Air Quality", "US EPA", "https://aqs.epa.gov/aqsweb/airdata/download_files.html",
           "station", "EPA monitor search in " + ", ".join(AQS_COUNTIES.values()), "Monitor/pollutant/day observations",
           "PM2.5 and ozone, 2019 onward; monitoring locations do not provide uniform county coverage."),
    Source("noaa.weather", "Rain & Records", "NOAA", "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-inventory.txt",
           "station", "GHCN-Daily temperature stations across the region", "Station/day/measurement",
           "Every county's charts use its headline station (most days with rain and temperature); 2014 onward. A station is not every city's weather."),
    Source("usgs.water", "Water", "USGS", "https://waterservices.usgs.gov/nwis/dv/",
           "station", "USGS streamflow gages, region counties (Island & Kitsap have none)", "Station/day streamflow",
           "Per-county headline gage; not regional water supply or every watershed. 2014 onward."),
    Source("noaa.tides", "Water", "NOAA", "https://tidesandcurrents.noaa.gov/",
           "station", "NOAA tide gauges in the 5 saltwater-front counties", "Station/month tidal datum",
           "Only coastal counties have a gauge; datum and observation period matter for comparisons."),
    Source("nrcs.snow", "Water", "NRCS", "https://wcc.sc.egov.usda.gov/awdbRestApi/",
           "station", "NRCS SNOTEL stations in the mountainous counties (7 of 10)", "Station/day snow-water equivalent",
           "Lowland counties (Island/Kitsap/Thurston) have no station; not a regional snowpack average."),
    Source("federal.ntd", "Transit Ridership", "FTA National Transit Database", _soda_page(NTD_RIDERSHIP),
           "agency", "Configured NTD operators: " + ", ".join(NTD_AGENCIES.values()),
           "Agency/mode/month ridership",
           "Curated operators, 2015 onward; unlinked passenger trips are boardings, not unique people. No county allocation."),
    Source("federal.ntd.ferry", "Ferry Ridership", "FTA National Transit Database", _soda_page(NTD_RIDERSHIP),
           "agency", "Ferry-mode records within the configured NTD operator list",
           "Agency/ferry-mode/month ridership",
           "Shares the transit source; no route/county allocation. Regional operator completeness has not been verified."),
)
validate_sources(DATA_SOURCES)

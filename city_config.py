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

# SPD crime + Fire 911 are huge (full history is millions of rows); cap the baked
# warehouse to recent years for lean, fast builds (Elvis precedent). Filter is a
# SoQL $where on the datetime field.
CRIME_START = "2019-01-01"   # ~630k rows since 2019
FIRE_START = "2019-01-01"

# SPD crime uses a -1.0 sentinel (not null) for missing lat/lon (~11% of rows);
# staging must filter these before they plot at (-1, -1). Very recent SPD rows
# (~last 30 days) arrive with REDACTED geo until finalized.
SPD_CRIME_GEO_SENTINEL = -1.0

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
# Full Seattle metro per the interview: King + Pierce + Snohomish.
AQS_STATE = "53"  # Washington
AQS_COUNTIES = {
    "033": "King",
    "053": "Pierce",
    "061": "Snohomish",
}
AQS_PARAMS = {"88101": "PM2.5", "44201": "Ozone"}  # param code -> label
# The national daily bulk files are large and EPA's server is slow (~20-35s each),
# so — like crime/fire — the baked warehouse caps to recent years for lean builds.
# 2019 still spans the 2020 & 2022/2023 wildfire-smoke seasons.
AQS_START_YEAR = 2019
AQS_END_YEAR = 2026  # inclusive; the current year's file is partial but published

# --------------------------------------------------------------------------- #
# NOAA GHCN-Daily — keyless station CSV                                        #
# --------------------------------------------------------------------------- #
# Seattle-Tacoma International Airport (Sea-Tac).
NOAA_STATION = "USW00024233"

# --------------------------------------------------------------------------- #
# Sources still being verified before they get wired (see TASKS.md Group TOPIC)#
# --------------------------------------------------------------------------- #
# Placeholders only — do NOT fetch these until each is confirmed live and its
# dataset id / layer path recorded above.
UNVERIFIED = (
    "water_body",         # USGS NWIS + NOAA tides 9447130 + SPU/SNOTEL (all three)
    "tourism",            # Port of Seattle (Sea-Tac) passengers + Visit Seattle
    # weather (NOAA GHCN-Daily USW00024233) — VERIFIED + WIRED 2026-08-11.
    # air_quality (EPA AQS bulk, WA 53 / 033 / 053 / 061) — VERIFIED + WIRED 2026-08-11.
    # parks (Seattle ArcGIS Park_Boundaries) — VERIFIED + WIRED 2026-08-12.
    # Marriage Licenses intentionally DROPPED (no Seattle/KC open feed) — logged.
)

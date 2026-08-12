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

# Verified-live Socrata dataset ids (domain, dataset_id).
# Verified 2026-08-11: Seattle DCI Building Permits, ~192k rows, 40 cols.
PERMITS = (SEATTLE_SOCRATA, "76t5-zqzr")

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
AQS_START_YEAR = 2015

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
    "spd_crime",          # SPD Crime Data 2008-Present (Socrata, use CSV export)
    "food_inspections",   # Food Establishment Inspections (King County Socrata)
    "sfd_911",            # Seattle Fire 911 dispatch (Socrata)
    "short_term_rentals", # Seattle STR licenses (Socrata)
    "business_licenses",  # City of Seattle business license tax certificates
    "parks",              # Seattle/King County parks (ArcGIS)
    "public_art",         # Office of Arts & Culture (Socrata/ArcGIS)
    "water_body",         # USGS NWIS + NOAA tides 9447130 + SPU/SNOTEL
    "tourism",            # Port of Seattle (Sea-Tac) passengers + Visit Seattle
    # Marriage Licenses intentionally DROPPED (no Seattle/KC open feed) — logged.
)

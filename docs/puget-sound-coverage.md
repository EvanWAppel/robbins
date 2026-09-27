# Puget Sound source coverage audit

Updated 2026-09-27. This matrix audits configured integrations, not live data
completeness. See Data Coverage in the app for loaded air observations and dates.

**Codes:** S = Seattle-only integration (partial King County); K = King County
inspection jurisdiction; A = county filter configured for EPA monitors (actual
pollutant/date coverage must be checked); T = agency totals, county allocation
unavailable; P = station series, broader coverage unverified; U = regional source
not yet verified or integrated. U does not mean no public source exists.

| Topic | Island | Jefferson | King | Kitsap | Mason | Pierce | Skagit | Snohomish | Thurston | Whatcom |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 311 Requests | U | U | S | U | U | U | U | U | U | U |
| Air Quality | A | A | A | A | A | A | A | A | A | A |
| Building Permits | U | U | S | U | U | U | U | U | U | U |
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

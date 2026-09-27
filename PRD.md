# Robbins — PRD

> **Status:** Shipped — live on Railway · **Owner:** Evan Appel · **Date:** 2026-08-11
> (updated 2026-09-26; Puget Sound expansion planned in §12)
> A Seattle-metro open-data explorer, and the **flagship** of a family of open-data
> apps that share one engine. The same architecture powers **elvis** (Las Vegas) and
> **groening** (Portland): re-targeting the whole pipeline to a new metro is a single
> config-file change (`city_config.py`). elvis and groening prove the engine ports
> across cities; robbins is the most complete of the three — the shipped, hosted one,
> and the only one with the third (federal-bulk) ingestion pattern, a dbt data-quality
> test suite, and full model docs. See [`PRIMER.md`](./PRIMER.md) for the handoff
> context and the Vegas→Seattle source mapping; this document specifies the product.

---

## 1. Problem

Seattle-area public data is scattered across many portals and agencies — Seattle
Open Data (Socrata), Seattle GeoData (ArcGIS), King County GIS, Public Health –
Seattle & King County, EPA, NOAA, USGS, Port of Seattle — in inconsistent formats
(Socrata SODA API, ArcGIS FeatureServers, CSV exports, EPA/NOAA bulk files). There
is no single place to browse the region's civic data as maps, trends, and
searchable tables. Separately, Evan needs a **portfolio piece** demonstrating
end-to-end data engineering: multi-source ingestion, a reproducible warehouse, dbt
modeling, and an interactive app.

## 2. Goals

1. **One explorer for Puget Sound public data** — maps, charts, and searchable
   tables across the region's most useful open datasets, in one Streamlit app.
2. **Reproducible, hands-off pipeline** — a single `build_warehouse.py` fetch +
   `dbt build` recreates the entire warehouse from public sources on every deploy.
3. **Portfolio proof for a Data / Data-Engineering role** — showcase ELT
   orchestration and multi-source ingestion across **three access patterns** (Socrata
   SODA + ArcGIS FeatureServer + keyless federal bulk files), a tested dbt
   staging/marts model, and deployment.
4. **Cheap to run, easy to redeploy** — embedded DuckDB, no database server, no
   real secrets, warehouse baked into the image at build time.

## 3. Non-goals

- **Not a real-time system.** Data is as fresh as the last deploy/build.
- **Not a new stack.** Identical to Elvis by decision — no reevaluating
  DuckDB/dbt/Streamlit/Railway. (The net-new code versus Elvis is the
  `fetch_socrata()` helper plus a set of keyless federal-feed fetchers.)
- **Not a shared design system with other portfolio apps.** Robbins has its own
  look, like every other project under `evanappel.me`.
- **No auth; no real secrets.** Public data only. (A Socrata app token is optional
  and only raises rate limits — not a protected secret.)
- **Not exhaustive.** Expand existing topics across the confirmed Puget Sound
  geography where reliable public sources exist; document gaps under §12.

## 4. Principles & constraints

- **Port, don't reinvent.** Elvis's architecture, fetch helpers, dbt layout, and
  Dockerfile are the blueprint. Add `fetch_socrata()`; keep everything else.
- **One config surface.** All city-specific values (Socrata domains + dataset ids,
  ArcGIS orgs, FIPS codes, station code, year ranges) live in `city_config.py`.
- **Warehouse is built at Docker build time**, never at runtime. The `.duckdb`
  file is a git-ignored build artifact.
- **Honor the house style** (`CLAUDE.md`): `uv`, `uv run python`, `ruff` + `ty` +
  `prek` + `pytest`, dependencies only via `uv add`, don't hide or wrap errors, use
  `logging`, never push to `main`/`master`.
- **Verify every source before wiring it.** The Seattle leads in the primer are
  starting points; confirm each is live and machine-readable, and `log()` any topic
  dropped for lack of a source.
- **dbt two-tier is the analytics contract:** `staging/` views normalize raw
  schemas; `marts/` tables aggregate/denormalize for the app. Pages read marts only.
- **Prefer CSV export for large Socrata datasets.** Let DuckDB ingest the SODA CSV
  export URL directly rather than paging millions of JSON rows (e.g. SPD crime).

## 5. Scope — topic inventory (target)

Mirror of Elvis, adjusted for Seattle. Final status per topic is confirmed in
`TASKS.md` after source verification; this is the plan. **Portal** = access pattern.

| # | Page | Seattle source (lead) | Portal | Status |
| --- | --- | --- | --- | --- |
| 1 | **Overview** | Derived from the marts that exist | — | Keep |
| 2 | **Building Permits** | Seattle DCI permits (`data.seattle.gov`) | Socrata | Keep (high confidence) |
| 3 | **Police / Crime** | SPD Crime Data 2008-Present | Socrata | Keep (use CSV export) |
| 4 | **Restaurant Inspections** | Food Establishment Inspections (Public Health – Seattle & King County) | Socrata | Keep (high confidence) |
| 5 | **Parks** | Seattle Parks & Rec boundaries + water-feature flags | ArcGIS | Keep (high confidence) |
| 6 | **Air Quality** | EPA AQS bulk, WA 53 / King 033 (+ Pierce, Snohomish) | keyless | Keep (high confidence) |
| 7 | **Weather (Rain & Records)** | NOAA GHCN-Daily, Sea-Tac `USW00024233` | keyless | Keep (rename from "Desert Heat") |
| 8 | **Fire 911 Calls** | Seattle Fire 911 dispatch | Socrata | Reframe (from fire inspections) |
| 9 | **Short-Term Rentals** | Seattle STR licenses | Socrata | Keep (verify) |
| 10 | **Business Licenses** | City of Seattle business license tax certificates / WA DOR | Socrata | Keep (verify) |
| 11 | **Signature Water Body** | Lake Washington/Cedar (USGS NWIS), Puget Sound tides (NOAA), or reservoir/snowpack (SPU/SNOTEL) | API | Keep (pick one — interview #4) |
| 12 | **Tourism / Air Travel** | Port of Seattle (Sea-Tac) passengers + Visit Seattle | web/CSV | Reframe (drop gaming) |
| 13 | **Public Art** | Seattle Office of Arts & Culture / GeoData | Socrata/ArcGIS | Verify / optional |
| 14 | **Marriage Licenses** | King County Recorder | ? | Candidate to drop (risk) |
| + | **Seattle extras** | e.g. 311 (Find-It-Fix-It), transit ridership, tree canopy, seismic zones | mixed | Optional — interview #7 |

## 6. Key decisions (decision log)

| # | Decision | Rationale |
| --- | --- | --- |
| D1 | **Port Elvis, don't design fresh.** | Battle-tested architecture; fastest path to a credible portfolio piece. |
| D2 | **Identical stack** (DuckDB + dbt-duckdb + Streamlit + PyDeck/Altair). | Reuse patterns and helpers wholesale. |
| D3 | **Original target: Seattle / King County; expansion: Puget Sound (§12).** | Broaden geographic coverage through verified sources and explicit coverage metadata. |
| D4 | **Add `fetch_socrata()`; keep ArcGIS helpers.** | Seattle is Socrata-first (city) but King County GIS is ArcGIS — need both. |
| D5 | **Mirror Elvis's topics where data exists; drop the gaps.** | Breadth where cheap; no thin/unreliable sources. |
| D6 | **Centralize city config in `city_config.py`.** | A single config surface makes the port (and future cities) a one-file change. |
| D7 | **Warehouse baked at Docker build time; `.duckdb` git-ignored.** | Predictable cold starts; reproducible from public sources. |
| D8 | **No gaming page; reframe Tourism around Sea-Tac air travel; reframe fire as SFD 911 calls.** | No gaming analog; Seattle publishes 911 dispatch, not fire inspections. |
| D9 | **Broad Data/DE portfolio framing.** | Emphasize end-to-end ELT and two-pattern multi-source ingestion. |
| D10 | **Keep the Vegas gotchas that still apply** (force IPv4 for EPA AQS; per-host `ssl_verify=False`, logged). | Same EPA host; municipal GIS servers still ship bad certs. |

## 7. Architecture

Identical to Elvis (see `PRIMER.md` §1), plus `fetch_socrata()`. Repo layout:

```
robbins/
├── build_warehouse.py     # ETL: fetch every source -> raw.* DuckDB tables (Socrata + ArcGIS)
├── city_config.py         # ALL Seattle-specific constants (the "which city" file)
├── streamlit_app.py       # multi-page router (st.Page + st.navigation)
├── app_db.py              # read-only DuckDB connection + @st.cache_data query()
├── dbt_project.yml        # name/profile: robbins ; staging=view, marts=table
├── profiles.yml           # dbt-duckdb, path -> seattle.duckdb
├── Dockerfile             # build: build_warehouse.py && dbt build ; run: streamlit on $PORT
├── requirements.txt       # pip fallback for Docker
├── pyproject.toml / uv.lock
├── models/
│   ├── staging/           # stg_*.sql views + sources.yml
│   └── marts/             # mart_*.sql tables
├── views/                 # one *.py Streamlit page per kept topic
├── tests/                 # pytest; conftest.py fixtures (DRY)
└── seattle.duckdb         # build artifact; NOT in git
```

**Data flow:** `build_warehouse.py` (build time; Socrata SODA + ArcGIS) → `raw.*`
→ `dbt build` → `staging` views → `marts` tables → Streamlit reads marts via
`app_db.query()`.

## 8. Configuration & secrets

- **No real secrets.** All data is public.
- **`city_config.py`** holds every city-specific value: Socrata domains
  (`data.seattle.gov`, `data.kingcounty.gov`) + dataset ids, King County / Seattle
  ArcGIS roots, EPA AQS state/county FIPS, NOAA station code, source URLs, year
  ranges, and (optional) a Socrata app token.
- Runtime needs only `$PORT` (injected by Railway; default `8501` locally).

## 9. Deployment

- **Railway**, from the `Dockerfile`. No Procfile, no `railway.toml`.
- Build stage runs `build_warehouse.py && dbt build --profiles-dir .`, baking
  `seattle.duckdb` into the image.
- Runtime: `streamlit run streamlit_app.py --server.port ${PORT:-8501}
  --server.address 0.0.0.0`.
- **Optional (interview #8):** register under the portfolio orchestrator manifest
  and expose at `robbins.evanappel.me`.

## 10. Success metrics

- **Reproducible:** a clean `uv sync && uv run python build_warehouse.py &&
  uv run dbt build --profiles-dir . && uv run streamlit run streamlit_app.py`
  produces the full app locally.
- **Deployed:** live on Railway, warehouse baked in the image, serving on `$PORT`.
- **Coverage:** 15 working topic pages spanning all three ingestion patterns
  (Socrata, ArcGIS, federal bulk); every dropped topic explicitly logged with its
  reason.
- **Portfolio-ready:** README explains the ELT + dbt + Streamlit story and the
  three-pattern ingestion for a Data/DE audience.

## 11. Original scope interview (historical)

Current expansion decisions are tracked in §12. The interview outcomes in
`TASKS.md` resolve several questions below; these remain as planning history.

Resolve via the re-runnable interview in `PRIMER.md` §7.1 before finalizing the
page list:

1. Metro breadth — King County only vs. + Pierce + Snohomish (affects GIS orgs +
   AQS FIPS list).
2. Confirm the drop list (Marriage Licenses; anything else).
3. Signature water body — Lake Washington/Cedar (USGS NWIS) vs. Puget Sound tides
   (NOAA) vs. reservoir/snowpack (SPU/SNOTEL).
4. Seattle-specific extras worth adding (311, transit ridership, tree canopy…).
5. Deploy target — standalone Railway vs. orchestrator + `*.evanappel.me` subdomain.

### Resolved (carried from Groening interview, 2026-08-11)

- **Metro** = Seattle / King County.
- **Stack** = identical to Elvis (+ `fetch_socrata()`).
- **Scope** = mirror Elvis where data exists.
- **Framing** = broad Data / Data-Engineering portfolio piece.
- **Codename** = `robbins` (bikeable).

## 12. Puget Sound expansion — planned, 2026-09-26

**Development started 2026-09-27.**

**Intent:** expand Robbins from a Seattle-centered atlas into an explorer for the
whole Puget Sound area. This is a new implementation program; existing shipped
checkboxes do not imply regional coverage. This section supersedes the original
Seattle-only target where they conflict. The existing application remains the
baseline while expansion ships in independently validated increments.

### Scope decisions

- **Geographic boundary (confirmed 2026-09-27):** King, Pierce, Snohomish,
  Kitsap, Island, Skagit, Thurston, Mason, Jefferson, and Whatcom counties,
  including cities and unincorporated areas. These administrative boundaries
  define product coverage, not an ecological definition of Puget Sound.
- **Navigation (confirmed):** one regional explorer with county/city filters.
- **Incomplete coverage (confirmed):** publish partial coverage with clear
  geographic and observation-date labels; missing coverage is never a zero.
- **Priorities (confirmed):** environment and mobility first, after shared
  foundations. Air quality is the first slice, reusing the existing EPA feed.
- **Topic breadth:** regionalize existing topics first. New topics remain explicit
  backlog candidates; this expansion does not automatically revive dropped topics.

### Current baseline and gaps

The current configuration includes Seattle civic feeds, King County food
inspections, air-quality monitors in King/Pierce/Snohomish, a curated transit and
ferry agency list, and individual weather/water stations. An agency's service
area or one station's observations must not be presented as county-wide coverage.
Existing Seattle neighborhood maps use SPD MCPP boundaries; those boundaries
cannot serve as a regional neighborhood system.

The source audit must distinguish implemented coverage from intended coverage.
Historic statements about unavailable sources are leads for re-verification,
not current evidence that regional equivalents do or do not exist.

### Required experience

1. Show the selected place, actual reporting coverage, observation period, source,
   and last successful retrieval on every topic. Distinguish no data, unavailable
   coverage, stale data, and a verified zero.
2. Geographic selection must apply consistently to maps, charts, tables, overview
   metrics, and Ask the Data. Preserve a valid selection across page navigation;
   explain unsupported selections without silently falling back to Seattle.
3. Include cities and unincorporated county areas. Use stable geographic IDs and
   explicit boundary versions; do not equate a city's records with its county.
4. Keep maps top-down with legible basemaps. Use dots for individual locations and
   shaded areas for comparable area metrics. Fit maps to the selected geography;
   retain Seattle MCPP detail only where it applies. Label samples, cap displayed
   points, and ensure small jurisdictions remain represented in regional samples.
5. Compare jurisdictions only when definitions, units, coverage, and periods
   align. Show incompatible series separately with explanations. Regional totals
   must not double-count overlapping municipal, county, or agency feeds.
6. Distinguish density per square mile from population-adjusted rates. Any new
   per-capita comparison requires a documented population source, matching place
   and year, and an explicit denominator; raw counts must not imply relative risk.
7. Keep public-facing branding and geographic claims aligned with the actual
   launch scope. A regional title alone is not completion of the expansion.

### Source and data contracts

Create a source/coverage inventory for every target county and existing topic.
Record publisher, dataset URL and ID, verification date, access method, reuse
terms, geographic extent, reporting agency, record grain, source key, date range,
refresh cadence, units, coordinate system, known exclusions, and comparability.
Track candidates, verified sources, implemented sources, and documented gaps
separately. Verify official machine-readable sources before wiring them.

Extend the existing centralized configuration to multiple jurisdictions and
sources; retain DuckDB, dbt, Streamlit, PyDeck/Altair, and build-time ingestion.
Stage each source without discarding provenance. Define source-qualified record
keys, canonical geographic dimensions, agency/station relationships, and explicit
crosswalks before unioning datasets. Preserve unknown geography and report
assignment coverage rather than silently excluding unmatched records.

A county source may cover only unincorporated land; a transit agency may cross
county boundaries. Keep reporting jurisdiction, event location, service area,
and station location distinct. Agency-wide ridership must not be apportioned to
counties or routes without supporting data. Station observations remain station
observations unless a defensible aggregation method is specified.

Remove hardcoded Seattle bounding boxes and single-station assumptions where
applicable. Handle missing coordinates, boundary-edge points, multipart geometry,
and source revisions. Use deduplication rules specific to record grain; repeated
inspections or multiple permits at an address are not automatically duplicates.

Make geography and coverage available to marts, the metric registry/generated
models, the catalog, and Ask the Data. Preserve SQL safety and read-only access;
answers must disclose scope and avoid inventing unavailable regional totals.

### Delivery phases and acceptance

| Phase | Deliverable | Exit criteria |
| --- | --- | --- |
| 0 — Scope and discovery | Confirmed county list, experience, priorities, source/coverage matrix | Every target county × existing topic has a recorded status; selected slice has verified sources and compatible definitions |
| 1 — Foundation and slice | Shared geography, coverage metadata, one topic end to end | Slice includes Seattle and at least one new jurisdiction; filters affect all relevant outputs; unsupported places are explicit; counts reconcile to source aggregates |
| 2 — Environment and mobility | Regional air, weather, water, transit, ferry coverage | Audited stations/agencies for every target county; supported sources integrated; gaps recorded; no invented county or route allocation |
| 3 — Civic breadth | Permits, parks, inspections, art, trees, licenses, STR, crime, fire, 311 | Each county/topic has implemented coverage or an explicit gap under the selected coverage policy; incompatible definitions remain separate |
| 4 — Release | Regional overview, documentation, operational validation | Coverage claims match inventory; existing Seattle views work; quality gates and regional UX checks pass; owner approves deployment |

Phases 2 and 3 may ship by topic after the slice passes. Do not promise every
municipality publishes every dataset. Release scope and exclusions must be
reviewable against the coverage matrix rather than inferred from page count.

### Validation, performance, and operational limits

- Test parsers/transforms with synthetic fixtures first. Include duplicate source
  IDs across jurisdictions, overlapping feeds, unavailable coverage, unknown
  geography, missing coordinates, and incompatible time windows/units.
- Add dbt uniqueness, relationships, accepted-value, and aggregate reconciliation
  checks. Verify geographic filters and coverage labels across all app surfaces.
- Benchmark the existing build time, image/warehouse size, runtime memory, query
  latency, and map load times. Set numeric budgets before expanding ingestion;
  evaluate regional loads against those budgets before release.
- Set explicit history windows and map sample limits per topic. Required-source
  failures must fail visibly; any optional-source omission needs a recorded status
  exposed in coverage metadata. Never substitute missing observations with zeros.
- Run Ruff, ty, pytest, dbt checks, page smoke checks, and browser verification of
  region/county/city navigation, no-data states, maps, and mobile layouts. Rehearse
  the Docker build and rollback to the prior image before authorized deployment.

**Completion:** the confirmed geography is represented in navigation and the
coverage inventory; each county/topic cell is implemented or explicitly classified
under the agreed policy; all regional claims and aggregates are supported; the
owner can review coverage, exclusions, and measured performance before release.

# Robbins — TASKS

Implementation task board for [`PRD.md`](./PRD.md). Originally a port of **Elvis**
(Las Vegas) to Seattle; next is the Puget Sound expansion program below.
Read [`PRIMER.md`](./PRIMER.md) first for the
Vegas→Seattle source mapping, the `fetch_socrata()` helper, and known gotchas.

## How to use this board

- Each task has a unique ID and a `[ ]` checkbox. Mark `[x]` when done, `[~]` when
  partial (leave a note).
- **TDD is mandatory for every parser/transform task** (including `fetch_socrata`):
  write a failing `pytest` test first, implement until green, then refactor. Shared
  fixtures go in `tests/conftest.py` (DRY).
- **House rules apply** (`CLAUDE.md`): `uv` only (`uv add` / `uv add --dev`, never
  edit `pyproject.toml` by hand), `uv run python`, lint with `ruff`, typecheck with
  `ty`, pre-commits with `prek`. Do not hide or wrap errors. Use `logging`. Never
  push to `main`/`master`.
- **Do the vertical slice (Group VS) first and confirm it deploys** before fanning
  out to the rest of the topics.
- **Verify every source before wiring it.** `log()` any topic dropped for lack of a
  source.

## Interview outcomes (fill in before coding pages)

Carried from the Groening interview 2026-08-11 (see `PRD.md` §11 Resolved): metro =
Seattle/King County; stack = identical to Elvis + `fetch_socrata()`; scope = mirror
Elvis where data exists; framing = broad Data/DE; codename = `robbins`.

**Seattle-specific interview (`PRIMER.md` §7.1) — answered with Evan 2026-08-11:**

- [x] Metro breadth: **Full metro — King + Pierce + Snohomish.** AQS FIPS = WA `53`,
  King `033`, Pierce `053`, Snohomish `061`. Include Pierce/Snohomish GIS + cities
  (Tacoma, Bellevue, Everett) where datasets cover them.
- [x] Confirmed drop list: **Marriage Licenses only** (log the drop). Attempt every
  other topic; drop others only if source verification actually fails.
- [x] Signature water body: **All three — be ambitious.** Lake WA/Cedar River (USGS
  NWIS) + Puget Sound tides (NOAA Tides & Currents 9447130) + reservoir/snowpack
  (SPU / NRCS SNOTEL). One water page, multiple series.
- [x] Fire page = **SFD 911 dispatch calls** (confirmed; Seattle doesn't publish fire
  inspections).
- [x] Tourism = **Sea-Tac passenger volumes + Visit Seattle** (confirmed; no gaming).
- [x] Public Art = **keep** (not dropped).
- [x] Seattle-specific extras: **shipped** 311/Find-It-Fix-It, transit ridership, ferry
  ridership, and street trees (2026-08-15). Tree-canopy rasters + seismic zones remain
  deferred (no strong tabular source).
- [x] Deploy target: **Standalone Railway** from the Dockerfile (orchestrator +
  `robbins.evanappel.me` deferred; DEPLOY-06 stays optional).

## Parallelization guide

```
VS  (vertical slice) ─────────────► must finish & deploy first
        │
        ├── CONFIG  (city_config.py)     ─┐
        ├── SOCRATA (fetch_socrata helper) │  seeded by VS, refined in parallel
        ├── ETL     (ArcGIS helpers port)  │
        └── TOPIC   (one page per dataset) ┘  fan out AFTER sources verified
DEPLOY / DOCS: after ≥ VS; finalize at the end.
```

Within Group TOPIC, each dataset is an independent task — assign one agent per
topic. They touch different `stg_`/`mart_`/`views/` files, so they don't collide.

---

## Group VS — Vertical slice (DO FIRST) 🎯

Goal: one topic working end to end — fetch → staging view → mart → Streamlit page
→ **deployed to Railway** — proving the whole pipe before breadth. Pick a
high-confidence Socrata source (**Building Permits** or **SPD Crime**) or an ArcGIS
source (**Parks** via King County / Seattle GeoData).

**Slice topic chosen: Building Permits (Seattle DCI, Socrata `76t5-zqzr`).** Verified
live 2026-08-11 (~192k rows). Exercises the net-new `fetch_socrata()` helper.

- [x] **VS-01** — Scaffolded uv project (Python pinned 3.12 for dbt/Docker parity);
  runtime + dev deps added via `uv add`; imports confirmed.
- [x] **VS-02** — Ported `app_db.py`, `dbt_project.yml`, `profiles.yml`, `Dockerfile`,
  `requirements.txt`, `.gitignore`, `.dockerignore`, `.streamlit/config.toml`, and a
  minimal `streamlit_app.py`. Renamed `vegas.duckdb`→`seattle.duckdb`, `elvis`→`robbins`.
- [x] **VS-03** — Created `city_config.py` (Socrata domains + verified permits id; full
  metro AQS FIPS 53/033/053/061; NOAA `USW00024233`; unverified topics parked).
- [x] **VS-04** — Added `fetch_socrata()` (SODA `$limit`/`$offset` paging until a short
  page, default `$order=:id` for stable paging, CSV-export URL builder, optional
  `X-App-Token`, zero-row raise). TDD: 9 tests green (`tests/test_fetch_socrata.py`).
- [x] **VS-05** — Fetched 192,185 permits → `raw.building_permits` (40 cols, 1986–2026).
- [x] **VS-06** — `stg_building_permits.sql` + `sources.yml`; marts `mart_permits_monthly`,
  `mart_permits_by_class`, `mart_permits_map_sample`. `dbt build` green (4 models).
- [x] **VS-07** — `views/building_permits.py`: KPIs + monthly area/line charts + by-class
  bar + PyDeck hexbin map. Verified rendering in-browser (no console errors).
- [x] **VS-08** — Deployed to Railway ✅ Project `robbins`; `railway up` bakes the
  warehouse at build time (43 dbt models) and serves Streamlit on injected `$PORT`.
  Live at https://robbins-production.up.railway.app (verified in-browser).

**Exit criteria:** ✅ local — `pytest`, `ruff`, `ty` all green; page renders; Docker
image bakes + serves on `$PORT`. ✅ Railway deploy live.

---

## Group SOCRATA — SODA API ingestion (net-new vs. Elvis)

- [x] **SOCRATA-01** — `fetch_socrata()` with `$limit`/`$offset` paging until a short
  page (default `$order=:id`). TDD: 9 tests (`tests/test_fetch_socrata.py`). ✅ (VS-04)
- [x] **SOCRATA-02** — CSV path: `socrata_resource_csv_url()` (SoQL `$where`-filterable
  `.csv`) + `socrata_csv_url()` bulk export → `ingest_csv()` via DuckDB `read_csv_auto`.
  Used for SPD crime, Fire 911, and 311. ✅
- [x] **SOCRATA-03** — Optional `X-App-Token` from `city_config.SOCRATA_APP_TOKEN`;
  anonymous still works; the fetch logs `app_token=yes/no`. ✅
- [x] **SOCRATA-04** — Zero rows raises in both `fetch_socrata()` and `ingest_csv()`. ✅

---

## Group CONFIG — City configuration

- [x] **CONFIG-01** — Seattle Socrata domain + dataset ids for all kept topics
  (permits, crime, fire, STR, licenses, 311) recorded in `city_config.py`. ✅
- [x] **CONFIG-02** — King County Socrata (`data.kingcounty.gov`, food inspections) +
  Seattle ArcGIS org root (`ZOyb2t4B0UYuYNYH`) for art, parks, and trees. ✅
- [x] **CONFIG-03** — EPA AQS FIPS WA `53` + King `033` / Pierce `053` / Snohomish
  `061` (full metro). ✅
- [x] **CONFIG-04** — NOAA GHCN-Daily Sea-Tac `USW00024233`. ✅
- [x] **CONFIG-05** — SPD crime `tazs-3rd5`, `CRIME_START=2019-01-01`. ✅
- [x] **CONFIG-06** — Water sources: USGS `12119000`, NOAA tides `9447130`, SNOTEL
  `791:WA:SNTL`. ✅

---

## Group ETL — Ingestion hardening

- [x] **ETL-01** — Force-IPv4 (`_ipv4_first` global `getaddrinfo` wrapper) carried over;
  AQS fetch completes locally + on Railway. ✅
- [x] **ETL-02** — ArcGIS `fetch_features()` (paging, WGS84 reprojection, polygon
  centroids) with the per-host `ssl_verify=False` escape hatch (logged loudly). ✅
- [~] **ETL-03** — cp1252 handling not needed: every shipped source is JSON, UTF-8
  CSV, or a zip DuckDB/pandas reads directly. No muni bulk file required a cp1252
  decode, so no `_read_delimited` was added. Re-open if a future topic hits one.
- [x] **ETL-04** — Every fetch logs source, URL, and row count. ✅

---

## Group TOPIC — One task per dataset (fan out; TDD each transform)

Start only after the interview outcomes (drop list, metro breadth, water body, fire
reframe) are recorded above and each source is verified. For each: fetch → `stg_`
view → `mart_` table → `views/*.py` page. Drop and **log** any topic without a
source.

- [x] **TOPIC-permits** — Building Permits (Seattle DCI, Socrata `76t5-zqzr`). ✅ VS topic.
- [x] **TOPIC-crime** — SPD Crime (`tazs-3rd5`, CSV export, recent yrs). Hexbin map. ✅
- [x] **TOPIC-restaurants** — Food inspections (King County `r878-4sxa`). ✅ non-spatial.
- [x] **TOPIC-parks** — Parks (Seattle GIS `Park_Boundaries`, ArcGIS, ~511 pts). ✅ Size
  bands, acreage map (sized by area, water-name parks in blue), largest table. Water
  flag is name-derived (word-boundary regex, TDD'd; fixed a "cove"⊂"Discovery" false
  positive). Verified in-browser.
- [x] **TOPIC-air** — Air Quality (EPA AQS bulk, WA FIPS 53/033/053/061). ✅ PM2.5 +
  Ozone daily, 2019+ (capped for lean builds; ~6 min of EPA downloads at build time).
  Category distribution, monthly peak-AQI (wildfire-smoke spikes), monitor map, worst
  days. Verified in-browser.
- [x] **TOPIC-weather** — Weather (NOAA GHCN-Daily, Sea-Tac `USW00024233`). ✅ "Rain &
  Records": monthly climatology, temp band, annual trend, all-time records. 3rd
  ingestion pattern (federal bulk CSV). Verified in-browser.
- [x] **TOPIC-fire** — SFD 911 dispatch (`kzjm-xkqj`). ✅ Reframed from inspections.
- [x] **TOPIC-str** — Short-Term Rental licenses (`s7df-xba4`). ✅ scatter map.
- [x] **TOPIC-licenses** — Business license tax certificates (`wnbq-64tb`). ✅
- [x] **TOPIC-water** — Signature water body, **all three** ✅ USGS Cedar River @ Renton
  (streamflow), NOAA Seattle 9447130 (sea-level datums), NRCS SNOTEL Stampede Pass
  (snowpack). One `build_water` → 3 raw tables; page has snowpack-by-water-year (2015
  drought), recent winters, Cedar hydrograph, sea-level trend w/ regression. Verified.
- [x] **TOPIC-tourism** — **DROPPED** (logged). No machine-readable Sea-Tac passenger
  feed exists: other cities publish airport traffic on open portals (NY Port Authority
  `8pkr-4b7t`, LAX `g3qu-7q2u`) but the Port of Seattle does not, and BTS T-100 is
  form/POST-only (not a clean GET). Checked 2026-08-12. **Pivot shipped** as
  TOPIC-ferry: WSF + King County Water Taxi monthly ridership from the federal NTD,
  a clean Puget Sound travel proxy with strong summer seasonality (2026-08-15).
- [x] **TOPIC-art** — Public Art — **ArcGIS** (`PublicArt2`, 758 pts, 754 geocoded). ✅ 2nd pattern.
- [x] **TOPIC-marriage** — Marriage Licenses — **DROPPED** (no Seattle/KC open feed). Logged.
- [x] **TOPIC-311** — Customer Service Requests / Find-It-Fix-It (Socrata `5ngg-rpne`,
  ~2.46M all-time, capped 2020+ ≈ 1.65M via CSV export). Page: monthly trend, top
  request types (abandoned vehicles, encampments, dumping, graffiti, potholes),
  reporting channel (77% via the Find-It-Fix-It app), owning department, hexbin map.
  Verified in-browser. ✅
- [x] **TOPIC-trees** — SDOT street trees (**ArcGIS** `SDOT_Trees_(Active)`, 211,713
  points, 777 species). Genus derived at fetch (TDD'd, `tests/test_trees.py`). Page:
  top species/genera, plantings by year, condition (mostly unassessed — a data-quality
  note), green hexbin density map. Verified in-browser. ✅
- [x] **TOPIC-transit** — Puget Sound transit ridership (**federal NTD** `8bui-9xvu` @
  `data.transportation.gov`, 2015+). Curated metro agencies; monthly UPT. Page: COVID
  collapse + 91% recovery, by-agency + by-mode, Link light-rail 6.2× growth. Verified. ✅
- [x] **TOPIC-ferry** — Ferry ridership (same NTD source, mode FB — the parked Tourism
  pivot). WSF + King County Water Taxi. Page: seasonal summer swell (July peak), 2020
  collapse, by-operator (WSF 98%), annual. Verified in-browser. ✅
- [x] **TOPIC-extras** — 311, transit, ferry, and street trees shipped (above). Remaining
  candidates (tree *canopy* rasters, seismic zones) deferred — no strong tabular source.
- [x] **TOPIC-overview** — ✅ Landing page (nav default): warehouse-wide headline (1.8M+
  records, 11 topics, 3 ingestion patterns) + themed KPI sections (City & Housing,
  Public Safety, Health & Food, Environment, Culture & Rec) each with `st.page_link`s
  into the detail pages. Aggregates existing marts only. Verified in-browser.

---

## Group DEPLOY — Ship & document

- [x] **DEPLOY-01** — `.gitignore` covers the build artifacts (`*.duckdb`, `target/`,
  `logs/`, `.venv/`, `__pycache__/`, `.DS_Store`). ✅ (since VS-02).
- [x] **DEPLOY-02** — `prek` pre-commit configured ✅ `.pre-commit-config.yaml` runs
  `ruff check` + `ty` on commit and `pytest` on push (local/system hooks → uv tools).
  Installed via `prek install`; hooks confirmed firing. `ruff format` intentionally
  NOT enforced (would rewrite the compact hand style; `ruff check` covers real issues).
- [x] **DEPLOY-03** — GitHub Actions CI ✅ `.github/workflows/ci.yml`: ruff + ty +
  pytest on every push/PR (uv-based; skips the warehouse bake — tests stub the network).
- [x] **DEPLOY-04** — Railway deploy live with all 8 shipped topics ✅ Project `robbins`
  on Evan's workspace; baked warehouse builds (43 models) and app serves at
  https://robbins-production.up.railway.app. Build ~ a few min (deps + full source
  fetch incl. ~6 min EPA AQS). Deployed from working dir via `railway up`.
- [x] **DEPLOY-05** — `README.md` refreshed ✅ live URL, three-pattern ingestion story
  (Socrata + ArcGIS + federal bulk), full 11-topic source table, dropped-topic note,
  local run + quality-gate steps.
- [ ] **DEPLOY-06** *(optional, interview #8)* — Register in the portfolio
  orchestrator manifest and wire `robbins.evanappel.me`.

---

## Original sequencing (historical)

- **Now:** VS (vertical slice, deployed) → SOCRATA/CONFIG/ETL alongside.
- **Then:** re-run interview §7.1, record outcomes, fan out Group TOPIC.
- **Finish:** Overview page, DEPLOY, docs.

## Puget Sound expansion — planned 2026-09-26

Implements PRD §12. Historical completed tasks above describe the original app,
not regional coverage. Development started 2026-09-27; partial work is marked explicitly.

Sequence: PS-SCOPE → PS-DISCOVERY → PS-FOUNDATION → PS-SLICE → PS-TOPICS →
PS-RELEASE. Shared contracts settle before topic implementation.

### Group PS-SCOPE — Product boundary and priorities

- [x] **PS-SCOPE-01** — Confirm the county list, geographic navigation, incomplete
  coverage policy, first topic, and priorities. Record answers in PRD §12 and the
  decision log; reconcile historical metro claims. Confirmed 2026-09-27: ten
  counties, shared county/city filters, labeled partial coverage, environment/
  mobility first; air quality selected for the first slice.
- [~] **PS-SCOPE-02** — Benchmark build time, image/warehouse size, runtime memory,
  query latency, and map load times; agree numeric budgets and history windows.

### Group PS-DISCOVERY — Verify sources (after PS-SCOPE)

- [~] **PS-DISCOVERY-01** — Create a county × existing-topic coverage matrix for
  every target county. Audit current sources/marts; distinguish candidate,
  verified, implemented, and unavailable coverage.
- [~] **PS-DISCOVERY-02** — Verify official machine-readable sources and record
  PRD §12 metadata, reuse terms, extent, dates, units, grain, and exclusions.
  Recheck historical source-drop claims where relevant to the agreed scope.
- [ ] **PS-DISCOVERY-03** — Document compatible metrics, periods, classifications,
  and overlapping feeds. Distinguish city, unincorporated, agency, and station
  coverage; define source-specific deduplication rules.
- [ ] **PS-DISCOVERY-04** — Select a verified slice covering Seattle and at least
  one new jurisdiction; record acceptance examples and unresolved gaps.

### Group PS-FOUNDATION — Shared contracts (after discovery)

Use test-first synthetic fixtures for parsers and transforms.

- [~] **PS-FOUNDATION-01** — Extend centralized configuration for multiple
  jurisdictions/sources, stable IDs, source-qualified keys, and provenance.
- [~] **PS-FOUNDATION-02** — Add versioned county/city geography and crosswalks,
  unincorporated/unknown geography, and agency/station relationships. Test boundary
  edges and multipart geometry; expose geographic assignment coverage.
- [~] **PS-FOUNDATION-03** — Add coverage metadata, observation/retrieval dates,
  and explicit unavailable/stale/zero states. Define required/optional source
  behavior; expose omissions rather than silently publishing incomplete totals.
- [~] **PS-FOUNDATION-04** — Build the agreed geographic navigation and selection
  state. Apply selection to maps/charts/tables/metrics; test persistence across
  pages and explain unsupported places without falling back to Seattle.
- [~] **PS-FOUNDATION-05** — Carry geography/coverage through marts, metric
  definitions/generated models, catalog, and Ask the Data. Preserve read-only SQL
  safety; test geographic scope and unavailable-data answers.
- [~] **PS-FOUNDATION-06** — Replace applicable Seattle map bounds/centers with
  selected geography. Preserve top-down dots/area maps and local MCPP detail;
  define representative regional samples, point caps, and sample labels.

### Group PS-SLICE — One regional topic end to end (after foundations)

- [~] **PS-SLICE-01** — Implement verified adapters, staging models, regional
  marts, and the selected topic UI using the shared contracts.
- [~] **PS-SLICE-02** — Reconcile source aggregate counts and test cross-source
  ID collisions, overlapping feeds, unknown geography, incompatible dates/units,
  no-data states, and geographic filters.
- [~] **PS-SLICE-03** — Pass dbt, pytest, Ruff, ty, page smoke checks, and browser
  checks for regional and existing Seattle behavior; measure against budgets.
  This exit gate precedes broad topic implementation.

### Group PS-TOPICS — Regional breadth (after slice acceptance)

Environment/mobility-first order confirmed by the owner on 2026-09-27. Every task
includes verified sources → tested adapters → staging/marts → geographic UI →
coverage matrix → aggregate reconciliation. A documented gap is a discovery
outcome, not implemented coverage.

- [~] **PS-TOPICS-01 — Air quality:** audit county monitor/pollutant coverage;
  integrate supported sources and distinguish absent monitors from clean air.
- [~] **PS-TOPICS-02 — Weather and water:** audit and integrate regional weather,
  river, tide, and snow stations; preserve station identity, units, datum/baseline,
  and comparable periods. Do not extrapolate a station across a county.
- [~] **PS-TOPICS-03 — Transit and ferries:** audit operators serving the region;
  integrate verified coverage at agency/mode grain without inventing county or
  route ridership allocations.
- [ ] **PS-TOPICS-04 — Permits:** integrate municipal/county feeds; distinguish
  applications from issued permits, preserve valuation definitions, deduplicate
  overlapping publishers, and retain multiple legitimate permits at an address.
- [ ] **PS-TOPICS-05 — Parks, trees, and art:** integrate available inventories,
  resolve overlapping publishers, and distinguish managed street-tree inventory
  from canopy coverage or all trees.
- [ ] **PS-TOPICS-06 — Inspections:** integrate health-jurisdiction feeds;
  preserve inspection event grain and differences between scoring systems.
- [ ] **PS-TOPICS-07 — Business and STR licenses:** integrate verified feeds with
  explicit jurisdiction/status rules; distinguish licenses from all operating
  businesses or rentals.
- [ ] **PS-TOPICS-08 — Crime, fire, and 311:** verify agency coverage; harmonize
  only comparable categories/periods, preserve incident/offense/dispatch/request
  grain, and use applicable local boundaries. Population rates require documented
  geographic/year-matched denominators.

### Group PS-RELEASE — Regional completion and operational validation

- [~] **PS-RELEASE-01** — Update overview, navigation, titles, geographic copy,
  README, source explanations, and generated docs to match actual coverage.
  Surface the coverage matrix and limitations in the app.
- [ ] **PS-RELEASE-02** — Audit every county/topic under the selected coverage
  policy; record implemented coverage, exclusions, and gaps. Verify regional
  totals and comparisons disclose actual geographic/time coverage.
- [ ] **PS-RELEASE-03** — Run quality gates and regional UX checks, including
  mobile, no-data states, map samples, Ask the Data, and Seattle regressions.
  Measure regional performance against PS-SCOPE-02 budgets.
- [ ] **PS-RELEASE-04** — Rehearse a clean Docker build and runtime, validate
  rollback to the prior image, and prepare a release PR with coverage/performance
  evidence for review.
- [ ] **PS-RELEASE-05** — After explicit owner approval, deploy to Railway,
  verify the live regional experience, and record scope and remaining gaps.


### Development checkpoint — 2026-09-27

- Confirmed scope is recorded in PRD §12 and DECISIONS.md.
- Source registry inventories 17 configured integrations across 15 topics;
  `docs/puget-sound-coverage.md` records all 150 county/topic statuses.
- Ten-county configuration and stable EPA monitor IDs are implemented.
- County selection is shared; Air Quality and Data Coverage support it. Other
  topics explicitly decline county filtering. City filters and geographic boundary
  dimensions remain unimplemented.
- Air queries apply selection before each aggregation; missing data and ozone-only
  coverage have explicit states. The new mart is documented for Ask the Data.
- Source retrieval timestamps, complete source contracts, benchmarks, broader
  source discovery, and other regional topic implementations remain open.
- Regional air rebuild completed: seven counties have observations; Island,
  Jefferson, and Mason are explicitly unavailable in this configured feed/window.
  98 tests and all 25 selected dbt model/test steps passed. Local query/build
  measurements are recorded in `docs/puget-sound-coverage.md`.
- Partial checkboxes above are not completion claims; city filters and the broader
  regional rollout remain open.

- Browser verification passed for Kitsap air summaries and its single-monitor map,
  Island no-data states, selection persistence, unsupported civic-topic guidance,
  the source inventory, and a 390×844 mobile layout. No deployment performed.
- Numeric production budgets, independent source reconciliation beyond synthetic
  fixtures, full Docker rehearsal, and end-to-end Ask the Data verification remain
  open; the slice exit gate is therefore only partially complete.


### Mobility continuation — 2026-09-27

- Foundations/air slice opened as PR #19. Continuation branch: `puget-sound-mobility`.
- Verified and integrated five additional FTA reporters: Kitsap, Skagit, Whatcom,
  Intercity, and Pierce County Ferry. Thirteen reporting agencies now load.
- Fixed ferry aggregation so new operators are not mislabeled as Water Taxi;
  retained service-type provenance in staging and added reporting coverage marts/UI.
- Island/Jefferson/Mason operators are absent from this monthly feed's inventory;
  alternate/annual source discovery remains open. County/route allocation is not
  inferred from agency totals. Full regional mobility coverage remains partial.
- Mobility checks: 102 pytest tests, Ruff, ty, 19 selected dbt steps, and a separate
  source-total reconciliation test passed. All three affected pages passed smoke
  checks; the expanded ferry chart was inspected in the browser. No deployment.


### Weather & water continuation — 2026-10-05

- Branch `puget-sound-weather-water`. Weather, river, tide, and snow now ingest every
  verified station region-wide (GHCN TMAX stations, USGS gages, NOAA tide gauges,
  NRCS SNOTEL) with county assignment and a per-county headline station; old
  Seattle-only marts replaced by `mart_{weather,river,tides,snow}_observations`.
- Uniform 2014-onward window for every weather station incl. Sea-Tac (see
  DECISIONS.md); all-time records now span 2014+ only.
- Honest absences: no USGS gage in Island/Kitsap, tide gauges only in the 5
  saltwater-front counties, no SNOTEL in Island/Kitsap/Thurston.
- Checks: 130 pytest tests, Ruff, ty, and `dbt build` (PASS=162, ERROR=0; 2 known
  crime warnings) passed on the existing warehouse. No full warehouse rebuild or
  Docker rehearsal on this branch. No deployment.

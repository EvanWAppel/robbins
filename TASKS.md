# Robbins — TASKS

Implementation task board for [`PRD.md`](./PRD.md). A near-exact port of **Elvis**
(Las Vegas) to the Seattle metro. Read [`PRIMER.md`](./PRIMER.md) first for the
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

## Suggested sequencing

- **Now:** VS (vertical slice, deployed) → SOCRATA/CONFIG/ETL alongside.
- **Then:** re-run interview §7.1, record outcomes, fan out Group TOPIC.
- **Finish:** Overview page, DEPLOY, docs.

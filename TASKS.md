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
- [ ] Seattle-specific extras: optional; revisit after the core set ships (candidates:
  311/Find-It-Fix-It, transit ridership, tree canopy, seismic zones).
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

- [ ] **SOCRATA-01** — Implement `fetch_socrata(domain, dataset_id, where=None,
  select=None, order=None)` with `$limit`/`$offset` paging until a short page. TDD.
- [ ] **SOCRATA-02** — Add a CSV-export path
  (`/api/views/{id}/rows.csv?accessType=DOWNLOAD`) for large datasets; ingest via
  DuckDB `read_csv_auto`. Use it for SPD crime. TDD the URL builder.
- [ ] **SOCRATA-03** — Support an optional `$$app_token` from `city_config.py`
  (raises throttling limits; anonymous still works). Log whether a token is in use.
- [ ] **SOCRATA-04** — A fetch returning zero rows raises (don't ship an empty page).

---

## Group CONFIG — City configuration

- [ ] **CONFIG-01** — Record in `city_config.py` the **Seattle Open Data** Socrata
  domain (`data.seattle.gov`) + dataset ids for kept topics.
- [ ] **CONFIG-02** — Record the **King County** Socrata (`data.kingcounty.gov`) +
  **King County / Seattle GeoData** ArcGIS roots and layer paths.
- [ ] **CONFIG-03** — Record **EPA AQS** FIPS: WA state `53`, King `033` (add Pierce
  `053`, Snohomish `061` if metro breadth = full metro).
- [ ] **CONFIG-04** — Record **NOAA GHCN-Daily** station: Sea-Tac `USW00024233`.
- [ ] **CONFIG-05** — Record the **SPD crime** dataset id + available date range.
- [ ] **CONFIG-06** — Record the chosen **signature water body** source (USGS NWIS
  site id, NOAA Tides station 9447130, or SPU/SNOTEL feed).

---

## Group ETL — Ingestion hardening

- [ ] **ETL-01** — Confirm the **force-IPv4 for `aqs.epa.gov`** path is carried over
  (see `PRIMER.md` §4). Test that the AQS fetch completes in the target env.
- [ ] **ETL-02** — Port the ArcGIS helpers for King County GIS; keep the per-host
  `ssl_verify=False` escape hatch (logged) for any broken-TLS server.
- [ ] **ETL-03** — Centralize encoding handling (Windows-1252 / cp1252) for any muni
  bulk files in `_read_delimited`. TDD with a fixture file.
- [ ] **ETL-04** — Ensure every fetch logs source, URL, and row count.

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
- [ ] **TOPIC-water** — Signature water body: USGS NWIS + NOAA tides 9447130 + SPU/SNOTEL (all 3).
- [ ] **TOPIC-tourism** — Tourism / Air Travel (Sea-Tac passengers + Visit Seattle). **No gaming.**
- [x] **TOPIC-art** — Public Art — **ArcGIS** (`PublicArt2`, 758 pts, 754 geocoded). ✅ 2nd pattern.
- [x] **TOPIC-marriage** — Marriage Licenses — **DROPPED** (no Seattle/KC open feed). Logged.
- [ ] **TOPIC-extras** — Deferred (311, transit, tree canopy, seismic) — revisit after core.
- [ ] **TOPIC-overview** — Overview page LAST: headline metrics from the marts that exist.

---

## Group DEPLOY — Ship & document

- [ ] **DEPLOY-01** — `.gitignore` the build artifacts: `*.duckdb`, `target/`,
  `logs/`, `.venv/`, `.env`, `.DS_Store`, `__pycache__/`.
- [ ] **DEPLOY-02** — Configure `prek` (ruff + ty) pre-commit; `uv run prek
  install`; confirm hooks fire.
- [ ] **DEPLOY-03** — GitHub Actions CI: pytest + ruff + ty on push/PR.
- [x] **DEPLOY-04** — Railway deploy live with all 8 shipped topics ✅ Project `robbins`
  on Evan's workspace; baked warehouse builds (43 models) and app serves at
  https://robbins-production.up.railway.app. Build ~ a few min (deps + full source
  fetch incl. ~6 min EPA AQS). Deployed from working dir via `railway up`.
- [ ] **DEPLOY-05** — Write `README.md`: what Robbins is, the ELT + dbt + Streamlit
  story with two-pattern (Socrata + ArcGIS) ingestion, local run steps, source list.
- [ ] **DEPLOY-06** *(optional, interview #8)* — Register in the portfolio
  orchestrator manifest and wire `robbins.evanappel.me`.

---

## Suggested sequencing

- **Now:** VS (vertical slice, deployed) → SOCRATA/CONFIG/ETL alongside.
- **Then:** re-run interview §7.1, record outcomes, fan out Group TOPIC.
- **Finish:** Overview page, DEPLOY, docs.

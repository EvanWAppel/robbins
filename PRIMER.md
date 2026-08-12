# Robbins — Handoff Primer

> **Purpose:** Everything a fresh repo (and a fresh Claude session) needs to build
> a Seattle-metro clone of **Elvis**, Evan's Las Vegas open-data explorer.
> **Owner:** Evan Appel · **Date:** 2026-08-11 · **Status:** Handoff v1
>
> Read this first, then work from [`PRD.md`](./PRD.md) and [`TASKS.md`](./TASKS.md).
> House rules live in [`CLAUDE.md`](./CLAUDE.md) and are non-negotiable.
> Sibling handoff: `groening` (Portland) ports the same architecture.

---

## 0. TL;DR

Build **Robbins**: an interactive, multi-page **Streamlit** app that ingests free
public datasets about the **Seattle, WA metro** (King County core; extend to
Pierce + Snohomish where easy) and presents them as maps, charts, and searchable
tables. It is a near-exact port of **Elvis** (Las Vegas). Same architecture, same
toolchain, same deploy target — **only the data sources and city-specific
configuration change.**

- **ELT:** `build_warehouse.py` fetches public data → raw tables in a DuckDB file →
  **dbt-duckdb** models it into `staging/` views and `marts/` tables.
- **App:** `streamlit_app.py` routes to `views/*.py` pages that query the marts
  through a cached `app_db.query()` helper.
- **Deploy:** a `Dockerfile` **bakes the warehouse at build time** (`build_warehouse.py`
  then `dbt build`), then runs Streamlit. Ships to **Railway**.
- **Codename:** `robbins` (a recognizable Seattle/Pacific-Northwest figure —
  analog to "Elvis" for Vegas). Bikeable; rename freely.

**The one big difference from Elvis/Groening:** Seattle's dominant open-data portal
is **Socrata** (`data.seattle.gov`, `data.kingcounty.gov`), not ArcGIS. Elvis was
mostly ArcGIS FeatureServers. So Robbins adds a **`fetch_socrata()`** helper (SODA
API) alongside Elvis's existing ArcGIS helpers, which King County GIS still needs.
See §3 and §4.

The identical-stack decision, the mirror-Elvis scope, and the broad Data/DE framing
carry over from the Groening interview (§7). Re-run the interview in §7.1 to close
Seattle-specific open questions before finalizing the page list.

---

## 1. The reference: what Elvis is

Elvis (`portfolio/elvis`) is a Streamlit app over a baked DuckDB warehouse. Its
shape is the blueprint you are copying:

```
elvis/
├── build_warehouse.py     # ETL orchestrator — fetches every source into raw.* DuckDB tables
├── streamlit_app.py       # multi-page router (st.Page + st.navigation)
├── app_db.py              # shared read-only DuckDB connection + @st.cache_data query()
├── dbt_project.yml        # dbt: staging=view, marts=table
├── profiles.yml           # dbt-duckdb profile, path -> vegas.duckdb
├── Dockerfile             # build: build_warehouse.py && dbt build ; run: streamlit
├── requirements.txt       # pip fallback used inside Docker
├── pyproject.toml / uv.lock
├── models/
│   ├── staging/           # ~15 stg_*.sql (raw -> light normalize) + sources.yml
│   └── marts/             # ~12 mart_*.sql (aggregations / viz-ready wide tables)
├── views/                 # 14 *.py Streamlit pages, one per topic
└── vegas.duckdb           # ~220 MB; NOT in git; rebuilt every deploy
```

**Data flow:** `build_warehouse.py` (build time) → `raw.*` tables → `dbt build`
→ `staging` views → `marts` tables → Streamlit reads marts at runtime.

**Elvis's 14 pages (the topic menu to mirror):** Overview, Public Art,
Restaurant Inspections, Fire Inspections, Metro (Police) Calls, Building Permits,
Business Licenses, Short-Term Rentals, Parks, Marriage Licenses, Tourism & Gaming,
Lake Mead (reservoir level), Desert Heat (weather extremes), Air Quality.

**Key fetch helpers in `build_warehouse.py` you will reuse:**

- `fetch_layer(service, org, layer, geometry, out_sr=4326)` — generic ArcGIS
  FeatureServer pagination. **King County GIS uses this.**
- `fetch_features(base_url, where="1=1", geometry, out_sr=4326, ssl_verify=True)`
  — flexible ArcGIS fetch; `ssl_verify=False` handles broken-TLS servers.
- `_centroid(geom)` — (lon, lat) from a point or polygon ring.
- `_epoch_to_date(ms)` — ArcGIS epoch-millis → ISO date.
- `_urlopen()` / `_read_delimited()` — HTTP + delimited-file parsing with encoding
  handling (Windows-1252 / cp1252).

**New helper Robbins must add — `fetch_socrata()`** (see §4). Most City-of-Seattle
and King County datasets are Socrata, reached via the SODA API.

**No secrets.** Everything is public data. City-specific config is hardcoded as
constants near the top of Elvis's `build_warehouse.py`. For Robbins, **lift those
into a `city_config.py` module** so the swap is a single file (see §5).

---

## 2. What stays identical (do not re-litigate)

The stack is **identical** to Elvis. Copy wholesale:

- **DuckDB** single-file warehouse; **dbt-duckdb** with `staging`=views, `marts`=tables.
- **Streamlit** multi-page (`st.Page()` + `st.navigation()`), **Altair** charts,
  **PyDeck** maps (hexbin for dense point data like police/fire calls).
- **`app_db.query()`** cached with `@st.cache_data(ttl=3600)` over a read-only
  DuckDB connection.
- **Dockerfile bakes the warehouse at build time.** The `.duckdb` file stays out of
  git and is rebuilt fresh on every deploy.
- **Railway** deploy from the `Dockerfile` — no Procfile, no `railway.toml`.
- **Toolchain:** `uv` only, `pytest` (TDD), `ruff`, `ty`, `prek`, `logging`, never
  wrap/hide errors, never push to `main`/`master`. (Full rules: `CLAUDE.md`.)

---

## 3. What changes: Vegas → Seattle source mapping

Each row is a topic; find the Seattle equivalent, confirm it's live, then wire it.
**Verify every source before coding** — these are strong leads from domain
knowledge, not guaranteed-current endpoints. Note the **portal** column: `Socrata`
means SODA API (`fetch_socrata`), `ArcGIS` means FeatureServer (`fetch_features`).

| Topic | Elvis source (Vegas) | Seattle lead | Portal | Notes / risk |
| --- | --- | --- | --- | --- |
| **City data portal** | ArcGIS `F1v0ufATbBQScMtY` (City of LV) | **Seattle Open Data** `data.seattle.gov` + **Seattle GeoData** (ArcGIS Hub) | Socrata + ArcGIS | Primary city source. Socrata for tabular, ArcGIS Hub for spatial. |
| **Regional GIS** | Henderson / Clark County ArcGIS | **King County GIS Open Data** (ArcGIS Hub) + `data.kingcounty.gov` (Socrata) | ArcGIS + Socrata | Regional/county layers (Pierce, Snohomish if metro breadth extends). |
| **Police calls / crime** | LVMPD ArcGIS, yearly layers | **SPD Crime Data: 2008-Present** (`data.seattle.gov`) | Socrata | Well-known dataset; large. Page/limit via SODA. |
| **Fire calls** | City of LV fire-prevention ArcGIS | **Seattle Fire 911 dispatch** (`data.seattle.gov`) | Socrata | Reframe from "fire inspections" → SFD 911 calls (which Seattle publishes). |
| **Restaurant inspections** | SNHD developer ZIP bundle | **Food Establishment Inspection Data** (Public Health – Seattle & King County, `data.kingcounty.gov`) | Socrata | Strong candidate; famous open dataset. |
| **Building permits** | City of LV permits ArcGIS | **Seattle DCI Building Permits** (`data.seattle.gov`) | Socrata | Strong candidate. |
| **Business licenses** | City of LV licenses ArcGIS | **City of Seattle Business License Tax Certificates** / WA DOR | Socrata | Verify current dataset + shape. |
| **Short-term rentals** | 3-jurisdiction ArcGIS | **Seattle Short-Term Rental licenses** | Socrata | Seattle licenses STRs; find the dataset. Verify. |
| **Parks** | Metro-wide ArcGIS + water join | **Seattle Parks & Recreation** boundaries (Seattle GeoData / ArcGIS) | ArcGIS | Strong; reuse water-feature flagging pattern. |
| **Marriage licenses** | Clark County CSVs | King County Recorder | ? | **High risk** — may not publish open CSVs → candidate to **drop**. |
| **Tourism & Gaming** | LVCVA XLSX (visitors, ADR, gaming) | **Port of Seattle (Sea-Tac) passenger volumes** + Visit Seattle | web/CSV | **No gaming** — reframe as "Tourism / Air Travel." |
| **Signature water body** | Lake Mead elevation (USBR RISE) | **Lake Washington / Cedar River (USGS NWIS)**, **Puget Sound tides (NOAA Tides & Currents, Seattle 9447130)**, or **Chester Morse reservoir / snowpack (NRCS SNOTEL)** | API | Pick one signature series — interview #4. Seattle's water story is snowpack/reservoir supply, not drought drawdown. |
| **Weather extremes** | NOAA GHCN-Daily, `USW00023169` | **NOAA GHCN-Daily, Sea-Tac `USW00024233`** | keyless | One-line station-code swap. Rename "Desert Heat" → e.g. "Rain & Records." |
| **Air quality** | EPA AQS bulk, NV `32` / Clark `003` | **EPA AQS bulk, WA `53` / King `033`** (optionally Pierce `053`, Snohomish `061`); Puget Sound Clean Air Agency | keyless | Same EPA bulk-file mechanism; change FIPS. |

**Net effect:** expect to keep ~9–12 pages, drop 1–2 (likely marriage), reframe 2
(fire→911 calls, tourism-no-gaming), and shift most ingestion from ArcGIS to
Socrata. Always **`log()` what you drop.** Final page list is a `TASKS.md`
deliverable, not a guess made here.

---

## 4. Known gotchas + the Socrata helper

**Carry over from Elvis (still apply):**

1. **EPA AQS needs forced IPv4.** `aqs.epa.gov` hangs over IPv6 in some
   environments (Railway included). Elvis forces IPv4 for that host — keep it.
2. **Broken-TLS GIS servers.** Pass `ssl_verify=False` **only** per-host for a
   server with a bad cert, and log loudly. Never disable it globally.
3. **Warehouse builds at Docker build time, not runtime.**
4. **The `.duckdb` file is large (~200 MB) and NOT in git** — a build artifact.
5. **Encodings** — muni bulk files are often Windows-1252 / cp1252.
6. **ArcGIS pagination + geometry** — reproject to WGS84 (`out_sr=4326`); compute
   centroids for polygon layers.

**New for Seattle — `fetch_socrata()`:**

Most City-of-Seattle and King County datasets live on Socrata and are read via the
**SODA API**: `https://{domain}/resource/{dataset_id}.json`. Add a helper that:

- Pages with `$limit` + `$offset` (default page 1000–50000; loop until a short page).
- Supports `$where`, `$select`, `$order`, and `$$app_token` (optional — anonymous
  works for modest volumes, but an app token raises throttling limits; if used,
  keep it in `city_config.py`, and remember this is the *one* place a token might
  appear — still not a real secret).
- Returns rows as dicts → load into a DuckDB `raw.*` table (DuckDB can also read a
  Socrata CSV export URL directly via `read_csv_auto` for big datasets).
- For large tables (SPD crime is millions of rows), prefer the CSV export endpoint
  `https://{domain}/api/views/{id}/rows.csv?accessType=DOWNLOAD` and let DuckDB
  ingest it, rather than paging JSON.

`fetch_socrata()` is the main net-new code vs. Elvis. Everything else is a port.

---

## 5. Adaptation plan (the port, step by step)

Do the **vertical slice first** (one topic, end to end, deployed) before breadth.
`TASKS.md` tracks the items; the shape is:

1. **Scaffold** the uv project (`uv init`; `uv add streamlit duckdb dbt-duckdb
   pandas pydeck altair openpyxl requests`; dev: `uv add --dev pytest ruff ty
   prek`). Copy Elvis's `app_db.py`, `dbt_project.yml`, `profiles.yml`,
   `Dockerfile`, `streamlit_app.py` skeleton; rename `vegas.duckdb` →
   `seattle.duckdb` and the dbt `name`/`profile` `elvis` → `robbins`.
2. **Create `city_config.py`** — all Seattle endpoints (Socrata domains + dataset
   ids, King County ArcGIS orgs), EPA AQS FIPS, NOAA station code, year ranges.
   This is the one file that encodes "which city."
3. **Add `fetch_socrata()`** to `build_warehouse.py` alongside the ported ArcGIS
   helpers. TDD it against a small dataset fixture.
4. **Vertical slice:** pick one easy Socrata source (**Building Permits** or
   **SPD Crime**) or one ArcGIS source (**Parks** via King County GIS). Fetch →
   one `stg_` view → one `mart_` table → one Streamlit page → run locally →
   deploy to Railway. Prove the whole pipe.
5. **Fan out per topic** (§3 table): for each, verify the source, add a fetch call
   (Socrata or ArcGIS), a staging view, a mart, and a page. TDD parser/transform
   logic with `pytest` fixtures in `conftest.py`. Drop topics with no source + log.
6. **Overview page last** — headline metrics from the marts that exist.
7. **Deploy** to Railway; confirm the baked warehouse builds and the app serves on
   `$PORT`.

---

## 6. Deliverables in this handoff

| File | What it is |
| --- | --- |
| [`PRIMER.md`](./PRIMER.md) | This document — the port plan for Seattle. |
| [`PRD.md`](./PRD.md) | Product requirements for Robbins (mirrors Elvis/Groening style). |
| [`TASKS.md`](./TASKS.md) | TDD task board: vertical slice first, then per-topic fan-out. |
| [`CLAUDE.md`](./CLAUDE.md) | House rules (verbatim) + Robbins-specific build/repo notes. |

Drop these four files into the new repo's root. The `.duckdb`, `target/`, `logs/`,
`.venv/`, `__pycache__/` all belong in `.gitignore`.

---

## 7. The interview (unified understanding)

These decisions carry over from the Groening (Portland) interview with Evan on
2026-08-11 and apply to Robbins unless Evan changes them:

| Question | Decision |
| --- | --- |
| **Target metro** | **Seattle / King County** (core; extend to Pierce + Snohomish where easy). |
| **Tech stack fidelity** | **Identical to Elvis** — DuckDB + dbt-duckdb + Streamlit + PyDeck/Altair, Docker→Railway, warehouse baked at build time (plus a `fetch_socrata()` helper). |
| **Dataset scope** | **Mirror Elvis where data exists** — same ~14 topics, drop what Seattle lacks, add Seattle-specific extras. |
| **Portfolio framing** | **Broader Data / Data-Engineering role** — emphasize end-to-end ELT, multi-source ingestion (Socrata + ArcGIS), reproducible warehouse. |
| **Codename** | `robbins` (bikeable). |

### 7.1 Re-runnable interview protocol (for the receiving repo)

When the receiving Claude session starts, **re-run this short interview with Evan
to close Seattle-specific open questions** before committing the page list:

1. **Codename** — keep `robbins`, or pick another recognizable Seattle figure?
2. **Metro breadth** — King County only, or include Pierce + Snohomish (and cities:
   Tacoma, Bellevue, Everett)? Affects GIS orgs + AQS FIPS list.
3. **Drop list** — confirm dropping topics with no Seattle open feed (leading
   candidate: **Marriage Licenses**). Any worth extra sourcing effort?
4. **Signature water body** — Seattle's water story is supply, not drawdown. Which
   anchor: Lake Washington/Cedar River (USGS NWIS), Puget Sound tides (NOAA Tides &
   Currents), or reservoir/snowpack (SPU / NRCS SNOTEL)?
5. **Fire reframe** — confirm SFD 911 dispatch calls as the "fire" page (vs.
   inspections, which Seattle may not publish).
6. **Tourism reframe** — Port of Seattle (Sea-Tac) passenger volumes as the anchor,
   plus Visit Seattle stats? (Gaming dropped.)
7. **Seattle-specific extras** — anything Seattle publishes worth adding (e.g. 911
   response times, transit ridership / ORCA, bike counts, tree canopy, seismic /
   liquefaction zones, 311/Find-It-Fix-It requests)?
8. **Deploy target** — standalone Railway, or under the portfolio orchestrator +
   `robbins.evanappel.me`?

Record the answers in an "Interview outcomes" block at the top of `TASKS.md`. Don't
start coding pages until #2, #3, and #4 are answered — they change the source list.

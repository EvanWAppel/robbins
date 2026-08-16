# Robbins — PRD

> **Status:** Shipped — live on Railway · **Owner:** Evan Appel · **Date:** 2026-08-11
> (updated 2026-08-16)
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

1. **One explorer for Seattle-metro public data** — maps, charts, and searchable
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
- **Not exhaustive.** Mirror Elvis's topics where Seattle publishes them; drop the
  rest rather than forcing thin or unreliable sources.

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
| D3 | **Target Seattle / King County metro.** | Rich open-data ecosystem (Seattle Open Data, King County GIS, Public Health). |
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

## 11. Open questions

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

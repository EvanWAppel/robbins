# Robbins — Seattle-Metro Open-Data Explorer

**Robbins** is an interactive, multi-page [Streamlit](https://streamlit.io) app
that explores free public datasets about the **Seattle metro** (King County core,
extending to Pierce & Snohomish) — maps, trends, and searchable tables in one place.

It's a portfolio piece demonstrating end-to-end data engineering: multi-source
ingestion across **two access patterns** (Socrata SODA + ArcGIS FeatureServer), a
reproducible DuckDB warehouse, dbt modeling, and an interactive front end. It is a
near-exact port of Elvis (Las Vegas) — same stack, different city.

## Stack

- **DuckDB** — single-file embedded warehouse (no server).
- **dbt-duckdb** — SQL modeling: `staging/` views normalize raw sources,
  `marts/` tables aggregate and denormalize for the app.
- **Streamlit** + **Altair** (charts) + **PyDeck** (maps).
- **uv** for Python; **Docker** → **Railway** for deploy.

## How it works

```
build_warehouse.py   # fetch every public source -> raw.* tables in seattle.duckdb
        │            #   Socrata (SODA API) for city/county tabular data
        │            #   ArcGIS FeatureServers for King County GIS spatial layers
     dbt build       # raw -> staging views -> marts tables
        │
streamlit_app.py     # views/*.py pages query marts via cached app_db.query()
```

The DuckDB warehouse is **baked at Docker build time** (`build_warehouse.py` then
`dbt build`), so the running container serves a ready warehouse. The `.duckdb` file
is a git-ignored build artifact, rebuilt fresh on every deploy.

The one net-new piece versus Elvis is **`fetch_socrata()`** — Seattle's dominant
open-data portal is Socrata (`data.seattle.gov`, `data.kingcounty.gov`), reached via
the SODA API. All Seattle-specific configuration lives in **`city_config.py`**.

## Run it locally

```sh
uv sync
uv run python build_warehouse.py            # fetch sources -> raw.* tables
uv run dbt build --profiles-dir .           # raw -> staging -> marts
uv run streamlit run streamlit_app.py       # serve on :8501
```

Quality gates:

```sh
uv run pytest          # TDD for parsers/transforms (fetch_socrata et al.)
uv run ruff check .
uv run ty check
```

## Data sources

Public, no secrets. A Socrata app token is optional (raises rate limits only).
Current pages and the full topic inventory live in [`TASKS.md`](./TASKS.md); the
Vegas→Seattle source mapping and known gotchas are in [`PRIMER.md`](./PRIMER.md).

| Page | Source | Portal |
| --- | --- | --- |
| Building Permits | Seattle DCI Building Permits (`76t5-zqzr`) | Socrata |
| _…more topics fanning out — see TASKS.md_ | | |

## Deploy

Railway, from the `Dockerfile` (no Procfile, no `railway.toml`). The build stage
runs `build_warehouse.py && dbt build --profiles-dir .` to bake the warehouse into
the image; the runtime serves Streamlit on `$PORT`.

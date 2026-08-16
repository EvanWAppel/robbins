prime directive: don't do anything you're unclear about, ask me about it.
use uv
run python tools with uv run python
do not edit pyproject.toml dependencies directly
use uv add LIB or uv add --dev LIB
use pytest to implement tdd
use pytest fixtures in conftest.py to DRY
use ruff to lint
use ty to typecheck
use prek for precommits
use logging to help ai debug
do not hide or wrap errors.
Do not push to master or main

# Robbins — project notes

Robbins is a Seattle-metro open-data explorer: a near-exact port of the Elvis
(Las Vegas) app. Read PRIMER.md first, then PRD.md and TASKS.md.

## Architecture (identical to Elvis — do not redesign)
- ELT: `build_warehouse.py` fetches public data into `raw.*` tables in a single
  DuckDB file, then `dbt build` (dbt-duckdb) models `staging/` views and `marts/`
  tables. Streamlit pages read the marts.
- App: `streamlit_app.py` (st.Page + st.navigation) routes to `views/*.py`; each
  page queries via the cached `app_db.query()` helper (@st.cache_data).
- Charts: Altair. Maps: PyDeck (hexbin for dense point layers like crime/911).

## The one net-new piece vs. Elvis: Socrata
- Seattle's city + county data is mostly on Socrata (`data.seattle.gov`,
  `data.kingcounty.gov`), reached via the SODA API. Add `fetch_socrata(domain,
  dataset_id, ...)` that pages with $limit/$offset. King County GIS is ArcGIS, so
  keep Elvis's `fetch_features`/`fetch_layer` too.
- For large datasets (SPD crime = millions of rows), use the CSV export endpoint
  `/api/views/{id}/rows.csv?accessType=DOWNLOAD` and let DuckDB ingest it, rather
  than paging JSON.
- A Socrata app token is OPTIONAL (raises rate limits); anonymous works. If used,
  it lives in `city_config.py` and is not a protected secret.

## City config
- ALL Seattle-specific values (Socrata domains + dataset ids, ArcGIS orgs, EPA AQS
  state/county FIPS, NOAA station code, source URLs, year ranges) live in
  `city_config.py`. `build_warehouse.py` imports from it.

## Build & deploy
- The DuckDB warehouse is baked at DOCKER BUILD TIME (`build_warehouse.py &&
  dbt build --profiles-dir .`), never at runtime. Railway's release phase is a
  throwaway container.
- The `*.duckdb` file is a build artifact — git-ignore it; rebuilt on every deploy.
  Also ignore `target/`, `logs/`, `.venv/`, `__pycache__/`.
- Deploy to Railway from the Dockerfile (no Procfile, no railway.toml). Runtime
  serves Streamlit on `$PORT` (default 8501 locally).

## Known gotchas (carry over from Elvis)
- Force IPv4 for `aqs.epa.gov` — it hangs over IPv6 in some environments
  (Railway included). Air quality uses keyless EPA bulk files.
- Some municipal ArcGIS servers ship broken TLS certs; pass `ssl_verify=False`
  ONLY for the specific offending host, and log a warning when you do. Never
  disable verification globally.
- Muni bulk files are often Windows-1252 / cp1252, not UTF-8.
- Reproject ArcGIS geometry to WGS84 (out_sr=4326) at fetch time; compute
  centroids for polygon layers so PyDeck maps just work.

## Data discipline
- Verify every source is live and machine-readable before wiring it. The primer's
  Seattle leads are starting points, not guarantees.
- A fetch that returns zero rows should raise, not silently ship an empty page.
- Drop any topic Seattle doesn't publish — and `log()` the drop so it's visible.

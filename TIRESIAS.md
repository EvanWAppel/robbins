# Tiresias

The "Ask Tiresias" page is a grounded text-to-SQL agent over the Seattle-metro marts.
It replaces the earlier "Ask the Data" page (`nl_sql.py` / `sql_safety.py` /
`catalog.py`), adding a code-level table allowlist, map-only column hiding, a row cap,
a statement timeout, retrieval grounding, abstention, and abuse caps. Engine:
https://github.com/EvanWAppel/tiresias (pinned in `pyproject.toml` / `requirements.txt`).
Robbins keeps only its city config:

- `tiresias.yml`: allowed tables, map-only columns, examples, planner notes
  (including the old page's geography caveats), grounding threshold, limits.
- `tiresias_metrics.yml`: Tiresias metric registry (empty; `metrics.yml` still
  drives the `mart_metrics` headline totals, which Tiresias can query).
- `evals/tiresias_gold.yaml`, `evals/tiresias_retrieval_gold.yaml`: gold sets.

```
uv run tiresias check                    # config vs dbt artifacts
uv run tiresias eval --retrieval-only    # recall@k, no key needed
uv run --env-file .env tiresias eval     # + live gold set (needs a dedicated key)
uv run tiresias calibrate                # pick the grounding threshold
```

The page needs `ANTHROPIC_API_KEY` from a dedicated, spend-capped workspace key;
without it the page shows a notice and stops.

## Column-doc claims to check against the data

Docs for the 11 previously undocumented columns, the sharpened descriptions, and
the 26 regional-mart columns were written from code. To check:

1. `mart_*_by_neighborhood.precinct`: passed through raw from ArcGIS; value set
   (N/S/E/W/SW?) and nulls unverified. Check distinct values.
2. `hour_of_day` (crime, fire): no timezone conversion in code; confirm the source
   publishes local time.
3. License "active": no status filter in code; relies on dataset wnbq-64tb being
   active certificates only. Check the dataset's metadata.
4. Tide `mhhw_ft`, `mllw_ft`, `highest_ft`, `lowest_ft`: described as relative to
   the station's MSL datum (the request uses `datum=MSL`). Check one month against
   NOAA's page.
5. `mart_weather_observations.snow_in` / `snow_depth_in`: null where a station
   doesn't report snow. Check null share by station.

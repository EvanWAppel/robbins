# Review — Ask Tiresias page (PR #23)

Fresh-context adversarial reviewer, 2026-10-05. **No HIGH findings.** Removal of the
old text-to-SQL confirmed clean; deploy path resolves (pip, py3.12); hostile SQL
(file readers, metadata/query functions, every `rings_json` route) rejected; schema
tests and model entries unchanged vs main; pytest, ruff, ty, `tiresias check`,
recall@3 = 1.00 all green.

| # | Sev | Finding | Disposition |
|---|-----|---------|-------------|
| 1 | MED | "King headline is Sea-Tac" likely false (headline = most years since 2014, ties to lowest id), so "Sea-Tac rain" could sum another station | **Fixed**: docs + example + planner note name `station_id = 'USW00024233'`; headline check added to `TIRESIAS.md` for Evan |
| 2 | LOW | `precip_in` had no missing-day warning | **Fixed** |
| 3 | LOW | Air rows are site × day × pollutant; "count days" could overcount | **Fixed**: example + planner note say count distinct `obs_date` |
| 4 | LOW | README local run omitted `dbt docs generate` | **Fixed** |
| 5 | LOW | Stale "Ask the Data" prose in PRD/TASKS/primer | Accepted (history) |
| 6 | LOW | Embedding model downloads on first question after deploy | Open: same as Elvis; consider baking it into the image later |
| 7 | LOW | CI skips artifact tests (no catalog in CI) | Accepted; fails safe (unclassified marts are not queryable) |
| 8 | LOW | Public dbt docs site not regenerated since 2026-08-19 | Pre-existing; out of scope |

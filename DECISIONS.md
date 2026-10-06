# DECISIONS — the Ledger

The durable *why*. One entry per decision with a **real trade-off** — what was chosen, what was rejected, and why. Append-only; newest at the bottom. The agent drafts the entry; the human confirms it.

---

## 2026-09-26 — Reskin the editorial atlas from PNW-forest to Maritime / Puget Sound

**Context.** The `design/seattle-city-atlas` branch already had an editorial-atlas
design in an earthy PNW palette (evergreen `#496e58` on oat `#f7f5ed`, gold/olive
accents). Asked to make it feel more "for the Seattle crowd," we chose to iterate on
that structure rather than rebuild it, and to shift the skin toward a **Maritime /
Puget Sound** direction (deep blues, slate, one warm brass accent).

**Chosen — "Balanced Sound" palette, applied as a hex-for-hex remap.**
- Ink `#123141` · primary `#2f6285` (Sound blue) · paper `#f2f5f6` (sea fog) ·
  brass accent `#c1913f` · harbor sky `#4f88a6` · harbor teal `#3f7d86` · sea mist
  `#8fb3b5` · buoy-red alert `#b4503f`.
- Chart categorical list → `[#2f6285, #c1913f, #4f88a6, #b4503f, #3f7d86, #8fb3b5]`.
- Applied via a single-pass, dict-based substitution across `.streamlit/config.toml`,
  `assets/atlas.css`, and all 18 views; three non-hex PyDeck map colors (parks,
  public art, short-term rentals) updated by hand.
- `landscape.svg` redrawn from a mountain-forest engraving to a Puget Sound
  ferry-and-water scene in the new palette, keeping the same frame/ticks/labels.

**Rejected.**
- *"Deep harbor" and "Morning fog" moods* — moodier/darker and airier/lighter
  variants. Balanced Sound keeps contrast closest to the current design, lowest risk.
- *Recoloring the semantic scales* — AQI's standard green→maroon and the crime/fire
  red heatmaps were left untouched so they keep their public meaning; only decorative
  and categorical colors moved. The trees canopy sequential (green) was likewise kept
  as a meaningful density scale.
- *A full IA/copy rewrite* — out of scope; this was theme + overview + all pages only.

**Why it's safe.** The remap targets only the specific old-palette hexes, which don't
collide with the AQI or canopy colors, so those survived automatically. All views
byte-compile and `ruff` passes.

## 2026-09-26 — Replace 3D hexbin maps with MCPP neighborhood choropleths

**Context.** The Crime, Fire 911, and 311 pages each showed a 3D extruded-hexagon
PyDeck map over a ~12k point sample. Feedback: hard to read, and the towers don't
convey *where* incidents concentrate. Chose to replace all three with neighborhood
choropleths shaded by **per-square-mile density**.

**Chosen.**
- **Geography = SPD MCPP neighborhoods** (ArcGIS `MCPP` FeatureServer, 58 polygons).
  Crime is already tagged with these names; verified live before wiring (58 polygons,
  `neighborhood`/`precinct`/`Shape__Area` fields).
- **Assignment = point-in-polygon for all three**, uniformly, via the DuckDB
  `spatial` extension (`ST_Contains`) with a bounding-box prefilter, rather than a
  name-join for crime + spatial for the others. Uniform method, no dependence on
  name-string matching. Coverage came out 99.4–99.7% (unassigned ≈ points over water).
- **Shading = per-area density** (incidents ÷ area sq mi), colored by **rank/quantile**
  so the skewed distribution spreads across the ramp instead of one dark blob.
- **Geometry handling**: store each polygon as a GeoJSON MultiPolygon with every ring
  as its own polygon (no hole modeling) — robust to winding/multipart, over-covers the
  rare hole. Good enough for a density map; MCPP turned out to be single-ring anyway.

**Rejected.**
- *Density heatmap / flat hexbins* — lower lift but answer "hot spots," not "which
  neighborhood." *Raw counts* and *quantile-binned raw counts* — rejected in favor of
  per-area density so large neighborhoods don't dominate purely by size.
- *Name-join for crime* — avoided to keep one uniform method and dodge name-mismatch bugs.
- *shapely/geopandas PIP in Python* — DuckDB `spatial` keeps it in the warehouse layer,
  no heavy new Python dep, and the bbox prefilter makes it run in ~5s per dataset.

**Cost.** New `spatial` extension in the dbt profile; three new marts + a `raw.mcpp`
fetch. Build-time impact negligible (~5s/mart). The old `mart_*_map_sample` marts are
now unused by the views (left in place; candidate for later cleanup).

## 2026-09-26 — Replace remaining hex columns with top-down dots

Following the user's approval of flat maps, Trees and Building Permits now use
small translucent dots over the labeled light basemap. Tree hovers show species
and condition; permit hovers show address, type, number, and issue date. Existing
sample limits remain explicit in captions.

Dots preserve individual locations and hover details; a permit heatmap would
emphasize concentrations but lose individual inspection. Overlapping permits can
hide one another, so the caption calls this out. Crime, Fire 911, and 311 keep
their existing neighborhood density maps.


## 2026-09-27 — Ten-county Puget Sound expansion

The owner confirmed King, Pierce, Snohomish, Kitsap, Island, Skagit, Thurston,
Mason, Jefferson, and Whatcom; one regional explorer with county/city filters;
clearly labeled partial coverage; and environment/mobility first. Partial
coverage permits useful releases while sources are verified, at the cost of
requiring explicit gaps and comparison limitations on every topic. Air quality
is the first implementation slice because the existing EPA feed carries county
codes. Separate city/county page trees and all-counties-before-launch gating
were not selected.


## 2026-09-27 — Expand mobility at agency grain

Use the existing verified FTA monthly feed for five additional regional reporters,
with explicit agency reporting windows. Preserve separate ferry operators and map
only the two known King County reporting names to Water Taxi. Retain source service
type in staging. Do not assign agency-wide totals to counties or join annual-only
series into monthly charts; alternate sources for monthly-feed gaps remain work
to verify separately. This implements the approved partial-coverage policy.


## 2026-09-27 — Regional Weather & Water: all stations, curated headline, four networks

The owner chose to expand Weather & Water (PS-TOPICS-02) across all four keyless
federal networks already wired for Seattle — GHCN-Daily weather, USGS NWIS
streamflow, NOAA CO-OPS tides, NRCS SNOTEL snow — ingesting every station for map
density and honest per-county coverage counts, while designating one curated
"headline" station per county per network for the KPI/charts. Verified 2026-09-27
coverage: river gages in 8/10 counties (Island, Kitsap none); tide gauges in the 5
saltwater-front counties (Jefferson, King, Kitsap, Pierce, Whatcom); SNOTEL snow in
7/10 (Island, Kitsap, Thurston none); weather in all 10.

Interpretation adopted for build cost: weather "all stations" means the ~142
TMAX-reporting GHCN stations in the region bbox (discovery filters on the single
TMAX element), NOT the 554-station set that includes precip-only volunteer gauges —
the latter add map noise without the temperature story and multiply build-time CSV
downloads. Every weather station (including the Sea-Tac King headline) is clipped to
a uniform 2014-onward window for a lean build — chosen 2026-09-27 over preserving
Sea-Tac's full 1948+ record; the all-time-records feature now spans 2014+ only.
River, tide, and snow ingest every verified station (pullable by county in a few calls).

Chosen over: one-curated-station-per-county (leaner but loses the density map and
honest station counts) and all-stations-no-curation (noisy charts, implies
county-wide coverage the PRD forbids). Cost: ~142 GHCN per-station CSV downloads add
a few minutes to the build; per-county gaps must be shown explicitly (no station is
extrapolated across a county); station identity, units, and datum/baseline are
preserved per the PRD.

## 2026-10-05 — Replace "Ask the Data" with Tiresias (drafted by Claude; replacement confirmed by Evan 2026-10-04)

Evan chose to replace the in-repo text-to-SQL (`nl_sql.py`, `sql_safety.py`,
`catalog.py`, `generate_catalog.py`, `catalog/marts.json`) with the Tiresias
library (v0.1.0, pinned by the tag's commit archive); `semantic.py`, `metrics.yml`
and `mart_metrics` stay (the overview reads them). The old page enforced table
scope only in the prompt; Tiresias enforces an explicit allowlist in code. Scope:
57 of 60 marts; **excluded** the two map samples (silent undercounts) and
`mart_build_info`; neighborhood `rings_json` and approximate centroids are map-only.
`mart_metrics` stays queryable (headline totals). The old prompt's geography
caveats became planner notes. Threshold **0.63**, midway between the generic
off-topic band and the lowest answerable question (rejected: 0.66+, within ~0.04 of
a real question). Tiresias metric registry starts empty (rejected: reshaping
`metrics.yml`, which also drives a dbt model). `anthropic` is no longer a direct
dependency; `requires-python` narrowed to 3.12.

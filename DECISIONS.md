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

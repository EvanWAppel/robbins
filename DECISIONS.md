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

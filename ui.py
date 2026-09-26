"""Shared visual language for the Robbins city atlas."""
import json
from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).parent

# Maritime sequential ramp for the choropleths: pale sea fog -> deep Sound navy.
_RAMP = [
    (207, 224, 230),
    (143, 179, 181),
    (79, 136, 166),
    (47, 98, 133),
    (18, 49, 65),
]


def apply_theme():
    """Load the same design system on every page."""
    st.html(f"<style>{(ROOT / 'assets' / 'atlas.css').read_text()}</style>")


def landscape():
    """An original, decorative Puget Sound engraving."""
    return (ROOT / 'assets' / 'landscape.svg').read_text()


def ramp_color(t: float) -> list[int]:
    """Interpolate the maritime ramp; ``t`` in [0, 1] -> [r, g, b]."""
    t = max(0.0, min(1.0, t))
    span = len(_RAMP) - 1
    i = min(int(t * span), span - 1)
    local = t * span - i
    a, b = _RAMP[i], _RAMP[i + 1]
    return [round(a[k] + (b[k] - a[k]) * local) for k in range(3)]


def neighborhood_choropleth(
    df: pd.DataFrame,
    *,
    value_col: str = "incidents_per_sq_mile",
    count_col: str = "incident_count",
    unit: str = "per sq mi",
) -> pdk.Deck:
    """A PyDeck polygon choropleth of MCPP neighborhoods shaded by ``value_col``.

    Color is assigned by RANK (quantile position), not raw value, so the skewed
    density distribution spreads evenly across the ramp instead of collapsing to
    one dark neighborhood. Each polygon ring becomes its own record so multipart
    neighborhoods render correctly.
    """
    ranked = df.sort_values(value_col).reset_index(drop=True)
    denom = max(len(ranked) - 1, 1)
    records: list[dict] = []
    for rank, (_, row) in enumerate(ranked.iterrows()):
        color = ramp_color(rank / denom) + [205]
        for ring in json.loads(row["rings_json"]):
            records.append(
                {
                    "polygon": ring,
                    "neighborhood": str(row["neighborhood"]).title(),
                    "count": f"{int(row[count_col]):,}",
                    "density": f"{float(row[value_col]):,.0f}",
                    "fill_color": color,
                }
            )
    layer = pdk.Layer(
        "PolygonLayer",
        records,
        get_polygon="polygon",
        get_fill_color="fill_color",
        get_line_color=[247, 250, 250, 130],
        line_width_min_pixels=1,
        pickable=True,
        auto_highlight=True,
        stroked=True,
        filled=True,
    )
    return pdk.Deck(
        layers=[layer],
        initial_view_state=pdk.ViewState(latitude=47.62, longitude=-122.33, zoom=10.2),
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        tooltip={
            "html": f"<b>{{neighborhood}}</b><br/>{{count}} total<br/>{{density}} {unit}",
            "style": {"backgroundColor": "#123141", "color": "#f2f5f6"},
        },
    )


def choropleth_legend(df: pd.DataFrame, unit: str, value_col: str = "incidents_per_sq_mile") -> str:
    """A small gradient legend (low -> high) with the observed value range."""
    lo, hi = float(df[value_col].min()), float(df[value_col].max())
    stops = ", ".join(f"rgb{tuple(ramp_color(i / 4))}" for i in range(5))
    return (
        '<div style="display:flex;align-items:center;gap:.6rem;font-size:.68rem;'
        'color:var(--muted);margin:.1rem 0 .3rem">'
        f'<span>{lo:,.0f}</span>'
        f'<span style="flex:0 0 180px;height:10px;border-radius:2px;'
        f'background:linear-gradient(90deg,{stops})"></span>'
        f'<span>{hi:,.0f}</span>'
        f'<span style="margin-left:.3rem">{unit}</span></div>'
    )

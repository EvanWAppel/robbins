"""An editorial index into Seattle's public data, using warehouse metrics."""
from html import escape

import streamlit as st

from app_db import query
from ui import landscape

_build = query("select built_at, total_records from main.mart_build_info").iloc[0]
_metrics = query("select metric_name, value from main.mart_metrics")
_metric_values = dict(zip(_metrics["metric_name"], _metrics["value"], strict=True))


def metric(name: str) -> float:
    """Read headline values from the shared semantic layer."""
    return _metric_values[name]


st.html('<div class="masthead"><strong>Seattle metropolitan area</strong><span>An open-data field guide &nbsp; / &nbsp; No. 01</span></div>')
st.html(f'''
<section class="hero">
  <div>
    <div class="eyebrow">Local perspective. Public knowledge.</div>
    <h1>A city, seen<br>through <em>data.</em></h1>
    <p>From the trees on your street to the ferries on the Sound.
    Explore the patterns, places, and everyday rhythms that make Seattle, Seattle.</p>
    <a href="#explore">Explore the atlas &nbsp; ↗</a>
  </div>
  <div class="hero-art">{landscape()}
    <div class="art-caption"><span>47.6062° N &nbsp; 122.3321° W</span><span>LAND · WATER · CITY</span></div>
  </div>
</section>
<div class="facts">
  <div class="fact"><div class="fact-value">{int(_build['total_records']) / 1e6:.1f}M</div><div class="fact-label">Public records to explore</div></div>
  <div class="fact"><div class="fact-value">15</div><div class="fact-label">Ways to see the city</div></div>
  <div class="fact"><div class="fact-value">3</div><div class="fact-label">Counties in the metro</div></div>
  <div class="fact"><div class="fact-value fact-date">{_build['built_at']:%b %d, %Y}</div><div class="fact-label">Warehouse last refreshed</div></div>
</div>
<div id="explore" class="section-heading"><h2>Follow your curiosity.</h2><span>Six collections. One connected city.</span></div>
''')

collections = [
    ("01", "City & housing", "A city in the making. Follow construction, commerce, and the places we stay.",
     f"{int(metric('total_permits')):,}", "building permits", [
         ("building_permits", "Building Permits"), ("business_licenses", "Business Licenses"),
         ("short_term_rentals", "Short-Term Rentals")]),
    ("02", "Public safety", "The calls, reports, and everyday requests that keep a city moving.",
     f"{metric('total_311_requests') / 1e6:.2f}M", "311 requests", [
         ("crime", "Crime"), ("fire_911", "Fire 911 Calls"), ("csr_311", "311 Requests")]),
    ("03", "Getting around", "Across the neighborhood or across the Sound. A region, in motion.",
     f"{metric('total_ferry_boardings') / 1e6:.0f}M", "ferry boardings", [
         ("transit", "Transit Ridership"), ("ferry", "Ferry Ridership")]),
    ("04", "Health & food", "Behind every neighborhood favorite, a public record of food safety.",
     f"{int(metric('total_inspections')):,}", "food inspections", [
         ("restaurants", "Restaurant Inspections")]),
    ("05", "The living landscape", "The green spaces and creative places that give Seattle its character.",
     f"{int(metric('total_street_trees')):,}", "street trees", [
         ("parks", "Parks"), ("trees", "Street Trees"), ("public_art", "Public Art")]),
    ("06", "Air, rain & water", "Beyond the forecast. Read the long story of our changing environment.",
     f"{metric('pct_good_or_moderate_air_days'):.0f}%", "Good or Moderate air days", [
         ("weather", "Rain & Records"), ("air_quality", "Air Quality"), ("water", "Water")]),
]

for offset in range(0, len(collections), 3):
    columns = st.columns(3, gap="medium")
    for column, (number, title, description, value, label, links) in zip(
        columns, collections[offset:offset + 3], strict=True
    ):
        with column, st.container(border=True, key=f"collection_{number}"):
            st.html(f'''<div class="collection">
                <div class="collection-index"><span>FIELD NOTES / {number}</span><span>↗</span></div>
                <h3>{escape(title)}</h3><p>{escape(description)}</p>
                <div class="collection-stat">{escape(value)}<small>{escape(label)}</small></div>
                </div>''')
            for slug, title in links:
                st.page_link(f"views/{slug}.py", label=f"{title}  →")

st.caption("Headline figures reflect each source’s loaded reporting window. Open a topic for dates, definitions, and detail.")
st.html('<div class="invitation"><h3>Every good discovery starts with a question.</h3><p>Browse the data catalog, or ask a question in your own words.</p></div>')
st.page_link("views/ask.py", label="Ask the data  ↗")
st.html('''<footer class="atlas-footer"><span>ROBBINS &nbsp; / &nbsp; Public data. A shared perspective.</span>
<span>Socrata · ArcGIS · Federal sources &nbsp; / &nbsp; <a href="https://evanwappel.github.io/robbins/" target="_blank" rel="noopener noreferrer">Sources & methodology ↗</a></span></footer>''')

"""Ask the Data — a natural-language query surface over the marts.

Two things in one page:
  1. A machine-readable **catalog** of the marts (``catalog/marts.json``), framed as
     the context an AI agent grounds on — the same file a coding agent could load.
  2. An optional **"Ask the data"** box: your question → a read-only DuckDB SELECT
     (Claude, grounded on the catalog) → results. The generated SQL is shown, the
     query is validated read-only before it runs, and errors are surfaced, not hidden.

This is a personal, applied-AI feature. It uses your own ``ANTHROPIC_API_KEY`` and no
employer system; without a key set, the catalog still renders and the query box
explains how to enable it.
"""

import json
import os
from pathlib import Path

import streamlit as st

from app_db import query
from catalog import catalog_prompt_text
from nl_sql import generate_sql
from sql_safety import assert_read_only

CATALOG_PATH = Path(__file__).parent.parent / "catalog" / "marts.json"

st.title("🤖 Ask the Data")
st.markdown(
    "A natural-language query surface over the modeled marts. The **catalog** below is "
    "machine-readable context an AI agent can ground on; the **Ask** box turns a "
    "question into a read-only DuckDB query over it."
)

catalog = json.loads(CATALOG_PATH.read_text())

with st.expander(f"📚 Marts catalog — {len(catalog['tables'])} tables an agent can ground on"):
    st.caption("Generated from the dbt model docs (`catalog/marts.json`).")
    for table in catalog["tables"]:
        st.markdown(f"**`main.{table['name']}`** — {table['description']}")
        st.caption(", ".join(c["name"] for c in table["columns"]))

st.divider()
st.subheader("Ask a question")

if not os.environ.get("ANTHROPIC_API_KEY"):
    st.info(
        "Set an **`ANTHROPIC_API_KEY`** environment variable to enable natural-language "
        "queries (Claude generates a read-only SQL query grounded on the catalog above). "
        "The catalog is fully browsable without a key."
    )
else:
    question = st.text_input(
        "Your question",
        placeholder="e.g. Which month had the most 311 requests?",
    )
    if question:
        with st.spinner("Generating a read-only query…"):
            result = generate_sql(question, catalog_prompt_text(catalog))
        sql = assert_read_only(result["sql"])  # raises loudly if not read-only
        st.caption(result.get("rationale", ""))
        st.code(sql, language="sql")
        # Let a bad query fail loud rather than swallow the DuckDB error.
        st.dataframe(query(sql), use_container_width=True)

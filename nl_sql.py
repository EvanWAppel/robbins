"""Natural-language → read-only DuckDB SQL over the marts, grounded on the catalog.

The 'Ask the data' tab passes a question plus the marts catalog to Claude, which
returns a single read-only SELECT via a forced tool call. The SQL is then validated
by ``sql_safety`` and run against the read-only warehouse. This module holds the
provider call and the pure parsing helpers; the Streamlit UI lives in ``views/ask.py``.

Personal project — the API key is the user's own (``ANTHROPIC_API_KEY``); this does
not use any employer system.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from anthropic.types import ToolParam

log = logging.getLogger(__name__)

MODEL = "claude-opus-4-8"

RUN_QUERY_TOOL: ToolParam = {
    "name": "run_query",
    "description": (
        "Return a single read-only DuckDB SELECT that answers the user's question "
        "over the Seattle-metro marts."
    ),
    "strict": True,
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": (
                    "One read-only SELECT/WITH statement over the main.mart_* tables. "
                    "No DDL/DML, no semicolon-separated statements."
                ),
            },
            "rationale": {
                "type": "string",
                "description": "One sentence describing what the query returns.",
            },
        },
        "required": ["sql", "rationale"],
        "additionalProperties": False,
    },
}


def build_system(catalog_text: str) -> str:
    """System prompt: rules + the marts catalog as grounding context."""
    return (
        "You translate questions about Seattle-metro open data into a single "
        "read-only DuckDB SQL query over pre-modeled marts.\n\n"
        "Rules:\n"
        "- Use ONLY the tables and columns listed in the catalog below. Every table "
        "is in the `main` schema (e.g. `main.mart_permits_monthly`).\n"
        "- Emit exactly one statement: a SELECT (optionally a WITH … SELECT). Never "
        "write, attach, copy, or use external-read functions.\n"
        "- Add a sensible LIMIT (<= 200) unless the question implies an aggregate.\n"
        "- If the question cannot be answered from these marts, return "
        "`select 'Not available in the marts' as note`.\n"
        "- Call the run_query tool with your SQL and a one-sentence rationale.\n\n"
        "CATALOG:\n"
        f"{catalog_text}"
    )


def extract_tool_input(response) -> dict:
    """Pull the run_query tool input out of a Messages response. Fails loud."""
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == "run_query":
            return dict(block.input)
    raise ValueError("Model did not return a run_query tool call")


def generate_sql(question: str, catalog_text: str, client=None) -> dict:
    """Ask Claude for a read-only SQL query. Returns {'sql', 'rationale'}."""
    import anthropic

    client = client or anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=build_system(catalog_text),
        tools=[RUN_QUERY_TOOL],
        tool_choice={"type": "tool", "name": "run_query"},
        messages=[{"role": "user", "content": question}],
    )
    result = extract_tool_input(response)
    log.info("Generated SQL for %r: %s", question, result.get("sql"))
    return result

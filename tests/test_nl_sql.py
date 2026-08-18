"""TDD for the NL→SQL parsing helpers (no network — the API call isn't unit-tested)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import nl_sql


def test_build_system_includes_rules_and_catalog():
    sys = nl_sql.build_system("TABLE main.mart_x — desc\n    col: c")
    assert "read-only" in sys
    assert "main.mart_x" in sys
    assert "run_query" in sys


def test_extract_tool_input_returns_sql_block():
    block = SimpleNamespace(type="tool_use", name="run_query",
                            input={"sql": "select 1", "rationale": "ok"})
    resp = SimpleNamespace(content=[SimpleNamespace(type="text"), block])
    assert nl_sql.extract_tool_input(resp) == {"sql": "select 1", "rationale": "ok"}


def test_extract_tool_input_raises_when_absent():
    resp = SimpleNamespace(content=[SimpleNamespace(type="text")])
    with pytest.raises(ValueError, match="run_query"):
        nl_sql.extract_tool_input(resp)

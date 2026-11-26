"""Every page renders against the built warehouse (PLAT-DEMO-04).

`/_stcore/health` only proves the server is up; a page that raises still shows a
recruiter a red error box. This drives the real entrypoint, switches to each
page registered in `streamlit_app.py`, and asserts nothing raised and no
`st.error` rendered. It needs the warehouse `build_warehouse.py` + `dbt build`
produce, so it skips when that is absent (CI); the Docker build runs it as a gate
right after baking the warehouse. Asserts on exceptions and elements only, never
on data values.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "seattle.duckdb"
PAGES = re.findall(r'st\.Page\("(views/[a-z0-9_]+\.py)"', (ROOT / "streamlit_app.py").read_text())

needs_warehouse = pytest.mark.skipif(
    not WAREHOUSE.exists(),
    reason="seattle.duckdb absent; run build_warehouse.py + dbt build (the Docker build runs this)",
)


def test_router_registers_every_view():
    # A page added to views/ but not the router would silently escape the smoke test.
    assert sorted(PAGES) == sorted(f"views/{p.name}" for p in (ROOT / "views").glob("*.py"))


@needs_warehouse
@pytest.mark.parametrize("page", PAGES)
def test_page_renders_without_error(page, app_test, monkeypatch):
    # The Ask page must render its no-key notice, not call the API, during the build.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    at = app_test("streamlit_app.py").run()
    at.switch_page(page).run()
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error, [e.value for e in at.error]

"""Shared pytest fixtures (keep tests DRY)."""

from __future__ import annotations

from collections.abc import Callable

import pytest


@pytest.fixture
def fake_soda_pages() -> Callable[[list[list[dict]]], Callable]:
    """Build a fake ``_soda_get`` that serves pre-canned pages by ``$offset``.

    Usage::

        get = fake_soda_pages([page1_rows, page2_rows, ...])
        monkeypatch.setattr(build_warehouse, "_soda_get", get)

    The returned callable mimics the real ``_soda_get(url, params, app_token)``
    signature and returns the page whose index matches ``$offset / $limit``.
    Requesting an offset past the last page yields ``[]`` (as Socrata does).
    """

    def _factory(pages: list[list[dict]]) -> Callable:
        def _get(url: str, params: dict, app_token: str | None) -> list[dict]:
            limit = params["$limit"]
            offset = params["$offset"]
            idx = offset // limit
            return pages[idx] if idx < len(pages) else []

        return _get

    return _factory

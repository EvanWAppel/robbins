"""ArcGIS paging must never silently truncate a layer (review of PS-TOPICS-04).

An HTTP-200 error body raises, a short page flagged exceededTransferLimit keeps
paging, paging is ordered by the object-id field so offsets are stable, and a
transient connection reset is retried before the build fails.
"""

from __future__ import annotations

import pytest
import requests

import build_warehouse as bw

BASE = "https://example.org/arcgis/rest/services/Permits/FeatureServer/0"
META = {"maxRecordCount": 2, "objectIdField": "OBJECTID"}


def feats(*ids):
    return [{"attributes": {"OBJECTID": i}, "geometry": None} for i in ids]


def serve(monkeypatch, pages, calls=None):
    """Fake _arcgis_get: metadata first, then the canned query responses in order."""
    queue = list(pages)

    def fake(url, params, ssl_verify):
        if calls is not None:
            calls.append(params)
        if not url.endswith("/query"):
            return META
        return queue.pop(0)

    monkeypatch.setattr(bw, "_arcgis_get", fake)


def test_error_body_mid_paging_raises(monkeypatch):
    serve(monkeypatch, [{"features": feats(1, 2)},
                        {"error": {"code": 500, "message": "Query timed out"}}])
    with pytest.raises(RuntimeError, match="Query timed out"):
        bw.fetch_features(BASE)


def test_missing_features_key_raises(monkeypatch):
    serve(monkeypatch, [{"unexpected": True}])
    with pytest.raises(RuntimeError, match="features"):
        bw.fetch_features(BASE)


def test_short_page_with_transfer_limit_keeps_paging(monkeypatch):
    serve(monkeypatch, [{"features": feats(1), "exceededTransferLimit": True},
                        {"features": feats(2, 3)},
                        {"features": []}])
    out = bw.fetch_features(BASE)
    assert [a["OBJECTID"] for a, _ in out] == [1, 2, 3]


def test_paging_is_ordered_by_object_id(monkeypatch):
    calls: list[dict] = []
    serve(monkeypatch, [{"features": feats(1)}], calls)
    bw.fetch_features(BASE)
    query = [c for c in calls if "resultOffset" in c]
    assert query and all(c["orderByFields"] == "OBJECTID" for c in query)


def test_transient_connection_reset_is_retried(monkeypatch):
    monkeypatch.setattr(bw.time, "sleep", lambda s: None)
    attempts = {"n": 0}

    class Resp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"ok": True}

    def flaky(url, params=None, timeout=None, verify=True):
        attempts["n"] += 1
        if attempts["n"] < 3:
            raise requests.ConnectionError("Connection reset by peer")
        return Resp()

    monkeypatch.setattr(bw.requests, "get", flaky)
    assert bw._arcgis_get(BASE, {"f": "json"}, True) == {"ok": True}
    assert attempts["n"] == 3


def test_persistent_connection_failure_raises(monkeypatch):
    monkeypatch.setattr(bw.time, "sleep", lambda s: None)

    def down(url, params=None, timeout=None, verify=True):
        raise requests.ConnectionError("Connection reset by peer")

    monkeypatch.setattr(bw.requests, "get", down)
    with pytest.raises(requests.ConnectionError):
        bw._arcgis_get(BASE, {"f": "json"}, True)

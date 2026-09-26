"""TDD for the MCPP neighborhood geometry transform.

``mcpp_feature_row`` is the pure piece: it turns one ArcGIS polygon feature
(attributes + geometry) into the raw.mcpp row that feeds the point-in-polygon
choropleth joins (GeoJSON) and the map render (rings). We test the shape and the
area conversion here; the spatial join itself is exercised by dbt against the
built warehouse.
"""

from __future__ import annotations

import json

import build_warehouse as bw


def _square_feature() -> tuple[dict, dict]:
    # A 1 sq-mile-ish square (in lon/lat degrees the units don't matter for the
    # transform) plus Shape__Area in square feet = exactly two square miles.
    attrs = {
        "neighborhood": "alaska junction",
        "precinct": "SW",
        "Shape__Area": 2 * 27_878_400.0,
    }
    geom = {"rings": [[[0.0, 0.0], [0.0, 1.0], [1.0, 1.0], [1.0, 0.0], [0.0, 0.0]]]}
    return attrs, geom


def test_mcpp_feature_row_shape_and_area():
    row = bw.mcpp_feature_row(*_square_feature())
    assert row is not None
    # Name is normalized to uppercase (matches SPD crime's MCPP naming).
    assert row["neighborhood"] == "ALASKA JUNCTION"
    assert row["precinct"] == "SW"
    # 2 * sqft-per-sqmile -> exactly 2 square miles.
    assert row["area_sq_miles"] == 2.0
    # Bounding box spans the square.
    assert (row["minx"], row["miny"], row["maxx"], row["maxy"]) == (0.0, 0.0, 1.0, 1.0)
    # Centroid is the vertex average of the (deduped) ring.
    assert row["centroid_lon"] == 0.5
    assert row["centroid_lat"] == 0.5


def test_mcpp_feature_row_geojson_is_multipolygon():
    row = bw.mcpp_feature_row(*_square_feature())
    assert row is not None
    gj = json.loads(row["geojson"])
    assert gj["type"] == "MultiPolygon"
    # One ring -> one polygon -> one outer ring of 5 closed vertices.
    assert len(gj["coordinates"]) == 1
    assert len(gj["coordinates"][0]) == 1
    assert gj["coordinates"][0][0][0] == [0.0, 0.0]
    # rings_json round-trips the raw rings for rendering.
    assert json.loads(row["rings_json"]) == _square_feature()[1]["rings"]


def test_mcpp_feature_row_none_without_rings():
    assert bw.mcpp_feature_row({"neighborhood": "X"}, None) is None
    assert bw.mcpp_feature_row({"neighborhood": "X"}, {"rings": []}) is None

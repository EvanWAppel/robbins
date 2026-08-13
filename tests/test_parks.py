"""TDD for the Parks topic (Seattle ArcGIS Park_Boundaries).

The fetch itself reuses the ArcGIS helpers; the one bespoke transform is the
name-derived water flag — Seattle has many waterfront parks, and the boundary
layer carries no amenity attributes, so we flag parks whose name references
water (beaches, lakes, waterfronts, boat ramps, ...). It's an approximation and
labeled as such in the UI, but the rule is pure and worth testing.
"""

from __future__ import annotations

import build_warehouse as bw


def test_water_name_matches_natural_water():
    assert bw.is_water_park_name("GREEN LAKE")
    assert bw.is_water_park_name("DISCOVERY PARK TIDELANDS")
    assert bw.is_water_park_name("14TH AVENUE NW BOAT RAMP")


def test_water_name_is_case_insensitive():
    assert bw.is_water_park_name("Alki Beach Park")


def test_water_name_false_for_dry_parks():
    assert not bw.is_water_park_name("12TH AVE SQUARE PARK")
    assert not bw.is_water_park_name("CAL ANDERSON PARK")


def test_water_name_ignores_substring_false_positives():
    # "Discovery" merely *contains* "cove"; word-boundary matching must not flag it.
    assert not bw.is_water_park_name("DISCOVERY PARK")


def test_water_name_handles_missing_name():
    assert not bw.is_water_park_name(None)
    assert not bw.is_water_park_name("")

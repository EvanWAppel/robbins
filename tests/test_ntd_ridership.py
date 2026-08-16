"""TDD for the NTD ridership topic (transit + ferry share one federal source).

The fetch reuses ``fetch_socrata``; the bespoke transform is mapping NTD's
two-letter mode codes to human labels. The rule is pure — known codes map to a
label, unknown codes fall back to the raw code so nothing is silently lost — and
it drives the "by mode" charts on the transit page.
"""

from __future__ import annotations

import build_warehouse as bw


def test_known_modes_map_to_labels():
    assert bw.ntd_mode_label("MB") == "Bus"
    assert bw.ntd_mode_label("LR") == "Light Rail"
    assert bw.ntd_mode_label("FB") == "Ferryboat"
    assert bw.ntd_mode_label("CR") == "Commuter Rail"


def test_mode_code_is_case_and_space_insensitive():
    assert bw.ntd_mode_label(" mb ") == "Bus"
    assert bw.ntd_mode_label("fb") == "Ferryboat"


def test_unknown_mode_falls_back_to_code():
    assert bw.ntd_mode_label("ZZ") == "ZZ"


def test_missing_mode_is_unknown():
    assert bw.ntd_mode_label(None) == "Unknown"
    assert bw.ntd_mode_label("") == "Unknown"

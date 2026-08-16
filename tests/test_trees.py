"""TDD for the Trees topic (Seattle ArcGIS SDOT_Trees_(Active)).

The fetch reuses the ArcGIS helpers; the one bespoke transform is deriving a
tree's genus from its scientific name (SDOT records the full binomial). The rule
is pure — first token, minus a hybrid marker, blanks/placeholders treated as
unknown — and worth testing.
"""

from __future__ import annotations

import build_warehouse as bw


def test_genus_is_first_token_titlecased():
    assert bw.tree_genus("Acer rubrum") == "Acer"
    assert bw.tree_genus("Cercidiphyllum japonicum") == "Cercidiphyllum"


def test_genus_lowercase_input_titlecased():
    assert bw.tree_genus("quercus garryana") == "Quercus"


def test_genus_skips_hybrid_marker():
    # Intergeneric hybrids are written with a leading "x" / "×".
    assert bw.tree_genus("x Cupressocyparis leylandii") == "Cupressocyparis"
    assert bw.tree_genus("× Cupressocyparis leylandii") == "Cupressocyparis"


def test_genus_none_for_missing_or_placeholder():
    assert bw.tree_genus(None) is None
    assert bw.tree_genus("") is None
    assert bw.tree_genus("   ") is None
    assert bw.tree_genus("Unknown") is None
    assert bw.tree_genus("VACANT") is None


def test_genus_single_word_name():
    assert bw.tree_genus("Magnolia") == "Magnolia"

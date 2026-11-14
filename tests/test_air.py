"""Air risk tests: SORA 2.5 Steps #5 and #6 (Table 6)."""

import pytest

from jarus_sora.air import normalize_arc, residual_arc, tmpr_for_arc


def test_vlos_reduces_the_arc_by_one_class():
    assert residual_arc("d", vlos=True) == "c"
    assert residual_arc("c", vlos=True) == "b"
    assert residual_arc("D", vlos=True) == "c"


def test_vlos_cannot_reduce_to_arc_a():
    # Step #5: the mitigation cannot be used to reduce the ARC
    # to an ARC-a, so ARC-b stays ARC-b.
    assert residual_arc("b", vlos=True) == "b"
    assert residual_arc("a", vlos=True) == "a"


def test_bvlos_keeps_the_initial_arc():
    for arc in ("a", "b", "c", "d"):
        assert residual_arc(arc, vlos=False) == arc


def test_tmpr_follows_table_6():
    assert tmpr_for_arc("a") == ("No requirement", "No requirement")
    assert tmpr_for_arc("b") == ("Low", "Low")
    assert tmpr_for_arc("c") == ("Medium", "Medium")
    assert tmpr_for_arc("d") == ("High", "High")


def test_invalid_arc_rejected():
    with pytest.raises(ValueError):
        normalize_arc("e")
    with pytest.raises(ValueError):
        residual_arc("ARC-b", vlos=True)
    with pytest.raises(ValueError):
        tmpr_for_arc("")

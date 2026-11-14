"""SAIL and OSO tests: SORA 2.5 Tables 7 and 14.

The whole SAIL table is pinned cell by cell. OSO counts per
SAIL are checked against the table, and spot rows are checked
in full.
"""

import pytest

from jarus_sora.sail import osos_for_sail, sail_for
from jarus_sora.tables import OSO_TABLE, SAIL_TABLE

EXPECTED_SAIL = (
    ("I", "II", "IV", "VI"),
    ("II", "II", "IV", "VI"),
    ("III", "III", "IV", "VI"),
    ("IV", "IV", "IV", "VI"),
    ("V", "V", "V", "VI"),
    ("VI", "VI", "VI", "VI"),
    ("CERTIFIED", "CERTIFIED", "CERTIFIED", "CERTIFIED"),
)

ARCS = ("a", "b", "c", "d")


def test_sail_table_matches_the_published_table():
    assert SAIL_TABLE == EXPECTED_SAIL


@pytest.mark.parametrize("row,grc", list(enumerate((2, 3, 4, 5, 6, 7, 8))))
@pytest.mark.parametrize("col,arc", list(enumerate(ARCS)))
def test_every_sail_cell(row, grc, col, arc):
    assert sail_for(grc, arc) == EXPECTED_SAIL[row][col]


def test_sail_boundaries():
    assert sail_for(1, "a") == "I"
    assert sail_for(2, "b") == "II"
    assert sail_for(7, "a") == "VI"
    assert sail_for(8, "a") == "CERTIFIED"
    assert sail_for(10, "d") == "CERTIFIED"
    # ARC-d means SAIL VI whatever the ground risk.
    assert sail_for(1, "d") == "VI"
    with pytest.raises(ValueError):
        sail_for(0, "a")
    with pytest.raises(ValueError):
        sail_for(4, "e")


def test_oso_table_has_17_objectives():
    assert len(OSO_TABLE) == 17
    ids = [row[0] for row in OSO_TABLE]
    assert ids == [
        "OSO#01", "OSO#02", "OSO#03", "OSO#04", "OSO#05", "OSO#06",
        "OSO#07", "OSO#08", "OSO#09", "OSO#13", "OSO#16", "OSO#17",
        "OSO#18", "OSO#19", "OSO#20", "OSO#23", "OSO#24",
    ]


def test_oso_robustness_counts_per_sail():
    # Count of required (non-NR) OSOs and of high-robustness OSOs.
    expected = {
        "I": (8, 0),
        "II": (11, 0),
        "III": (16, 1),
        "IV": (17, 4),
        "V": (17, 14),
        "VI": (17, 17),
    }
    for sail, (required, high) in expected.items():
        rows = osos_for_sail(sail)
        assert len(rows) == 17
        assert sum(1 for r in rows if r["robustness"] != "NR") == required
        assert sum(1 for r in rows if r["robustness"] == "H") == high


def test_oso_spot_rows_in_full():
    rows = {r["id"]: r for r in osos_for_sail("III")}
    assert rows["OSO#01"]["robustness"] == "M"
    assert rows["OSO#04"]["robustness"] == "NR"
    assert rows["OSO#08"]["robustness"] == "H"
    assert rows["OSO#24"]["robustness"] == "M"
    rows_vi = {r["id"]: r for r in osos_for_sail("VI")}
    assert all(r["robustness"] == "H" for r in rows_vi.values())
    rows_i = {r["id"]: r for r in osos_for_sail("I")}
    assert rows_i["OSO#05"]["robustness"] == "NR"
    assert rows_i["OSO#05"]["note"] == ""
    rows_ii = {r["id"]: r for r in osos_for_sail("II")}
    assert "novel or complex" in rows_ii["OSO#05"]["note"]


def test_invalid_sail_rejected():
    with pytest.raises(ValueError):
        osos_for_sail("VII")
    with pytest.raises(ValueError):
        osos_for_sail("CERTIFIED")

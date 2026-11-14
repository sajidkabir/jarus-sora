"""Ground risk tests: SORA 2.5 Table 2, Table 3, and Table 5.

The whole iGRC table is pinned cell by cell, because a wrong
cell here moves every SAIL that follows. Worked cases are
hand-computed from the tables.
"""

import pytest

from jarus_sora.ground import (
    OutOfSoraError,
    density_band,
    density_band_for_descriptor,
    final_grc,
    intrinsic_grc,
)
from jarus_sora.tables import IGRC_TABLE

# The full Table 2, transcribed independently of the module data,
# so a transcription error in tables.py fails here.
EXPECTED_IGRC = (
    (1, 1, 2, 3, 3),
    (2, 3, 4, 5, 6),
    (3, 4, 5, 6, 7),
    (4, 5, 6, 7, 8),
    (5, 6, 7, 8, 9),
    (6, 7, 8, 9, 10),
    (7, 8, None, None, None),
)

COLUMNS = ((1.0, 25.0), (3.0, 35.0), (8.0, 75.0), (20.0, 120.0), (40.0, 200.0))
# One density inside each band (row 0 is the controlled area).
BAND_DENSITIES = (0.0, 2.0, 20.0, 200.0, 2000.0, 20000.0, 60000.0)


def test_igrc_table_matches_the_published_table():
    assert IGRC_TABLE == EXPECTED_IGRC


@pytest.mark.parametrize("row,density", list(enumerate(BAND_DENSITIES)))
@pytest.mark.parametrize(
    "col,dim,speed",
    [(i, dim, speed) for i, (dim, speed) in enumerate(COLUMNS)],
)
def test_every_igrc_cell(row, density, col, dim, speed):
    expected = EXPECTED_IGRC[row][col]
    if expected is None:
        with pytest.raises(OutOfSoraError):
            intrinsic_grc(dim, speed, density)
    else:
        assert intrinsic_grc(dim, speed, density) == expected


def test_column_is_driven_by_the_larger_of_dimension_and_speed():
    # 1 m airframe but 35 m/s: the speed column governs.
    assert intrinsic_grc(1.0, 35.0, 20.0) == 4
    # 3 m airframe but only 25 m/s: the dimension column governs.
    assert intrinsic_grc(3.0, 25.0, 20.0) == 4
    # Both at the column edge stay in the column.
    assert intrinsic_grc(3.0, 35.0, 20.0) == 4
    assert intrinsic_grc(8.0, 75.0, 20.0) == 5


def test_density_on_a_band_edge_takes_the_next_band_up():
    # Table 2 bands are "less than": exactly 5 is not "< 5".
    assert density_band(4.999) == 1
    assert density_band(5.0) == 2
    assert density_band(50.0) == 3
    assert density_band(50000.0) == 6
    assert density_band(0.0) == 0


def test_controlled_ground_area_is_row_zero_whatever_the_density():
    assert intrinsic_grc(3.0, 35.0, 60000.0, controlled_ground_area=True) == 1


def test_descriptors_map_to_table_3_rows():
    assert density_band_for_descriptor("sparsely populated") == 2
    assert density_band_for_descriptor("Lightly Populated") == 2
    assert density_band_for_descriptor("low density metropolitan") == 4
    assert density_band_for_descriptor("assemblies of people") == 6
    assert intrinsic_grc(3.0, 35.0, descriptor="remote") == 3
    with pytest.raises(ValueError):
        density_band_for_descriptor("downtown")
    with pytest.raises(ValueError):
        intrinsic_grc(3.0, 35.0, 20.0, descriptor="remote")
    with pytest.raises(ValueError):
        intrinsic_grc(3.0, 35.0)


def test_250g_shortcut_gives_igrc_1():
    assert intrinsic_grc(0.5, 15.0, 60000.0, mass_kg=0.2) == 1
    assert intrinsic_grc(0.5, 25.0, 60000.0, mass_kg=0.25) == 1
    # Over the mass limit: no shortcut, dense city, 1 m column.
    assert intrinsic_grc(0.5, 25.0, 60000.0, mass_kg=0.26) == 7
    # Over the speed limit: no shortcut.
    assert intrinsic_grc(0.5, 26.0, 60000.0, mass_kg=0.2) == 8


def test_aircraft_beyond_the_table_is_outside_sora():
    with pytest.raises(OutOfSoraError):
        intrinsic_grc(41.0, 100.0, 20.0)
    with pytest.raises(OutOfSoraError):
        intrinsic_grc(8.0, 201.0, 20.0)
    with pytest.raises(OutOfSoraError):
        intrinsic_grc(8.0, 75.0, 60000.0)


def test_invalid_ground_inputs_rejected():
    with pytest.raises(ValueError):
        intrinsic_grc(0.0, 25.0, 20.0)
    with pytest.raises(ValueError):
        intrinsic_grc(3.0, -5.0, 20.0)
    with pytest.raises(ValueError):
        density_band(-1.0)


def test_mitigation_credits_follow_table_5():
    # iGRC 6, 3 m column: M1(A) medium -2 and M2 medium -1.
    final, credits = final_grc(6, 3.0, 35.0, {"m1a": "medium", "m2": "medium"})
    assert final == 3
    assert credits == {"m1a": -2, "m1b": 0, "m1c": 0, "m2": -1}
    # No mitigations: the final GRC is the iGRC.
    final, _ = final_grc(6, 3.0, 35.0, {})
    assert final == 6


def test_mitigation_levels_not_in_table_5_are_rejected():
    with pytest.raises(ValueError):
        final_grc(6, 3.0, 35.0, {"m1a": "high"})
    with pytest.raises(ValueError):
        final_grc(6, 3.0, 35.0, {"m1b": "low"})
    with pytest.raises(ValueError):
        final_grc(6, 3.0, 35.0, {"m1c": "medium"})
    with pytest.raises(ValueError):
        final_grc(6, 3.0, 35.0, {"m2": "low"})
    with pytest.raises(ValueError):
        final_grc(6, 3.0, 35.0, {"m1a": "strong"})
    with pytest.raises(ValueError):
        final_grc(6, 3.0, 35.0, {"m3": "high"})


def test_combined_m1_credit_is_capped_at_3():
    # Raw M1 credit would be -5; the cap holds it at -3.
    final, credits = final_grc(
        6, 3.0, 35.0,
        {"m1a": "medium", "m1b": "high", "m1c": "low"},
    )
    assert credits["m1a"] == -2
    assert credits["m1b"] == -2
    assert credits["m1c"] == -1
    assert final == 3


def test_m1_cannot_go_below_the_controlled_area_floor():
    # 1 m column, floor 1: iGRC 2 with M1 medium/high cannot go below 1.
    final, _ = final_grc(
        2, 1.0, 25.0, {"m1a": "medium", "m1b": "high"}
    )
    assert final == 1


def test_m2_applies_after_the_m1_floor():
    # 8 m column, floor 2: M1 takes 4 to the floor 2, then M2 high
    # takes it to 1, below the floor. M2 reduces impact energy,
    # not the number of people at risk.
    final, _ = final_grc(
        4, 8.0, 75.0, {"m1a": "medium", "m2": "high"}
    )
    assert final == 1


def test_final_grc_never_below_1():
    final, _ = final_grc(1, 1.0, 25.0, {"m1a": "medium", "m2": "high"})
    assert final == 1

"""End-to-end assessment tests: worked ConOps with hand-computed
results, plus the adjacent-area size from the SORA worked example.
"""

import pytest

from jarus_sora.assessment import (
    ConOps,
    adjacent_area_radius_km,
    assess,
    assessment_report,
)
from jarus_sora.ground import OutOfSoraError


def test_sub_250g_toy_is_sail_i():
    result = assess(ConOps(
        dimension_m=0.5, max_speed_m_s=15.0, mass_kg=0.2,
        density_per_km2=4000.0, initial_arc="a",
    ))
    assert result.igrc == 1
    assert result.final_grc_value == 1
    assert result.residual_arc_value == "a"
    assert result.tmpr == "No requirement"
    assert result.sail == "I"
    assert result.certified is False
    assert len(result.osos) == 17
    assert sum(1 for o in result.osos if o["robustness"] != "NR") == 8
    # 15 m/s for 3 minutes is 2.7 km, clamped to the 5 km minimum.
    assert result.adjacent_area_radius_km == 5.0


def test_rural_bvlos_survey_is_sail_iv():
    # 2.5 m, 30 m/s, 4 kg over 40 people/km2: iGRC 4. Sheltering
    # medium (-2) and a medium parachute (-1) take the final GRC
    # to 1. Initial ARC-c, BVLOS, so residual ARC-c. SAIL IV.
    result = assess(ConOps(
        dimension_m=2.5, max_speed_m_s=30.0, mass_kg=4.0,
        density_per_km2=40.0,
        mitigations={"m1a": "medium", "m2": "medium"},
        initial_arc="c", vlos=False,
    ))
    assert result.igrc == 4
    assert result.final_grc_value == 1
    assert result.mitigation_credits == {
        "m1a": -2, "m1b": 0, "m1c": 0, "m2": -1,
    }
    assert result.residual_arc_value == "c"
    assert result.tmpr == "Medium"
    assert result.tmpr_robustness == "Medium"
    assert result.sail == "IV"
    # 30 m/s for 3 minutes is 5.4 km: the value in the SORA
    # worked example for this same aircraft.
    assert result.adjacent_area_radius_km == pytest.approx(5.4)


def test_suburban_vlos_delivery_is_sail_ii():
    # 1.8 m, 25 m/s, 6 kg over 1200 people/km2: iGRC 6. M1(A) low,
    # M1(B) medium, M1(C) low total -3, the combined M1 cap, so
    # the final GRC is 3. Initial ARC-b with VLOS stays b (the
    # reduction cannot reach ARC-a). SAIL II, TMPR low.
    result = assess(ConOps(
        dimension_m=1.8, max_speed_m_s=25.0, mass_kg=6.0,
        density_per_km2=1200.0,
        mitigations={"m1a": "low", "m1b": "medium", "m1c": "low"},
        initial_arc="b", vlos=True,
    ))
    assert result.igrc == 6
    assert result.final_grc_value == 3
    assert result.residual_arc_value == "b"
    assert result.tmpr == "Low"
    assert result.sail == "II"
    assert any("cannot take the ARC to ARC-a" in n for n in result.notes)


def test_large_aircraft_over_a_city_is_certified():
    # 3 m, 35 m/s over 40000 people/km2: iGRC 7, no mitigations,
    # residual ARC-d. SAIL VI.
    result = assess(ConOps(
        dimension_m=3.0, max_speed_m_s=35.0, mass_kg=25.0,
        density_per_km2=40000.0, initial_arc="d",
    ))
    assert result.igrc == 7
    assert result.final_grc_value == 7
    assert result.sail == "VI"
    assert result.tmpr == "High"


def test_out_of_sora_operation_raises():
    with pytest.raises(OutOfSoraError):
        assess(ConOps(
            dimension_m=8.0, max_speed_m_s=70.0,
            density_per_km2=60000.0, initial_arc="c",
        ))


def test_jarus_worked_example_numbers():
    # SORA 2.5 section 4.8.4: a 2.5 m drone at 30 m/s, adjacent
    # area outer limit 5.4 km, average density 1000-4000/km2.
    assert adjacent_area_radius_km(30.0) == pytest.approx(5.4)
    from jarus_sora.ground import intrinsic_grc
    assert intrinsic_grc(2.5, 30.0, 2000.0) == 6


def test_adjacent_area_radius_clamps():
    assert adjacent_area_radius_km(10.0) == 5.0
    assert adjacent_area_radius_km(100.0) == 18.0
    assert adjacent_area_radius_km(300.0) == 35.0
    with pytest.raises(ValueError):
        adjacent_area_radius_km(0.0)


def test_report_names_every_step():
    result = assess(ConOps(
        dimension_m=2.5, max_speed_m_s=30.0, mass_kg=4.0,
        density_per_km2=40.0,
        mitigations={"m1a": "medium", "m2": "medium"},
        initial_arc="c", vlos=False,
    ))
    report = assessment_report(result)
    assert "Intrinsic GRC (iGRC): 4" in report
    assert "Final GRC: 1" in report
    assert "Residual ARC: c" in report
    assert "TMPR: Medium" in report
    assert "SAIL: IV" in report
    assert "OSO#08 [H]" in report
    assert "not an authorisation" in report

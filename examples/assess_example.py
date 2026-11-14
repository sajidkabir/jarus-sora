"""Assess the rural BVLOS survey from examples/rural_survey.json
and print the full report.

A 2.5 m, 30 m/s, 4 kg quadrotor over 40 people/km2, with medium
sheltering and a medium parachute, in ARC-c airspace, BVLOS.
Expected: iGRC 4, final GRC 1, residual ARC-c, TMPR medium,
SAIL IV.
"""

from pathlib import Path

from jarus_sora.assessment import ConOps, assess, assessment_report

CONOPS = ConOps(
    dimension_m=2.5,
    max_speed_m_s=30.0,
    mass_kg=4.0,
    density_per_km2=40.0,
    mitigations={"m1a": "medium", "m2": "medium"},
    initial_arc="c",
    vlos=False,
)


def main() -> None:
    result = assess(CONOPS)
    print(assessment_report(result))
    print()
    print(f"(ConOps file: {Path(__file__).parent / 'rural_survey.json'})")


if __name__ == "__main__":
    main()

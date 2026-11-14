"""Full assessment: run SORA 2.5 Steps #2 to #7 and #9 from one
Concept of Operations, and the Step #8 adjacent-area size.

The pipeline is: intrinsic GRC (Step #2) -> final GRC (Step #3)
-> residual ARC (Step #5) -> TMPR (Step #6) -> SAIL (Step #7)
-> OSO robustness (Step #9). Step #1 (the ConOps itself) and
Step #10 (the Comprehensive Safety Portfolio) are documentation
the operator writes; this package computes the numbers that go
into them. Step #8 containment Tables 8-13 are not in this
release; the adjacent-area size formula is included.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .air import normalize_arc, residual_arc, tmpr_for_arc
from .ground import final_grc, intrinsic_grc
from .sail import osos_for_sail, sail_for
from .tables import (
    ADJACENT_AREA_MAX_KM,
    ADJACENT_AREA_MIN_KM,
    ADJACENT_AREA_MINUTES,
)


@dataclass(frozen=True)
class ConOps:
    """The operation being assessed (SORA Step #1, in numbers).

    dimension_m: max characteristic dimension (wingspan, blade
      diameter, or max distance between blade tips), metres.
    max_speed_m_s: max possible commanded airspeed, m/s.
    mass_kg: UA mass in kg; needed for the 250 g shortcut.
    density_per_km2: max population density in the iGRC footprint,
      people per km2. Give this or descriptor, not both.
    descriptor: Table 3 qualitative descriptor instead of a number.
    controlled_ground_area: True when only involved persons are
      present in the operational area.
    mitigations: ground risk mitigations, keys m1a, m1b, m1c, m2
      with robustness none/low/medium/high.
    initial_arc: initial Air Risk Class a/b/c/d, from Figure 6 or
      an airspace collision risk map.
    vlos: True for VLOS, or a remote pilot supported by an airspace
      observer alongside the pilot (Step #5 one-class reduction).
    """

    dimension_m: float
    max_speed_m_s: float
    mass_kg: float | None = None
    density_per_km2: float | None = None
    descriptor: str | None = None
    controlled_ground_area: bool = False
    mitigations: dict[str, str] = field(default_factory=dict)
    initial_arc: str = "b"
    vlos: bool = False


@dataclass(frozen=True)
class Assessment:
    """Every SORA number for one ConOps, with the audit trail."""

    igrc: int
    final_grc_value: int
    mitigation_credits: dict[str, int]
    initial_arc: str
    residual_arc_value: str
    tmpr: str
    tmpr_robustness: str
    sail: str
    osos: tuple[dict[str, str], ...]
    adjacent_area_radius_km: float
    certified: bool
    notes: tuple[str, ...]


def adjacent_area_radius_km(max_speed_m_s: float) -> float:
    """Step #8: lateral outer limit of the adjacent area.

    The distance flown in 3 minutes at maximum speed, at least
    5 km and at most 35 km.
    """
    if max_speed_m_s <= 0:
        raise ValueError("maximum speed must be positive")
    distance = max_speed_m_s * ADJACENT_AREA_MINUTES * 60.0 / 1000.0
    return min(max(distance, ADJACENT_AREA_MIN_KM), ADJACENT_AREA_MAX_KM)


def assess(conops: ConOps) -> Assessment:
    """Run Steps #2 to #7 and #9 for one Concept of Operations."""
    igrc = intrinsic_grc(
        conops.dimension_m,
        conops.max_speed_m_s,
        conops.density_per_km2,
        descriptor=conops.descriptor,
        mass_kg=conops.mass_kg,
        controlled_ground_area=conops.controlled_ground_area,
    )
    final, credits = final_grc(
        igrc, conops.dimension_m, conops.max_speed_m_s,
        conops.mitigations,
    )
    initial = normalize_arc(conops.initial_arc)
    residual = residual_arc(initial, vlos=conops.vlos)
    tmpr, tmpr_robustness = tmpr_for_arc(residual)
    sail = sail_for(final, residual)
    certified = sail == "CERTIFIED"
    osos = tuple(osos_for_sail(sail)) if not certified else ()
    notes: list[str] = []
    if conops.vlos and initial != residual:
        notes.append(
            "VLOS strategic mitigation applied: initial ARC "
            f"{initial} reduced to residual ARC {residual}."
        )
    if conops.vlos and initial == "b" and residual == "b":
        notes.append(
            "VLOS reduction cannot take the ARC to ARC-a, so "
            "residual ARC stays b."
        )
    if certified:
        notes.append(
            "Final GRC is above 7: the operation is outside SORA "
            "and belongs in the certified category."
        )
    if final <= 2 and residual == "d":
        notes.append(
            "Residual ARC-d sets SAIL VI whatever the ground risk; "
            "an agreement with ATC may be required."
        )
    return Assessment(
        igrc=igrc,
        final_grc_value=final,
        mitigation_credits=credits,
        initial_arc=initial,
        residual_arc_value=residual,
        tmpr=tmpr,
        tmpr_robustness=tmpr_robustness,
        sail=sail,
        osos=osos,
        adjacent_area_radius_km=adjacent_area_radius_km(
            conops.max_speed_m_s
        ),
        certified=certified,
        notes=tuple(notes),
    )


def assessment_report(assessment: Assessment) -> str:
    """Plain-text report of an assessment, for the CLI and logs."""
    lines = [
        f"Intrinsic GRC (iGRC): {assessment.igrc}",
        f"Final GRC: {assessment.final_grc_value}",
    ]
    credits = ", ".join(
        f"{key} {value:+d}"
        for key, value in assessment.mitigation_credits.items()
        if value != 0
    )
    lines.append(
        f"Mitigation credits: {credits or 'none claimed'}"
    )
    lines.append(f"Initial ARC: {assessment.initial_arc}")
    lines.append(f"Residual ARC: {assessment.residual_arc_value}")
    lines.append(
        f"TMPR: {assessment.tmpr} "
        f"(robustness {assessment.tmpr_robustness})"
    )
    lines.append(f"SAIL: {assessment.sail}")
    lines.append(
        "Adjacent area radius: "
        f"{assessment.adjacent_area_radius_km:.1f} km"
    )
    if assessment.certified:
        lines.append(
            "Result: CERTIFIED category - outside the scope of SORA."
        )
    else:
        required = [
            oso for oso in assessment.osos if oso["robustness"] != "NR"
        ]
        if len(required) == len(assessment.osos):
            lines.append(
                f"OSOs: all {len(assessment.osos)} required at this SAIL."
            )
        else:
            lines.append(
                f"OSOs: {len(required)} of {len(assessment.osos)} "
                "required at this SAIL (the rest are not required)."
            )
        for oso in assessment.osos:
            mark = oso["robustness"]
            lines.append(f"  {oso['id']} [{mark}] {oso['title']}")
            if oso["note"]:
                lines.append(f"    Note: {oso['note']}")
    for note in assessment.notes:
        lines.append(f"Note: {note}")
    lines.append(
        "This is a calculation aid for JARUS SORA 2.5, not an "
        "authorisation. Only the competent authority decides."
    )
    return "\n".join(lines)

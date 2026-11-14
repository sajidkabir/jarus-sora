"""Air risk: SORA 2.5 Steps #4, #5, and #6.

Step #4 assigns the initial Air Risk Class (ARC) from the Figure 6
decision tree in the source document. That tree is a figure, not a
table, so this release takes the initial ARC as an input the
operator determines from Figure 6 (or from an airspace collision
risk map provided by the competent authority, ANSP, or UTM
provider), and documents the assignment rules it can state. Step
#5 applies the documented VLOS strategic reduction to reach the
residual ARC. Step #6 reads the Tactical Mitigation Performance
Requirement (TMPR) from Table 6.
"""

from __future__ import annotations

from .tables import TMPR_TABLE

ARC_LEVELS = ("a", "b", "c", "d")

ARC_TITLES = {
    "a": "ARC-a - atypical airspace: manned aircraft encounter is "
    "acceptably low without tactical mitigation",
    "b": "ARC-b - low encounter rate with manned aircraft",
    "c": "ARC-c - medium encounter rate with manned aircraft",
    "d": "ARC-d - high encounter rate with manned aircraft",
}


def normalize_arc(value: str) -> str:
    """Validate an ARC letter, returning lowercase a, b, c, or d."""
    arc = value.strip().lower()
    if arc not in ARC_LEVELS:
        raise ValueError(
            f"unknown air risk class {value!r}; use one of a, b, c, d"
        )
    return arc


def residual_arc(initial_arc: str, *, vlos: bool) -> str:
    """Residual ARC after Step #5 strategic mitigations.

    For VLOS operations, or where the remote pilot is supported by
    an airspace observer alongside the pilot, the initial ARC is
    reduced by one class. The reduction cannot take the ARC to
    ARC-a, so ARC-b stays ARC-b. In ARC-d environments an
    additional agreement with ATC may be required.
    """
    arc = normalize_arc(initial_arc)
    if not vlos:
        return arc
    index = ARC_LEVELS.index(arc)
    # One class lower, but never to ARC-a: ARC-b stays ARC-b and
    # ARC-a stays ARC-a.
    reduced = index - 1 if index >= 2 else index
    return ARC_LEVELS[reduced]


def tmpr_for_arc(residual: str) -> tuple[str, str]:
    """(TMPR, TMPR level of robustness) for a residual ARC, Table 6.

    Only applies to BVLOS segments: VLOS is itself an acceptable
    tactical mitigation for collision risk at all ARC levels.
    """
    arc = normalize_arc(residual)
    return TMPR_TABLE[arc]

"""SAIL and Operational Safety Objectives: SORA 2.5 Steps #7 and #9.

Step #7 reads the Specific Assurance and Integrity Level from
Table 7 using the final GRC and the residual ARC. Step #9 maps
the SAIL to the required robustness of each Operational Safety
Objective in Table 14.
"""

from __future__ import annotations

from .tables import OSO_NOTES, OSO_TABLE, SAIL_LEVELS, SAIL_TABLE
from .air import normalize_arc

ARC_COLUMNS = ("a", "b", "c", "d")


def sail_for(final_grc: int, residual_arc: str) -> str:
    """SAIL (I-VI) for a final GRC and residual ARC, Table 7.

    Returns "CERTIFIED" when the final GRC is above 7: the
    operation is outside SORA and belongs in the certified
    category.
    """
    if final_grc < 1:
        raise ValueError("final GRC must be at least 1")
    arc = normalize_arc(residual_arc)
    if final_grc <= 2:
        row = 0
    elif final_grc <= 7:
        row = final_grc - 2
    else:
        row = 6
    return SAIL_TABLE[row][ARC_COLUMNS.index(arc)]


def osos_for_sail(sail: str) -> list[dict[str, str]]:
    """Table 14 OSOs with required robustness for a SAIL.

    Each entry is a dict with id, title, robustness ("NR", "L",
    "M", "H"), and a note where the table carries one.
    """
    if sail not in SAIL_LEVELS:
        raise ValueError(
            f"unknown SAIL {sail!r}; use one of "
            f"{', '.join(SAIL_LEVELS)}"
        )
    index = SAIL_LEVELS.index(sail)
    result = []
    for oso_id, title, levels in OSO_TABLE:
        result.append(
            {
                "id": oso_id,
                "title": title,
                "robustness": levels[index],
                "note": OSO_NOTES.get((oso_id, sail), ""),
            }
        )
    return result

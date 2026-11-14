"""Ground risk: SORA 2.5 Steps #2 and #3.

Step #2 turns the aircraft (max characteristic dimension, max
speed, mass) and the overflown population density into the
intrinsic Ground Risk Class (iGRC, Table 2). Step #3 applies the
ground risk mitigations (Table 5) to reach the final GRC.
"""

from __future__ import annotations

from .tables import (
    DENSITY_DESCRIPTORS,
    IGRC_COLUMNS,
    IGRC_DENSITY_BOUNDS,
    IGRC_TABLE,
    M1_COMBINED_CAP,
    MITIGATION_CREDITS,
    MITIGATION_TITLES,
)

ROBUSTNESS_LEVELS = ("none", "low", "medium", "high")

# A UA of 250 g or less, at 25 m/s or less, has iGRC 1 regardless
# of population density (Table 2 note, SORA 2.5 section 4.2.3).
LIGHT_UA_MASS_KG = 0.25
LIGHT_UA_SPEED_M_S = 25.0


class OutOfSoraError(ValueError):
    """The operation has no SORA class: it belongs in the certified
    category (or needs the Annex F quantitative method)."""


def _column_for(dimension_m: float, max_speed_m_s: float) -> int:
    """Leftmost Table 2 column matching both dimension and speed.

    The column must cover the dimension and the speed, so the
    column index is the larger of the two single-criterion picks.
    """
    if dimension_m <= 0:
        raise ValueError("characteristic dimension must be positive")
    if max_speed_m_s <= 0:
        raise ValueError("maximum speed must be positive")
    dim_col = None
    speed_col = None
    for index, (max_dim, max_speed) in enumerate(IGRC_COLUMNS):
        if dim_col is None and dimension_m <= max_dim:
            dim_col = index
        if speed_col is None and max_speed_m_s <= max_speed:
            speed_col = index
    if dim_col is None:
        raise OutOfSoraError(
            f"characteristic dimension {dimension_m} m exceeds the "
            "40 m Table 2 column; calculate the iGRC per Annex F"
        )
    if speed_col is None:
        raise OutOfSoraError(
            f"maximum speed {max_speed_m_s} m/s exceeds the 200 m/s "
            "Table 2 column; the operation is outside SORA"
        )
    return max(dim_col, speed_col)


def density_band(density_per_km2: float) -> int:
    """Table 2 row index for a population density.

    Row 0 is the controlled ground area (density 0). Otherwise the
    row is the first band whose upper bound the density is strictly
    below, so a density exactly on a boundary takes the next band
    up, matching the "less than" wording of Table 2.
    """
    if density_per_km2 < 0:
        raise ValueError("population density cannot be negative")
    if density_per_km2 == 0:
        return 0
    for index, bound in enumerate(IGRC_DENSITY_BOUNDS, start=1):
        if density_per_km2 < bound:
            return index
    return len(IGRC_DENSITY_BOUNDS) + 1


def density_band_for_descriptor(descriptor: str) -> int:
    """Table 2 row index for a Table 3 qualitative descriptor."""
    key = descriptor.strip().lower()
    if key not in DENSITY_DESCRIPTORS:
        known = ", ".join(sorted(DENSITY_DESCRIPTORS))
        raise ValueError(
            f"unknown population descriptor {descriptor!r}; known "
            f"descriptors: {known}"
        )
    return DENSITY_DESCRIPTORS[key]


def intrinsic_grc(
    dimension_m: float,
    max_speed_m_s: float,
    density_per_km2: float | None = None,
    *,
    descriptor: str | None = None,
    mass_kg: float | None = None,
    controlled_ground_area: bool = False,
) -> int:
    """Intrinsic Ground Risk Class, SORA 2.5 Table 2.

    Give either a numeric density or a Table 3 descriptor, not
    both. Set controlled_ground_area for an area where only
    involved persons are present. The 250 g / 25 m/s shortcut
    applies when mass_kg is given.
    """
    if (density_per_km2 is None) == (descriptor is None):
        raise ValueError(
            "give exactly one of density_per_km2 or descriptor"
        )
    if controlled_ground_area:
        row = 0
    elif descriptor is not None:
        row = density_band_for_descriptor(descriptor)
    else:
        row = density_band(density_per_km2)  # type: ignore[arg-type]
    if (
        mass_kg is not None
        and mass_kg <= LIGHT_UA_MASS_KG
        and max_speed_m_s <= LIGHT_UA_SPEED_M_S
    ):
        return 1
    column = _column_for(dimension_m, max_speed_m_s)
    value = IGRC_TABLE[row][column]
    if value is None:
        raise OutOfSoraError(
            "no iGRC for this aircraft over this population density; "
            "the operation is outside SORA (certified category)"
        )
    return value


def _mitigation_credit(mitigation: str, robustness: str) -> int:
    """Table 5 credit for one mitigation at one robustness level."""
    level = robustness.strip().lower()
    if level not in ROBUSTNESS_LEVELS:
        raise ValueError(
            f"unknown robustness {robustness!r} for {mitigation}; "
            f"use one of: {', '.join(ROBUSTNESS_LEVELS)}"
        )
    if level == "none":
        return 0
    credit = MITIGATION_CREDITS[mitigation][level]
    if credit is None:
        raise ValueError(
            f"{MITIGATION_TITLES[mitigation]} is not available at "
            f"{level} robustness (Table 5)"
        )
    return credit


def final_grc(
    igrc: int,
    dimension_m: float,
    max_speed_m_s: float,
    mitigations: dict[str, str] | None = None,
) -> tuple[int, dict[str, int]]:
    """Final Ground Risk Class, SORA 2.5 Step #3 (Table 5).

    Returns (final GRC, applied credits by mitigation). The
    mitigations map uses keys m1a, m1b, m1c, m2 with robustness
    values none/low/medium/high. Applied in numerical sequence
    (M1(A), M1(B), M1(C), then M2). The combined M1 credit is
    capped at 3, and M1 credits cannot take the GRC below the
    controlled-ground-area value of the applicable Table 2 column.
    M2 (impact dynamics) applies after that floor. The result is
    at least 1; a result above 7 means the certified category.
    """
    if igrc < 1 or igrc > 10:
        raise ValueError("iGRC must be between 1 and 10")
    applied: dict[str, int] = {}
    claimed = dict(mitigations or {})
    unknown = sorted(set(claimed) - set(MITIGATION_CREDITS))
    if unknown:
        raise ValueError(f"unknown mitigations: {', '.join(unknown)}")
    for key in ("m1a", "m1b", "m1c"):
        applied[key] = _mitigation_credit(key, claimed.get(key, "none"))
    m1_total = applied["m1a"] + applied["m1b"] + applied["m1c"]
    if m1_total < -M1_COMBINED_CAP:
        m1_total = -M1_COMBINED_CAP
    column = _column_for(dimension_m, max_speed_m_s)
    floor = IGRC_TABLE[0][column]
    after_m1 = max(igrc + m1_total, floor)
    applied["m2"] = _mitigation_credit("m2", claimed.get("m2", "none"))
    result = max(after_m1 + applied["m2"], 1)
    return result, applied

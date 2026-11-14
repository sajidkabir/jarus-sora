"""Published SORA 2.5 tables, as data.

Every table here is transcribed from JARUS SORA Main Body 2.5
(JAR-doc-25, edition 13.05.2024), the document EASA adopted as the
acceptable means of compliance to Article 11 of Regulation (EU)
2019/947 through ED Decision 2025/018/R. Table numbers below are
the JARUS table numbers. Nothing is invented: a cell that the
source leaves blank (an operation outside SORA) is None.

Two values come from named secondary sources, and are marked so:
the combined M1 credit cap of 3 (Eng. Proc. 2025, 90, 47, a
peer-reviewed comparison of SORA 2.0 and 2.5) and the 250 g
assemblies note (see GROUND_NOTES). Both are flagged in the README
as items to confirm against Annex B for a formal application.
"""

# Table 2: Intrinsic Ground Risk Class (iGRC) determination.
# Columns are (max characteristic dimension in metres, max speed
# in m/s). Rows are population density bands in people per km2.
# A row label of None means the controlled ground area row.
# Values are the iGRC; None means the cell is outside SORA
# (the operation belongs in the certified category).
IGRC_COLUMNS = (
    (1.0, 25.0),
    (3.0, 35.0),
    (8.0, 75.0),
    (20.0, 120.0),
    (40.0, 200.0),
)

# Row order: controlled ground area, then upper bounds 5, 50, 500,
# 5000, 50000 people/km2, then above 50000.
IGRC_DENSITY_BOUNDS = (5.0, 50.0, 500.0, 5000.0, 50000.0)

IGRC_TABLE = (
    # Controlled ground area
    (1, 1, 2, 3, 3),
    # < 5 people/km2
    (2, 3, 4, 5, 6),
    # < 50 people/km2
    (3, 4, 5, 6, 7),
    # < 500 people/km2
    (4, 5, 6, 7, 8),
    # < 5000 people/km2
    (5, 6, 7, 8, 9),
    # < 50000 people/km2
    (6, 7, 8, 9, 10),
    # > 50000 people/km2 (assemblies of people)
    (7, 8, None, None, None),
)

# Table 3: qualitative descriptors for population density
# estimation. Each descriptor maps to a Table 2 row index.
DENSITY_DESCRIPTORS = {
    "controlled": 0,
    "extremely remote": 0,
    "remote": 1,
    "lightly populated": 2,
    "sparsely populated": 2,
    "residential lightly populated": 3,
    "low density metropolitan": 4,
    "high density metropolitan": 5,
    "assemblies of people": 6,
}

# Table 5: mitigations for final GRC determination. Values are the
# GRC credit (negative) at each robustness level; None means the
# level is not available for that mitigation.
MITIGATION_CREDITS = {
    "m1a": {"low": -1, "medium": -2, "high": None},
    "m1b": {"low": None, "medium": -1, "high": -2},
    "m1c": {"low": -1, "medium": None, "high": None},
    "m2": {"low": None, "medium": -1, "high": -2},
}

MITIGATION_TITLES = {
    "m1a": "M1(A) - Strategic mitigations - Sheltering",
    "m1b": "M1(B) - Strategic mitigations - Operational restrictions",
    "m1c": "M1(C) - Tactical mitigations - Ground observation",
    "m2": "M2 - Effects of UA impact dynamics are reduced",
}

# Combined M1 credit cap. Source: Eng. Proc. 2025, 90, 47
# ("The maximum reduction in GRC by M1 mitigations is now 3
# instead of 4"). The Main Body states the floor rule below;
# confirm the cap against Annex B for a formal application.
M1_COMBINED_CAP = 3

# Table 6: Tactical Mitigation Performance Requirement (TMPR) and
# TMPR level of robustness, by residual ARC.
TMPR_TABLE = {
    "a": ("No requirement", "No requirement"),
    "b": ("Low", "Low"),
    "c": ("Medium", "Medium"),
    "d": ("High", "High"),
}

# Table 7: SAIL determination. Rows are final GRC bands, columns
# are residual ARC a, b, c, d. "CERTIFIED" means the operation is
# outside SORA and belongs in the certified category.
SAIL_TABLE = (
    # Final GRC <= 2
    ("I", "II", "IV", "VI"),
    # Final GRC 3
    ("II", "II", "IV", "VI"),
    # Final GRC 4
    ("III", "III", "IV", "VI"),
    # Final GRC 5
    ("IV", "IV", "IV", "VI"),
    # Final GRC 6
    ("V", "V", "V", "VI"),
    # Final GRC 7
    ("VI", "VI", "VI", "VI"),
    # Final GRC > 7
    ("CERTIFIED", "CERTIFIED", "CERTIFIED", "CERTIFIED"),
)

SAIL_LEVELS = ("I", "II", "III", "IV", "V", "VI")

# Table 14: recommended Operational Safety Objectives (OSO).
# Each entry is (id, title, robustness by SAIL I..VI) where
# robustness is "NR" (not required), "L", "M", or "H".
# OSO numbers with no row in Table 14 (10, 11, 12, 14, 15, 21, 22)
# are not part of the SORA 2.5 consolidated list.
OSO_TABLE = (
    ("OSO#01", "Ensure the Operator is competent and/or proven",
     ("NR", "L", "M", "H", "H", "H")),
    ("OSO#02", "UAS manufactured by competent and/or proven entity",
     ("NR", "NR", "L", "M", "H", "H")),
    ("OSO#03", "UAS maintained by competent and/or proven entity",
     ("L", "L", "M", "M", "H", "H")),
    ("OSO#04", "UAS components essential to safe operations are "
     "designed to an Airworthiness Design Standard (ADS)",
     ("NR", "NR", "NR", "L", "M", "H")),
    ("OSO#05", "UAS is designed considering system safety and "
     "reliability",
     ("NR", "NR", "L", "M", "H", "H")),
    ("OSO#06", "C3 link characteristics are appropriate for the "
     "operation",
     ("NR", "L", "L", "M", "H", "H")),
    ("OSO#07", "Conformity check of the UAS configuration",
     ("L", "L", "M", "M", "H", "H")),
    ("OSO#08", "Operational procedures are defined, validated and "
     "adhered to",
     ("L", "M", "H", "H", "H", "H")),
    ("OSO#09", "Remote crew trained and current",
     ("L", "L", "M", "M", "H", "H")),
    ("OSO#13", "External services supporting UAS operations are "
     "adequate to the operation",
     ("L", "L", "M", "H", "H", "H")),
    ("OSO#16", "Multi crew coordination",
     ("L", "L", "M", "M", "H", "H")),
    ("OSO#17", "Remote crew is fit to operate",
     ("L", "L", "M", "M", "H", "H")),
    ("OSO#18", "Automatic protection of the flight envelope from "
     "human errors",
     ("NR", "NR", "L", "M", "H", "H")),
    ("OSO#19", "Safe recovery from human error",
     ("NR", "NR", "L", "M", "M", "H")),
    ("OSO#20", "A Human Factors evaluation has been performed and "
     "the HMI found appropriate for the mission",
     ("NR", "L", "L", "M", "M", "H")),
    ("OSO#23", "Environmental conditions for safe operations "
     "defined, measurable and adhered to",
     ("L", "L", "M", "M", "H", "H")),
    ("OSO#24", "UAS designed and qualified for adverse "
     "environmental conditions",
     ("NR", "NR", "M", "H", "H", "H")),
)

# OSO#05 at SAIL II is "NR" with footnote (c): where the UAS
# employs novel or complex features with very limited operational
# experience, the competent authority may still require it.
# The note is keyed by (OSO id, SAIL) and shown only there.
OSO_NOTES = {
    ("OSO#05", "II"): "At SAIL II this objective is not required, "
    "unless the UAS employs novel or complex features with very "
    "limited operational experience (SORA 2.5 Table 14 footnote c).",
}

# Step #8: adjacent area size. The lateral outer limit of the
# adjacent area is the distance flown in 3 minutes at maximum
# speed, clamped to 5 km at the low end and 35 km at the high end.
ADJACENT_AREA_MIN_KM = 5.0
ADJACENT_AREA_MAX_KM = 35.0
ADJACENT_AREA_MINUTES = 3.0

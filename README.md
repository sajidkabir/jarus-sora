# jarus-sora

[![CI](https://github.com/sajidkabir/jarus-sora/actions/workflows/ci.yml/badge.svg)](https://github.com/sajidkabir/jarus-sora/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)

JARUS SORA 2.5 risk assessment in Python: the Specific Operations
Risk Assessment as a library and a command line tool. Give it a
Concept of Operations and it returns the intrinsic and final Ground
Risk Class, the residual Air Risk Class, the Tactical Mitigation
Performance Requirement, the SAIL, and the Operational Safety
Objectives with their required robustness. Pure standard library,
no dependencies, installable from this repo.

## Why this exists

Every drone operation in the Specific category in Europe needs a
SORA before the authority will authorise it, and the SORA is a
ten-step paper exercise most small operators still do by hand in
spreadsheets or pay a consultant to do. The existing tooling is
not scriptable Python:

- DROSERA (ONERA) computes ground-risk indexes for SORA, but it
  is proprietary commercial software under an ONERA licence.
- Jarus.Sora_v2.5 is a .NET library (GPL-3.0) on NuGet, not Python.
- UK SORA (uksora.co.uk) is a web tool in beta, opened one account
  at a time, and it implements the UK variant (CAP 3017).
- An academic web tool (ScienceDirect, 2025) guides applicants
  through the steps but is a website, not a library.
- On PyPI, `sora` is an unrelated 2019 image-display library, and
  no SORA package exists at all.

There is no pip-installable, MIT-licensed, tested Python
implementation of the SORA 2.5 tables. This package is that: the
tables as data, the pipeline as functions, and a CLI, so a mission
planner, a CI check, or an operator's own script can compute a
SAIL instead of looking it up by hand.

## Install

```bash
git clone https://github.com/sajidkabir/jarus-sora.git
cd jarus-sora
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Use

One operation, start to finish:

```text
$ jarus-sora sail --dimension 2.5 --speed 30 --density 40 --m1a medium --m2 medium --arc c
Intrinsic GRC: 4
Mitigation credits: m1a -2, m2 -1
Final GRC: 1
Initial ARC: c, residual ARC: c
SAIL: IV
```

That is a 2.5 m, 30 m/s quadrotor over 40 people/km2, with medium
sheltering and a medium parachute, in ARC-c airspace, BVLOS.

A full assessment from a ConOps file:

```bash
jarus-sora assess --conops examples/rural_survey.json
jarus-sora assess --conops examples/rural_survey.json --format json
```

The ConOps JSON carries the operation: aircraft size, speed and
mass, the population density (or a Table 3 descriptor), the
mitigations claimed, the initial ARC, and VLOS or BVLOS. The text
report lists every step, the TMPR, the SAIL, and all 17 OSOs with
their required robustness. The JSON form is for pipelines.

Single steps, for checking one number:

```bash
jarus-sora igrc --dimension 2.5 --speed 30 --density 40
jarus-sora igrc --dimension 3 --speed 35 --descriptor "sparsely populated"
jarus-sora osos --sail III
jarus-sora tables
```

Python API:

```python
from jarus_sora import ConOps, assess

result = assess(ConOps(
    dimension_m=2.5, max_speed_m_s=30.0, mass_kg=4.0,
    density_per_km2=40.0,
    mitigations={"m1a": "medium", "m2": "medium"},
    initial_arc="c", vlos=False,
))
result.sail          # 'IV'
result.final_grc_value  # 1
result.tmpr          # 'Medium'
```

## What it computes

| Step | Output | Source |
| --- | --- | --- |
| #2 | Intrinsic GRC (iGRC) | Table 2 |
| #3 | Final GRC | Table 5 |
| #5 | Residual ARC | Step #5 VLOS rule |
| #6 | TMPR and its robustness | Table 6 |
| #7 | SAIL I-VI (or certified) | Table 7 |
| #8 | Adjacent-area radius | Step #8 formula |
| #9 | 17 OSOs with robustness | Table 14 |

Rules applied, exactly as published:

- Table 2 column: the leftmost column matching both the
  characteristic dimension and the maximum speed. A UA over 40 m
  or over 200 m/s has no column and is outside SORA.
- A UA of 250 g or less at 25 m/s or less has iGRC 1 regardless
  of population density.
- Population density bands are "less than": a density exactly on
  a boundary takes the next band up. A Table 3 descriptor
  (controlled, remote, sparsely populated, and the rest) may be
  used instead of a number.
- Mitigation credits: M1(A) low -1 / medium -2, M1(B) medium -1 /
  high -2, M1(C) low -1, M2 medium -1 / high -2. A level the table
  does not offer is rejected, not silently ignored.
- The combined M1 credit is capped at -3 (Eng. Proc. 2025, 90,
  47). M1 credits cannot take the GRC below the controlled-area
  value of the applicable Table 2 column; M2 applies after that
  floor. The result is at least 1, and above 7 means the certified
  category.
- VLOS (or an airspace observer alongside the pilot) reduces the
  initial ARC by one class, but never to ARC-a, so ARC-b stays
  ARC-b.
- Adjacent-area radius is the distance flown in 3 minutes at
  maximum speed, clamped to 5-35 km. For the 2.5 m, 30 m/s
  aircraft in the SORA worked example this gives 5.4 km, matching
  the document.

## Honest scope

- The initial ARC is an operator input. SORA assigns it from the
  Figure 6 decision tree, which is a figure in the source
  document, not a table; this release does not guess the tree.
  Determine the initial ARC from Figure 6 (or from an airspace
  collision risk map from your authority, ANSP, or UTM provider)
  and pass it in.
- Containment requirements (Tables 8-13, Step #8) are not in this
  release; only the adjacent-area size formula is. They are the
  next roadmap item.
- The combined M1 cap of 3 comes from a peer-reviewed comparison
  of SORA 2.0 and 2.5; confirm it against Annex B for a formal
  application, and open an issue if the AMC says otherwise.
- UK SORA (CAP 3017) adapts these tables for the UK; this package
  implements JARUS SORA 2.5 as EASA adopted it, not the UK variant.
- This is a calculation aid, not an authorisation and not legal
  advice. Only the competent authority decides. If a table value
  disagrees with the current AMC to Regulation (EU) 2019/947, the
  AMC wins.

## Validation

The test suite pins the full Table 2 (all 35 cells) and the full
Table 7 (all 28 cells) against the published tables, checks OSO
robustness counts per SAIL, and runs three hand-computed worked
operations end to end. The 5.4 km adjacent-area radius reproduces
the SORA worked example for the same aircraft.

## Sources

- JARUS SORA Main Body 2.5, JAR-doc-25, edition 13.05.2024
  (Tables 2-7, 14; Steps #2-#9).
- EASA AMC and GM to Regulation (EU) 2019/947, Issue 1
  Amendment 3, Annex to ED Decision 2025/018/R (SORA 2.5 as the
  AMC to Article 11).
- Eng. Proc. 2025, 90, 47: parametric comparison of SORA 2.0 and
  2.5 ground risk models (M1 combined cap).

# Changelog

All notable changes to this project are documented here. The format
follows [Keep a Changelog](https://keepachangelog.com/), and versions
follow [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-11-09

### Added

- Full SORA 2.5 pipeline (JAR-doc-25, May 2024) from one Concept of
  Operations: intrinsic GRC (Table 2), final GRC with M1(A)/M1(B)/
  M1(C)/M2 mitigations (Table 5), residual ARC with the VLOS
  one-class reduction (Step #5), TMPR (Table 6), SAIL (Table 7),
  and the 17 Operational Safety Objectives with required robustness
  (Table 14).
- `intrinsic_grc` with the 250 g / 25 m/s shortcut, Table 3
  qualitative population descriptors, and the controlled ground
  area row. Operations with no Table 2 cell raise `OutOfSoraError`
  (certified category) instead of returning a made-up number.
- Final GRC rules as published: combined M1 credit capped at 3,
  M1 credits cannot take the GRC below the controlled-area value
  of the applicable Table 2 column, M2 applies after that floor,
  result at least 1 and above 7 means the certified category.
- Step #8 adjacent-area radius: distance flown in 3 minutes at
  maximum speed, clamped to 5-35 km (matches the 5.4 km value in
  the SORA worked example for a 2.5 m, 30 m/s aircraft).
- CLI `jarus-sora` with subcommands `assess` (ConOps JSON in,
  text or JSON report out), `igrc`, `sail`, `osos`, and `tables`.
- Test suite of 103 checks, including the full Table 2 (all 35
  cells) and the full Table 7 (all 28 cells) pinned against the
  published tables, OSO robustness counts per SAIL, and three
  hand-computed worked operations.
- Example ConOps JSON and example script.

## Roadmap

- Containment requirements, Tables 8-13 (Step #8).
- Annex F quantitative iGRC model for aircraft whose dimension
  and speed point at different columns, and for UA above 40 m.
- ARC assignment from the Figure 6 decision tree, once a text
  form of the tree is published; the initial ARC stays an operator
  input until then.
- UK SORA (CAP 3017) variant tables, where they differ from JARUS.

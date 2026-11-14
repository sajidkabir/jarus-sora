"""Command line interface: jarus-sora assess, igrc, sail, osos, tables.

Every subcommand prints plain numbers an operator can check
against the JARUS tables, and exits with status 2 (argparse) or
1 (a bad value, or an operation outside SORA) on bad input.
"""

from __future__ import annotations

import argparse
import json
import sys

from .air import ARC_TITLES, residual_arc, tmpr_for_arc
from .assessment import (
    ConOps,
    assess,
    assessment_report,
)
from .ground import (
    OutOfSoraError,
    final_grc,
    intrinsic_grc,
)
from .sail import osos_for_sail, sail_for
from .tables import (
    IGRC_COLUMNS,
    IGRC_TABLE,
    MITIGATION_CREDITS,
    OSO_TABLE,
    SAIL_TABLE,
)


def _fail(message: str) -> int:
    print(f"jarus-sora: {message}", file=sys.stderr)
    return 1


def _robustness(value: str | None) -> str:
    return (value or "none").strip().lower()


def _mitigations(args: argparse.Namespace) -> dict[str, str]:
    return {
        "m1a": _robustness(args.m1a),
        "m1b": _robustness(args.m1b),
        "m1c": _robustness(args.m1c),
        "m2": _robustness(args.m2),
    }


def _add_ground_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dimension", type=float, required=True,
                        help="max characteristic dimension, metres")
    parser.add_argument("--speed", type=float, required=True,
                        help="max possible commanded airspeed, m/s")
    parser.add_argument("--mass-kg", type=float, default=None,
                        help="UA mass in kg (for the 250 g shortcut)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--density", type=float,
                       help="max population density, people/km2")
    group.add_argument("--descriptor",
                       help="Table 3 descriptor, e.g. 'sparsely populated'")
    parser.add_argument("--controlled", action="store_true",
                        help="controlled ground area (involved persons only)")


def _add_mitigation_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--m1a", default="none",
                        help="M1(A) sheltering robustness: none/low/medium")
    parser.add_argument("--m1b", default="none",
                        help="M1(B) operational restrictions: none/medium/high")
    parser.add_argument("--m1c", default="none",
                        help="M1(C) ground observation: none/low")
    parser.add_argument("--m2", default="none",
                        help="M2 impact dynamics: none/medium/high")


def cmd_igrc(args: argparse.Namespace) -> int:
    try:
        value = intrinsic_grc(
            args.dimension, args.speed, args.density,
            descriptor=args.descriptor,
            mass_kg=args.mass_kg,
            controlled_ground_area=args.controlled,
        )
    except (ValueError, OutOfSoraError) as exc:
        return _fail(str(exc))
    print(f"Intrinsic GRC (iGRC): {value}")
    return 0


def cmd_sail(args: argparse.Namespace) -> int:
    try:
        igrc = intrinsic_grc(
            args.dimension, args.speed, args.density,
            descriptor=args.descriptor,
            mass_kg=args.mass_kg,
            controlled_ground_area=args.controlled,
        )
        final, credits = final_grc(
            igrc, args.dimension, args.speed, _mitigations(args)
        )
        residual = residual_arc(args.arc, vlos=args.vlos)
        sail = sail_for(final, residual)
    except (ValueError, OutOfSoraError) as exc:
        return _fail(str(exc))
    print(f"Intrinsic GRC: {igrc}")
    applied = ", ".join(
        f"{key} {value:+d}" for key, value in credits.items()
        if value != 0
    )
    print(f"Mitigation credits: {applied or 'none claimed'}")
    print(f"Final GRC: {final}")
    print(f"Initial ARC: {args.arc.lower()}, residual ARC: {residual}")
    print(f"SAIL: {sail}")
    return 0


def cmd_osos(args: argparse.Namespace) -> int:
    try:
        rows = osos_for_sail(args.sail.upper())
    except ValueError as exc:
        return _fail(str(exc))
    print(f"Operational Safety Objectives for SAIL {args.sail.upper()}:")
    for row in rows:
        print(f"  {row['id']} [{row['robustness']}] {row['title']}")
        if row["note"]:
            print(f"    Note: {row['note']}")
    return 0


def _conops_from_json(data: dict) -> ConOps:
    if not isinstance(data, dict):
        raise ValueError("conops file must contain one JSON object")
    return ConOps(
        dimension_m=float(data["dimension_m"]),
        max_speed_m_s=float(data["max_speed_m_s"]),
        mass_kg=data.get("mass_kg"),
        density_per_km2=data.get("density_per_km2"),
        descriptor=data.get("descriptor"),
        controlled_ground_area=bool(
            data.get("controlled_ground_area", False)
        ),
        mitigations={
            key: str(value)
            for key, value in data.get("mitigations", {}).items()
        },
        initial_arc=str(data.get("initial_arc", "b")),
        vlos=bool(data.get("vlos", False)),
    )


def cmd_assess(args: argparse.Namespace) -> int:
    try:
        with open(args.conops, encoding="utf-8") as handle:
            data = json.load(handle)
        result = assess(_conops_from_json(data))
    except FileNotFoundError:
        return _fail(f"no such file: {args.conops}")
    except (ValueError, OutOfSoraError, KeyError, TypeError) as exc:
        return _fail(str(exc))
    if args.format == "json":
        payload = {
            "igrc": result.igrc,
            "final_grc": result.final_grc_value,
            "mitigation_credits": result.mitigation_credits,
            "initial_arc": result.initial_arc,
            "residual_arc": result.residual_arc_value,
            "tmpr": result.tmpr,
            "tmpr_robustness": result.tmpr_robustness,
            "sail": result.sail,
            "certified": result.certified,
            "adjacent_area_radius_km": round(
                result.adjacent_area_radius_km, 2
            ),
            "osos": [
                {
                    "id": oso["id"],
                    "title": oso["title"],
                    "robustness": oso["robustness"],
                }
                for oso in result.osos
            ],
            "notes": list(result.notes),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(assessment_report(result))
    return 0


def cmd_tables(_args: argparse.Namespace) -> int:
    print("Table 2 - Intrinsic Ground Risk Class (iGRC)")
    header = "density  " + "  ".join(
        f"{dim:g}m/{speed:g}m/s" for dim, speed in IGRC_COLUMNS
    )
    print(header)
    labels = (
        "controlled", "<5", "<50", "<500", "<5000", "<50000", ">50000",
    )
    for label, row in zip(labels, IGRC_TABLE):
        cells = "  ".join(
            f"{value}" if value is not None else "outside SORA"
            for value in row
        )
        print(f"{label:>10}  {cells}")
    print()
    print("Table 5 - Mitigations for final GRC (credit by robustness)")
    for key, levels in MITIGATION_CREDITS.items():
        print(
            f"  {key}: low {levels['low']}, medium "
            f"{levels['medium']}, high {levels['high']}"
        )
    print("  Combined M1 credit capped at -3; M1 cannot take the "
          "GRC below the controlled-area value of its column.")
    print()
    print("Table 6 - TMPR by residual ARC: a none, b low, "
          "c medium, d high")
    print()
    print("Table 7 - SAIL (rows final GRC, columns residual ARC)")
    for row_label, row in zip(
        ("<=2", "3", "4", "5", "6", "7", ">7"), SAIL_TABLE
    ):
        print(f"  {row_label:>3}  " + "  ".join(row))
    print()
    print("Table 14 - OSO robustness by SAIL I..VI "
          "(NR = not required)")
    for oso_id, title, levels in OSO_TABLE:
        print(f"  {oso_id}  {' '.join(levels)}  {title}")
    print()
    print("ARC classes:")
    for letter, text in ARC_TITLES.items():
        print(f"  {letter}: {text}")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="jarus-sora",
        description="JARUS SORA 2.5 risk assessment: GRC, ARC, "
        "TMPR, SAIL, and OSOs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    igrc = sub.add_parser("igrc", help="intrinsic GRC for an aircraft and area")
    _add_ground_args(igrc)

    sail = sub.add_parser("sail", help="iGRC, final GRC, residual ARC, SAIL")
    _add_ground_args(sail)
    _add_mitigation_args(sail)
    sail.add_argument("--arc", default="b",
                      help="initial ARC a/b/c/d (default b)")
    sail.add_argument("--vlos", action="store_true",
                      help="VLOS (or observer alongside pilot)")

    osos = sub.add_parser("osos", help="OSO robustness for a SAIL")
    osos.add_argument("--sail", required=True, help="SAIL I..VI")

    assess_p = sub.add_parser("assess", help="full assessment from a ConOps JSON file")
    assess_p.add_argument("--conops", required=True,
                          help="JSON file with the Concept of Operations")
    assess_p.add_argument("--format", choices=("text", "json"),
                          default="text")

    sub.add_parser("tables", help="print the SORA tables used")

    args = parser.parse_args(argv)
    if args.command == "igrc":
        raise SystemExit(cmd_igrc(args))
    if args.command == "sail":
        raise SystemExit(cmd_sail(args))
    if args.command == "osos":
        raise SystemExit(cmd_osos(args))
    if args.command == "assess":
        raise SystemExit(cmd_assess(args))
    if args.command == "tables":
        raise SystemExit(cmd_tables(args))


if __name__ == "__main__":
    main()

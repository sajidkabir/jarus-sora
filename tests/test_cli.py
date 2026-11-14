"""CLI tests: subcommands, JSON output, and bad-input exits."""

import json

import pytest

from jarus_sora.cli import main


def _run(argv):
    with pytest.raises(SystemExit) as caught:
        main(argv)
    return caught.value.code


def test_cli_igrc(capsys):
    assert _run(["igrc", "--dimension", "2.5", "--speed", "30",
                 "--density", "40"]) == 0
    assert "Intrinsic GRC (iGRC): 4" in capsys.readouterr().out


def test_cli_igrc_with_descriptor(capsys):
    assert _run(["igrc", "--dimension", "3", "--speed", "35",
                 "--descriptor", "remote"]) == 0
    assert "Intrinsic GRC (iGRC): 3" in capsys.readouterr().out


def test_cli_sail_full_path(capsys):
    code = _run([
        "sail", "--dimension", "1.8", "--speed", "25",
        "--density", "1200", "--m1a", "low", "--m1b", "medium",
        "--m1c", "low", "--arc", "b", "--vlos",
    ])
    assert code == 0
    out = capsys.readouterr().out
    assert "Intrinsic GRC: 6" in out
    assert "Final GRC: 3" in out
    assert "SAIL: II" in out


def test_cli_osos(capsys):
    assert _run(["osos", "--sail", "III"]) == 0
    out = capsys.readouterr().out
    assert "OSO#08 [H]" in out
    assert "OSO#04 [NR]" in out


def test_cli_assess_text_and_json(tmp_path, capsys):
    conops = {
        "dimension_m": 2.5,
        "max_speed_m_s": 30.0,
        "mass_kg": 4.0,
        "density_per_km2": 40.0,
        "mitigations": {"m1a": "medium", "m2": "medium"},
        "initial_arc": "c",
        "vlos": False,
    }
    path = tmp_path / "conops.json"
    path.write_text(json.dumps(conops))
    assert _run(["assess", "--conops", str(path)]) == 0
    out = capsys.readouterr().out
    assert "SAIL: IV" in out
    assert _run(["assess", "--conops", str(path), "--format", "json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["igrc"] == 4
    assert payload["final_grc"] == 1
    assert payload["sail"] == "IV"
    assert payload["tmpr"] == "Medium"
    assert payload["adjacent_area_radius_km"] == 5.4
    assert len(payload["osos"]) == 17


def test_cli_tables(capsys):
    assert _run(["tables"]) == 0
    out = capsys.readouterr().out
    assert "Table 2" in out
    assert "Table 7" in out
    assert "OSO#01" in out


def test_cli_bad_inputs_exit_1(capsys):
    # Out-of-SORA operation.
    assert _run(["igrc", "--dimension", "8", "--speed", "75",
                 "--density", "60000"]) == 1
    # Mitigation level the table does not offer.
    assert _run(["sail", "--dimension", "3", "--speed", "35",
                 "--density", "40", "--m1a", "high"]) == 1
    # Unknown SAIL.
    assert _run(["osos", "--sail", "VII"]) == 1
    # Missing file.
    assert _run(["assess", "--conops", "no-such-file.json"]) == 1
    assert "jarus-sora:" in capsys.readouterr().err

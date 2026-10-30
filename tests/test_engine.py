import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import zipfile
from dataclasses import replace
from pathlib import Path

import pytest
from conftest import row, write_zip
from official_support import official_config
from tse_importer.discovery import BoundedReader, inventory, member_stream
from tse_importer.domain import Config, ImportFailure, Limits, Selection, StoragePolicy
from tse_importer.engine import run_import, validate_release
from tse_importer.integrity import checksum_line, hashes, verify
from tse_importer.parsers import SCHEMAS, inspect_member, parse
from tse_importer.validation import validate_database
from votoaberto_auditor.cli import main


def config(root, tmp_path, **kwargs):
    return Config(root, tmp_path / "processed", data_kind="synthetic", **kwargs)


def test_inventory_and_hashes(source_set):
    result = inventory(source_set)
    assert len(result["files"]) == 2
    for item in result["files"]:
        assert item["status"] == "ok"
        assert item["member_count"] == 1
        data = (source_set / item["path"]).read_bytes()
        assert item["hashes"]["sha256"] == hashlib.sha256(data).hexdigest()
        assert item["hashes"]["sha512"] == hashlib.sha512(data).hexdigest()
        assert item["verification"]["status"] == "unverified"
    assert inventory(source_set) == result


def test_empty_corrupt_missing(tmp_path):
    assert inventory(tmp_path)["files"] == []
    (tmp_path / "bad.zip").write_bytes(b"broken")
    assert inventory(tmp_path)["files"][0]["status"] == "error"
    with pytest.raises(ImportFailure):
        inventory(tmp_path / "missing")


@pytest.mark.parametrize(
    "name",
    ["../escape.csv", "/absolute.csv", "C:\\escape.csv", "a/../../b.csv", "x.zip", "a:stream.csv"],
)
def test_unsafe_names(tmp_path, name):
    path = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(name, "unsafe")
    assert inventory(tmp_path)["files"][0]["status"] == "unsafe"
    with pytest.raises(ImportFailure):
        with member_stream(path, name, Limits()):
            pass
    assert not (tmp_path.parent / "escape.csv").exists()


def test_duplicate_member_bomb_and_limits(tmp_path):
    with zipfile.ZipFile(tmp_path / "duplicate.zip", "w") as z:
        z.writestr("a.csv", "one")
        with pytest.warns(UserWarning):
            z.writestr("a.csv", "two")
    item = inventory(tmp_path)["files"][0]
    assert "duplicate_member" in item["members"][0]["issues"]
    with zipfile.ZipFile(tmp_path / "bomb.zip", "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("x.csv", b"0" * 100000)
    assert inventory(tmp_path)["files"][0]["status"] == "unsafe"
    assert inventory(tmp_path, Limits(max_members=1))["files"][1]["status"] == "error"
    assert inventory(tmp_path, Limits(max_member_bytes=1))["files"][0]["status"] == "unsafe"
    assert inventory(tmp_path, Limits(max_total_bytes=1))["files"][0]["issues"] == [
        "total_size_limit"
    ]


def test_runtime_limit():
    import io
    import random

    reader = io.BufferedReader(BoundedReader(io.BytesIO(random.Random(1).randbytes(100)), 20))
    with pytest.raises(ImportFailure, match="bytes"):
        reader.read()


def test_hash_reference(tmp_path):
    path = tmp_path / "test.zip"
    path.write_bytes(b"test")
    calculated = hashes(path)
    assert verify(path, calculated)["status"] == "unverified"
    for algorithm in ("sha256", "sha512"):
        ref = {
            "algorithm": algorithm,
            "digest": calculated[algorithm],
            "origin": "https://example.invalid/test",
            "trusted": True,
        }
        assert verify(path, calculated, ref)["status"] == "verified"
        assert (
            verify(path, calculated, {**ref, "digest": "0" * len(ref["digest"])})["status"]
            == "mismatch"
        )
    side = Path(str(path) + ".sha512")
    side.write_text(calculated["sha512"] + "  test.zip\n")
    assert verify(path, calculated)["matches"]
    assert verify(path, calculated)["status"] == "unverified"
    side.write_text("bad")
    assert verify(path, calculated)["status"] == "unsupported"
    with pytest.raises(ImportFailure):
        checksum_line(calculated["sha512"] + "  other.zip\n", path.name, "sha512")


@pytest.mark.parametrize(
    "values",
    [
        {"offices": ("governor",)},
        {"rounds": (3,)},
        {"rounds": (True,)},
        {"territories": ("BR",)},
        {"territories": ("ALL", "SC")},
        {"profile": "unknown"},
        {"election_year": 2022},
    ],
)
def test_invalid_selection(values):
    with pytest.raises(ImportFailure):
        Selection(**values)


def test_configuration(tmp_path):
    c = Config.from_dict(
        {
            "input_dir": "a",
            "output_dir": "b",
            "limits": {"max_members": 4},
            "selection": {"territories": ["ZZ"]},
        },
        tmp_path,
    )
    assert c.input_dir == tmp_path / "a"
    assert c.limits.max_members == 4
    assert c.selection.rounds == (1, 2)
    with pytest.raises(ImportFailure):
        Config.from_dict({"input_dir": "a", "output_dir": "b", "silent_option": True})


def test_parse_identifiers_missing_zero(source_set):
    stats = {}
    records = list(
        parse(source_set / "synthetic-section.zip", "section.csv", Selection(), Limits(), stats)
    )
    assert records[0].municipality == "00001"
    assert records[0].zone == "0001"
    assert records[0].section == "0001"
    assert records[0].candidate_id == "0000011"
    assert records[0].eligible is None
    assert any(r.uf == "ZZ" for r in records)
    assert next(r for r in records if r.kind == "blank").votes == 0
    assert stats["crc_checked"] and stats["rows_read"] == 24


@pytest.mark.parametrize(
    "changes",
    [
        {"QT_VOTOS": "-4"},
        {"QT_VOTOS": ""},
        {"CD_CARGO": "1", "DS_CARGO": "Vereador"},
        {"NR_TURNO": "9"},
        {"SG_UF": "VT"},
        {"NR_VOTAVEL": "97"},
    ],
)
def test_invalid_record(tmp_path, changes):
    p = write_zip(tmp_path / "test.zip", [row(**changes)])
    with pytest.raises(ImportFailure):
        list(parse(p, "section.csv", Selection(), Limits(), {}))


@pytest.mark.parametrize(
    "delimiter,header", [(",", None), (";", SCHEMAS["section"] + ["UNEXPECTED"])]
)
def test_schema_drift(tmp_path, delimiter, header):
    p = write_zip(tmp_path / "test.zip", [row()], delimiter=delimiter, header=header)
    assert inspect_member(p, "section.csv")["status"] == "unsupported"
    with pytest.raises(ImportFailure):
        list(parse(p, "section.csv", Selection(), Limits(), {}))


def test_full_pipeline_concrete_queries(source_set, tmp_path):
    release = run_import(config(source_set, tmp_path))
    result = validate_release(release)
    assert result["structurally_valid"]
    assert result["result_rows"] == 24
    assert result["comparison"] == {"matched": 2, "not_verifiable": 4}
    with sqlite3.connect(release / "election.sqlite") as db:
        assert db.execute("SELECT COUNT(*) FROM sections").fetchone()[0] == 6
        assert db.execute("SELECT SUM(votes) FROM aggregates").fetchone()[0] == 600
        assert db.execute("SELECT SUM(votes) FROM aggregates WHERE uf='ZZ'").fetchone()[0] == 200
        assert (
            db.execute(
                "SELECT SUM(votes) FROM aggregates a JOIN elections e ON e.id=a.election WHERE e.round=2"
            ).fetchone()[0]
            == 300
        )
        assert db.execute(
            "SELECT eligible,turnout,abstention,blank FROM section_totals WHERE comparison='matched' LIMIT 1"
        ).fetchone() == (120, 100, 20, 0)
        assert (
            db.execute(
                "SELECT eligible FROM section_totals WHERE comparison='not_verifiable' LIMIT 1"
            ).fetchone()[0]
            is None
        )
        assert (
            db.execute(
                "SELECT SUM(votes) FROM results r JOIN sections s ON s.id=r.section_id WHERE s.municipality='00001' AND s.zone='0001' AND s.section='0001' AND s.uf='SC'"
            ).fetchone()[0]
            == 200
        )
        assert not db.execute(
            "SELECT name FROM sqlite_master WHERE name IN ('raw','analyst_presidential')"
        ).fetchall()
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []
    manifest = json.loads((release / "manifest.json").read_text(encoding="utf8"))
    assert manifest["data_kind"] == "synthetic"
    assert manifest["assessment"]["source_hashes"]["status"] == "unverified"
    assert (
        manifest["artifacts"]["election.sqlite"]["sha256"]
        == hashes(release / "election.sqlite")["sha256"]
    )


def test_idempotence_and_checkpoint_resume(source_set, tmp_path):
    c = config(source_set, tmp_path, storage=StoragePolicy(retain_checkpoints=True))
    first = run_import(c)
    assert run_import(c) == first
    # Remove only pointer/release via rename to simulate consolidation interrupted after units.
    (first / "manifest.json").rename(first / "original-manifest.json")
    hidden = first.with_name(first.name + "-saved")
    first.rename(hidden)
    second = run_import(c)
    assert (
        json.loads((second / "validation.json").read_text(encoding="utf8"))["performance"][
            "checkpoints_reused"
        ]
        == 2
    )
    assert hashes(second / "election.sqlite") == hashes(hidden / "election.sqlite")


def test_changed_source_and_failure_preserve_previous(source_set, tmp_path):
    c = config(source_set, tmp_path)
    first = run_import(c)
    pointer = (c.output_dir / "current.json").read_bytes()
    write_zip(source_set / "broken.zip", [row(), row()])
    with pytest.raises(ImportFailure, match="duplicado"):
        run_import(c)
    assert (c.output_dir / "current.json").read_bytes() == pointer
    assert validate_release(first)["structurally_valid"]


def test_divergence_blocks_publish(source_set, tmp_path):
    write_zip(
        source_set / "synthetic-bweb.zip",
        [
            row(fmt="bweb", number="11", votes=59),
            row(fmt="bweb", number="22", votes=31),
            row(fmt="bweb", number="95", votes=0),
            row(fmt="bweb", number="96", votes=10),
        ],
        fmt="bweb",
    )
    c = config(source_set, tmp_path)
    with pytest.raises(ImportFailure, match="Validação"):
        run_import(c)
    assert not (c.output_dir / "current.json").exists()
    reports = list((c.output_dir / ".work").glob("*/staging/validation.json"))
    assert (
        json.loads(reports[0].read_text(encoding="utf8"))["reconciliation"]["different_rows"] == 2
    )


def test_ambiguous_bu_never_summed(source_set, tmp_path):
    bu = []
    for context in ("one", "two"):
        for number, votes in (("11", 60), ("22", 30), ("95", 0), ("96", 10)):
            bu.append(row(fmt="bweb", number=number, votes=votes, DT_EMISSAO_BU=context))
    write_zip(source_set / "synthetic-bweb.zip", bu, fmt="bweb")
    release = run_import(config(source_set, tmp_path))
    report = json.loads((release / "validation.json").read_text(encoding="utf8"))
    assert report["reconciliation"]["ambiguous_locations"] == 1
    assert sum(r["votes"] for r in report["candidate_totals"]) == 600
    assert report["comparison"] == {"not_verifiable": 6}


def test_filters_and_analyst(source_set, tmp_path):
    selection = Selection(rounds=(2,), territories=("SC",), profile="analyst")
    release = run_import(config(source_set, tmp_path, selection=selection))
    with sqlite3.connect(release / "election.sqlite") as db:
        assert db.execute("SELECT COUNT(*) FROM results").fetchone()[0] == 4
        assert db.execute("SELECT COUNT(*) FROM analyst_presidential").fetchone()[0] == 8
    assert validate_release(release)["structurally_valid"]


def test_hash_mismatch_and_required_verification(source_set, tmp_path):
    c = config(source_set, tmp_path, require_verified=True)
    with pytest.raises(ImportFailure, match="confiável"):
        run_import(c)
    ref = {
        "synthetic-section.zip": {
            "algorithm": "sha256",
            "digest": "0" * 64,
            "origin": "fixture",
            "trusted": True,
        }
    }
    with pytest.raises(ImportFailure, match="recusada"):
        run_import(replace(c, references=ref, require_verified=False))


def test_missing_round_incomplete_and_line_limit(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    write_zip(root / "one.zip", [row()])
    with pytest.raises(ImportFailure, match="Validação"):
        run_import(config(root, tmp_path))
    with pytest.raises(ImportFailure, match="Linha"):
        list(parse(root / "one.zip", "section.csv", Selection(), Limits(max_line_bytes=10), {}))
    with zipfile.ZipFile(root / "bad.zip", "w") as z:
        z.writestr("section.csv", ";".join(SCHEMAS["section"]) + "\n2026;1\n")
    with pytest.raises(ImportFailure, match="incompleto"):
        list(parse(root / "bad.zip", "section.csv", Selection(), Limits(), {}))


def test_crc_corruption(tmp_path):
    path = tmp_path / "bad.zip"
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as z:
        z.writestr("data.txt", b"UNIQUE_PAYLOAD")
    content = bytearray(path.read_bytes())
    pos = content.index(b"UNIQUE_PAYLOAD")
    content[pos] = ord("X")
    path.write_bytes(content)
    with pytest.raises(zipfile.BadZipFile):
        with member_stream(path, "data.txt", Limits()) as stream:
            stream.read()


def test_cli_full_flow(source_set, tmp_path, capsys):
    assert main(["inventory", "--input", str(source_set)]) == 0
    assert main(["inspect", "--input", str(source_set)]) == 0
    assert main(["verify", "--input", str(source_set), "--crc"]) == 0
    cpath = tmp_path / "config.json"
    cpath.write_text(
        json.dumps(
            {
                "input_dir": str(source_set),
                "output_dir": str(tmp_path / "out"),
                "data_kind": "synthetic",
            }
        ),
        encoding="utf8",
    )
    assert main(["import", "--config", str(cpath)]) == 0
    assert main(["validate", "--dataset", str(tmp_path / "out")]) == 0
    assert main(["report", "--dataset", str(tmp_path / "out")]) == 0
    assert main(["inventory", "--input", str(tmp_path / "none")]) == 2
    assert "Erro:" in capsys.readouterr().err


def test_cli_help():
    result = subprocess.run(
        [sys.executable, "-m", "votoaberto_auditor", "--help"], capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "inventory" in result.stdout


def test_missing_totals_keep_semantics(source_set, tmp_path):
    bu = [
        row(fmt="bweb", number=number, votes=votes, QT_APTOS="-3", QT_ABSTENCOES="-1")
        for number, votes in (("11", 60), ("22", 30), ("95", 0), ("96", 10))
    ]
    write_zip(source_set / "synthetic-bweb.zip", bu, fmt="bweb")
    release = run_import(config(source_set, tmp_path))
    with sqlite3.connect(release / "election.sqlite") as db:
        eligible, abstention, status = db.execute(
            "SELECT eligible,abstention,totals_status FROM section_totals WHERE comparison='matched'"
        ).fetchone()
        assert eligible is None and abstention is None
        assert json.loads(status) == {
            "QT_APTOS": "not_recorded",
            "QT_ABSTENCOES": "missing",
            "QT_COMPARECIMENTO": "present",
        }


def test_math_errors_and_tampering(source_set, tmp_path):
    c = config(source_set, tmp_path)
    release = run_import(c)
    with sqlite3.connect(release / "election.sqlite") as db:
        db.execute("UPDATE section_totals SET blank=999 WHERE section_id=1")
        db.commit()
    result = validate_database(release / "election.sqlite")
    assert result["structurally_valid"]
    assert result["checks"]["sqlite_integrity"]["status"] == "passed"
    assert result["checks"]["mathematics"]["status"] == "failed"
    assert main(["validate", "--dataset", str(release / "election.sqlite")]) == 1
    with pytest.raises(ImportFailure, match="Hash"):
        validate_release(release)


def test_cancel_and_lock(source_set, tmp_path):
    c = config(source_set, tmp_path)

    def cancel(message):
        if "Processando" in message:
            raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        run_import(c, cancel)
    assert not (c.output_dir / "current.json").exists()
    assert not (c.output_dir / ".import.lock").exists()
    (c.output_dir / ".import.lock").write_text("test")
    with pytest.raises(ImportFailure, match="lock"):
        run_import(c)


def test_inconsistent_turnout_even_with_missing_abstention(source_set, tmp_path):
    bu = [
        row(fmt="bweb", number=number, votes=votes, QT_APTOS="99", QT_ABSTENCOES="-1")
        for number, votes in (("11", 60), ("22", 30), ("95", 0), ("96", 10))
    ]
    write_zip(source_set / "synthetic-bweb.zip", bu, fmt="bweb")
    with pytest.raises(ImportFailure, match="Validação"):
        run_import(config(source_set, tmp_path))


def test_symlink_encryption_and_index_limit(tmp_path):
    import stat

    from tse_importer.discovery import member_issues

    info = zipfile.ZipInfo("link.csv")
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    assert "symlink" in member_issues(info, Limits())
    info.flag_bits |= 1
    assert "encrypted" in member_issues(info, Limits())
    write_zip(tmp_path / "test.zip", [row()])
    assert inventory(tmp_path, Limits(max_index_bytes=1))["files"][0]["status"] == "error"


def test_volume_generated_stream(tmp_path):
    root = tmp_path / "volume"
    root.mkdir()
    records = (
        row(turn=turn, section=f"{section:05d}", votes=1)
        for turn in (1, 2)
        for section in range(10000)
    )
    write_zip(root / "volume.zip", records)
    release = run_import(config(root, tmp_path))
    result = validate_database(release / "election.sqlite")
    assert result["result_rows"] == 20000
    assert sum(c["votes"] for c in result["candidate_totals"]) == 20000


@pytest.mark.official
@pytest.mark.skipif(
    not (os.environ.get("TSE_REAL_INPUT") or os.environ.get("TSE_REAL_CONFIG")),
    reason="Defina TSE_REAL_INPUT ou TSE_REAL_CONFIG para integração local opt-in",
)
def test_official_sc_both_rounds(tmp_path):
    c = official_config(os.environ, tmp_path / "official")
    assert c.selection.territories == ("SC",)
    assert c.selection.rounds == (1, 2)
    release = run_import(c)
    result = validate_release(release)
    assert result["structurally_valid"]
    assert [(r["round"], r["rows"]) for r in result["observed_coverage"]] == [
        (1, 136979),
        (2, 67266),
    ]
    report = json.loads((release / "validation.json").read_text(encoding="utf8"))
    assert report["reconciliation"]["matched_rows"] == 204245
    assert report["reconciliation"]["different_rows"] == 0
    assert [r["sections"] for r in result["observed_coverage"]] == [17326, 17326]
    assert [r["votes"] for r in result["observed_coverage"]] == [4648159, 4762303]
    assert {
        (r["round"], r["number"]): r["votes"]
        for r in result["candidate_totals"]
        if r["number"] in ("13", "22", "95", "96")
    } == {
        (1, "13"): 1127168,
        (1, "22"): 3000020,
        (1, "95"): 69007,
        (1, "96"): 78071,
        (2, "13"): 1418314,
        (2, "22"): 3220071,
        (2, "95"): 48674,
        (2, "96"): 75244,
    }

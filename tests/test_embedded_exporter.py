"""Entirely fictional SQLite -> municipal JSON integration and failure regressions."""

import json
import sqlite3
from pathlib import Path

import pytest
from conftest import row, write_zip
from tse_importer import embedded_exporter as exporter
from tse_importer.domain import Config, ImportFailure, StoragePolicy
from tse_importer.embedded_assets import build_metadata, install_assets
from tse_importer.engine import run_import
from tse_importer.integrity import hashes


def read(path):
    return json.loads(path.read_text(encoding="utf8"))


@pytest.fixture
def release(tmp_path):
    sources = tmp_path / "sources"
    sources.mkdir()
    primary, bu = [], []
    for turn in (1, 2):
        for uf in ("SC", "RS", "ZZ"):
            for city in ("00001", "00002"):
                for number, votes in (
                    ("11", 60),
                    ("22" if turn == 1 else "33", 30),
                    ("95", 0),
                    ("96", 10),
                ):
                    changes = {"CD_MUNICIPIO": city, "NM_MUNICIPIO": "São FICTÍCIO"}
                    primary.append(row(turn=turn, uf=uf, number=number, votes=votes, **changes))
                    bu.append(
                        row(fmt="bweb", turn=turn, uf=uf, number=number, votes=votes, **changes)
                    )
    write_zip(sources / "section.zip", primary)
    write_zip(sources / "bweb.zip", bu, fmt="bweb")
    return run_import(Config(sources, tmp_path / "sqlite", data_kind="synthetic"))


def test_end_to_end_and_determinism(release, tmp_path):
    before = hashes(release / "election.sqlite")
    output = tmp_path / "embedded"
    first = exporter.export_embedded(release.parent.parent, output)
    target = Path(first["release"])
    report = exporter.validate_embedded(target)
    assert report["municipality_counts"] == {"RS": 2, "SC": 2, "ZZ": 2}
    assert report["municipal_round_records"] == 12
    assert report["national"]["rounds"][0]["totals"] == {
        "valid": 540,
        "counted": 600,
        "blank": 0,
        "null": 60,
        "eligible": 720,
        "turnout": 600,
        "abstention": 120,
    }
    assert report["national"]["domestic_rounds"][0]["totals"]["counted"] == 400
    # 120 eligible per section, never 120 times the four candidate/category rows.
    sc = read(target / "municipalities/SC.json")["municipalities"]
    assert [city["code"] for city in sc] == ["00001", "00002"]
    assert sc[0]["name"] == "São FICTÍCIO"
    assert sc[0]["rounds"][0]["totals"]["eligible"] == 120
    assert "0002:22" not in sc[0]["rounds"][1]["candidates"]
    assert "0002:33" in sc[0]["rounds"][1]["candidates"]
    manifest = read(target / "manifest.json")
    assert manifest["data_nature"] == "synthetic"
    assert manifest["public_readiness"]["status"] == "not_ready"
    second = exporter.export_embedded(release, output)
    assert second["dataset_id"] == first["dataset_id"]
    assert hashes(release / "election.sqlite") == before
    assert list((output / ".work").iterdir()) == []
    assert first["storage"]["remaining_work_bytes"] == 0


@pytest.mark.parametrize("failure", ["manifest", "schema", "hash"])
def test_invalid_release_never_promoted(release, tmp_path, failure):
    manifest = read(release / "manifest.json")
    if failure == "manifest":
        manifest["artifacts"] = {}
    elif failure == "schema":
        manifest["schema_version"] = 999
    else:
        manifest["artifacts"]["election.sqlite"]["sha256"] = "0" * 64
    (release / "manifest.json").write_text(json.dumps(manifest), encoding="utf8")
    output = tmp_path / "invalid"
    with pytest.raises(ImportFailure):
        exporter.export_embedded(release, output)
    assert not (output / "current.json").exists()


def test_read_only_and_unknown_output_protection(release, tmp_path):
    db = exporter.read_only(release / "election.sqlite")
    try:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            db.execute("DELETE FROM results")
    finally:
        db.close()
    with pytest.raises(ImportFailure, match="separada"):
        exporter.export_embedded(release, release / "derived")
    output = tmp_path / "low-budget"
    output.mkdir()
    unknown = output / "unknown.json"
    unknown.write_text("preserve", encoding="utf8")
    with pytest.raises(ImportFailure, match="max_work"):
        exporter.export_embedded(
            release, output, StoragePolicy(max_work_disk_bytes=1, min_free_disk_bytes=0)
        )
    assert unknown.read_text(encoding="utf8") == "preserve"


def test_validation_and_publish_failures_preserve_previous(release, tmp_path, monkeypatch):
    output = tmp_path / "embedded"
    exporter.export_embedded(release, output)
    pointer = (output / "current.json").read_bytes()

    def fail(*args, **kwargs):
        raise ImportFailure("injected mismatch")

    monkeypatch.setattr(exporter, "validate_embedded", fail)
    with pytest.raises(ImportFailure, match="injected"):
        exporter.export_embedded(release, output)
    assert (output / "current.json").read_bytes() == pointer


def test_absent_totals_remain_null(source_set, tmp_path):
    release = run_import(Config(source_set, tmp_path / "sqlite", data_kind="synthetic"))
    target = Path(exporter.export_embedded(release, tmp_path / "embedded")["release"])
    df = read(target / "municipalities/DF.json")["municipalities"][0]["rounds"][0]
    assert df["totals"]["eligible"] is None
    assert df["available_sections"]["eligible"] == 0
    assert df["totals"]["blank"] == 0  # Explicit zero source row, not an absence.


def test_install_and_build_preflight(release, tmp_path):
    target = Path(exporter.export_embedded(release, tmp_path / "embedded")["release"])
    assets = tmp_path / "assets"
    assets.mkdir()
    (assets / ".gitkeep").write_bytes(b"")
    install_assets(target, assets)
    assert build_metadata(assets, "synthetic")["schema_version"] == 1
    install_assets(target, assets)
    with pytest.raises(ImportFailure, match="natureza"):
        build_metadata(assets, "official-derived")
    with pytest.raises(ImportFailure, match="ausente"):
        build_metadata(tmp_path / "absent", "official-derived")
    assert (assets / ".gitkeep").exists()


def test_independent_sql_comparison_blocks_coherent_wrong_aggregate(release, tmp_path, monkeypatch):
    original = exporter._municipalities

    def wrong(db, work):
        data = original(db, work)
        record = next(iter(data.values()))[1]
        record["candidates"][next(iter(record["candidates"]))] += 1
        for key in ("valid", "counted", "turnout", "eligible"):
            record["totals"][key] += 1
        return data

    monkeypatch.setattr(exporter, "_municipalities", wrong)
    output = tmp_path / "bad"
    with pytest.raises(ImportFailure, match="JSON/SQLite"):
        exporter.export_embedded(release, output)
    assert not (output / "current.json").exists()


def test_pointer_failure_rolls_back_new_release(release, tmp_path, monkeypatch):
    output = tmp_path / "embedded"
    output.mkdir()
    pointer = b'{"preserve":"old pointer"}'
    (output / "current.json").write_bytes(pointer)

    def fail(*args, **kwargs):
        raise OSError("publication failure")

    monkeypatch.setattr(exporter, "_publish_pointer", fail)
    with pytest.raises(OSError, match="publication"):
        exporter.export_embedded(release, output)
    assert (output / "current.json").read_bytes() == pointer
    assert not list((output / "releases").iterdir())


@pytest.mark.parametrize("failure", ["schema", "hash", "duplicate", "mixed"])
def test_invalid_json_contract(release, tmp_path, failure):
    target = Path(exporter.export_embedded(release, tmp_path / "embedded")["release"])
    manifest = read(target / "manifest.json")
    name = "municipalities/SC.json"
    data = read(target / name)
    if failure == "schema":
        manifest["schema_version"] = 99
    elif failure == "hash":
        (target / name).write_bytes(b"corrupt")
    else:
        if failure == "duplicate":
            data["municipalities"].append(data["municipalities"][0])
        else:
            data["dataset_id"] = "different"
        payload = exporter.canonical(data)
        (target / name).write_bytes(payload)
        manifest["artifacts"][name] = {
            "bytes": len(payload),
            "sha256": hashes(target / name)["sha256"],
        }
    (target / "manifest.json").write_bytes(exporter.canonical(manifest))
    with pytest.raises(ImportFailure):
        exporter.validate_embedded(target)

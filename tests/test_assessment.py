import json
from dataclasses import replace

import pytest
from conftest import row, write_zip
from official_support import official_config
from tse_importer import engine
from tse_importer.assessment import coverage_assessment
from tse_importer.domain import TERRITORIES, Config, CoverageRequirements, ImportFailure, Selection
from tse_importer.engine import run_import, validate_release
from tse_importer.integrity import hashes, verify
from tse_importer.validation import validate_database
from votoaberto_auditor.cli import import_config, main, parser


def read_json(path):
    return json.loads(path.read_text(encoding="utf8"))


def test_partial_bu_coverage_is_structurally_sound(source_set, tmp_path):
    release = run_import(Config(source_set, tmp_path / "out", data_kind="synthetic"))
    result = validate_release(release)
    a = result["assessment"]
    assert result["structurally_valid"] and "valid" not in result
    assert a["sqlite_integrity"]["status"] == a["referential_integrity"]["status"] == "passed"
    assert a["mathematics"]["status"] == "partially_checked"
    assert a["mathematics"]["sections_with_unavailable_totals"] == 4
    assert a["coverage"]["status"] == "observed_only"
    assert a["coverage"]["national_presence"]["status"] == "incomplete"
    assert a["reconciliation"]["status"] == "partial"
    assert a["reconciliation"]["only_section_rows"] == 16
    assert a["reconciliation"]["matched_section_rounds"] == 2
    assert a["local_release"] == {"status": "eligible", "blockers": []}
    assert a["public_readiness"]["status"] == "not_ready"
    assert "reconciliation_incomplete" in a["public_readiness"]["blockers"]
    standalone = validate_database(release / "election.sqlite")
    assert standalone["public_readiness"]["status"] == "not_assessed"
    assert standalone["assessment_scope"] == "sqlite_only"


def test_manifest_separates_dimensions(source_set, tmp_path):
    release = run_import(Config(source_set, tmp_path / "out", data_kind="synthetic"))
    manifest, report = (read_json(release / name) for name in ("manifest.json", "validation.json"))
    assert manifest["assessment_version"] == report["assessment_version"] == 2
    assert manifest["assessment"] == report["assessment"]
    assert not {"valid", "validation"} & manifest.keys()
    assert set(manifest["assessment"]) == {
        "sqlite_integrity",
        "referential_integrity",
        "mathematics",
        "data_structure",
        "coverage",
        "source_hashes",
        "reconciliation",
        "local_release",
        "public_readiness",
    }
    assert manifest["assessment"]["source_hashes"]["origin_authentication"] == "not_performed"
    assert report["structurally_valid"]
    assert manifest["data_nature"] == "synthetic"


def test_all_allows_partial_national_failure_preserves_release(source_set, tmp_path):
    c = Config(source_set, tmp_path / "out", data_kind="synthetic")
    first = run_import(c)
    pointer = (c.output_dir / "current.json").read_bytes()
    requirements = CoverageRequirements(territories=("NATIONAL",), rounds=(1, 2))
    with pytest.raises(ImportFailure, match="Validação"):
        run_import(replace(c, coverage_requirements=requirements))
    assert (c.output_dir / "current.json").read_bytes() == pointer
    assert validate_release(first)["assessment"]["local_release"]["status"] == "eligible"
    failed = next((c.output_dir / ".work").glob("*/staging/validation.json"))
    report = read_json(failed)
    assert report["structurally_valid"]
    coverage = report["assessment"]["coverage"]
    assert coverage["status"] == "incomplete"
    assert len(coverage["expected_pairs"]) == 56 and len(coverage["missing_pairs"]) == 50
    assert report["assessment"]["local_release"]["blockers"] == ["required_coverage_missing"]


def test_national_presence_is_not_section_completeness():
    requirements = CoverageRequirements(territories=("NATIONAL",), rounds=(1, 2))
    rows = [{"round": turn, "uf": uf, "sections": 1} for turn in (1, 2) for uf in TERRITORIES]
    result = coverage_assessment(rows, Selection(), requirements)
    assert result["status"] == "complete"
    assert result["national_presence"] == {"rounds": [1, 2], "status": "complete"}
    assert result["section_completeness"]["status"] == "not_assessed"
    rows = [r for r in rows if not (r["round"] == 2 and r["uf"] == "ZZ")]
    result = coverage_assessment(rows, Selection(), requirements)
    assert result["status"] == "incomplete"
    assert result["missing_pairs"] == [{"round": 2, "uf": "ZZ"}]


def test_explicit_coverage_and_incompatible_filters(source_set, tmp_path):
    requirements = CoverageRequirements(territories=("SC", "DF", "ZZ"), rounds=(1, 2))
    release = run_import(
        Config(
            source_set, tmp_path / "out", data_kind="synthetic", coverage_requirements=requirements
        )
    )
    a = validate_release(release)["assessment"]
    assert a["coverage"]["status"] == "complete" and a["reconciliation"]["status"] == "partial"
    assert a["public_readiness"]["status"] == "not_ready"
    with pytest.raises(ImportFailure, match="territórios"):
        Config(
            source_set,
            tmp_path / "other",
            selection=Selection(territories=("SC",)),
            coverage_requirements=requirements,
        )
    with pytest.raises(ImportFailure, match="turnos"):
        Config(
            source_set,
            tmp_path / "other",
            selection=Selection(rounds=(1,)),
            coverage_requirements=requirements,
        )


def test_hash_trust_is_always_operator_assigned(source_set):
    path = source_set / "synthetic-section.zip"
    calculated = hashes(path)
    ref = {
        "algorithm": "sha256",
        "digest": calculated["sha256"],
        "origin": "https://example.invalid/reference",
        "trusted": True,
    }
    trusted = verify(path, calculated, ref)
    untrusted = verify(path, calculated, {**ref, "trusted": False})
    assert trusted["status"] == "verified"  # Legacy name; explicit scope now accompanies it.
    assert untrusted["status"] == "unverified"
    for result in (trusted, untrusted):
        assert result["digest_comparison"] == "match"
        assert (
            result["origin_authentication"] == result["signature_verification"] == "not_performed"
        )
    assert trusted["reference_trust"] == "operator_declared"
    assert untrusted["reference_trust"] == "not_assigned"


def test_public_ready_only_for_declared_scope(source_set, tmp_path):
    refs = {
        p.name: {
            "algorithm": "sha256",
            "digest": hashes(p)["sha256"],
            "origin": "fixture reference",
            "trusted": True,
        }
        for p in source_set.glob("*.zip")
    }
    # Simulate an operator-declared official input; the generated fixtures are fictional.
    c = Config(
        source_set, tmp_path / "out", selection=Selection(territories=("SC",)), references=refs
    )
    a = validate_release(run_import(c))["assessment"]
    assert a["source_hashes"]["status"] == "matched_operator_trusted"
    assert a["public_readiness"]["status"] == "ready_for_declared_scope"
    assert a["public_readiness"]["scope"] == [{"round": 1, "uf": "SC"}, {"round": 2, "uf": "SC"}]
    assert a["coverage"]["national_presence"]["status"] == "incomplete"
    assert a["public_readiness"]["section_completeness"] == "not_assessed"
    assert a["public_readiness"]["origin_authentication"] == "not_performed"
    a = validate_release(run_import(replace(c, data_kind="synthetic")))["assessment"]
    assert "synthetic_data" in a["public_readiness"]["blockers"]


def test_cli_coverage_flags_and_exit_codes(source_set, tmp_path):
    args = parser().parse_args(
        [
            "import",
            "--input",
            str(source_set),
            "--output",
            str(tmp_path / "out"),
            "--require-territory",
            "NATIONAL",
            "--require-round",
            "1",
            "--require-round",
            "2",
        ]
    )
    assert import_config(args).coverage_requirements == CoverageRequirements(
        territories=("NATIONAL",), rounds=(1, 2)
    )
    assert (
        main(
            ["import", "--input", str(source_set), "--output", str(tmp_path / "out"), "--synthetic"]
        )
        == 0
    )
    assert main(["validate", "--dataset", str(tmp_path / "out")]) == 0
    assert (
        main(
            [
                "import",
                "--input",
                str(source_set),
                "--output",
                str(tmp_path / "out"),
                "--require-territory",
                "NATIONAL",
            ]
        )
        == 2
    )


def test_official_path_precedence(tmp_path, monkeypatch):
    location = tmp_path / "configs"
    location.mkdir()
    config = location / "test.json"
    config.write_text(
        json.dumps(
            {
                "input_dir": "json-input",
                "output_dir": "json-output",
                "selection": {"territories": ["SC"]},
            }
        ),
        encoding="utf8",
    )
    monkeypatch.chdir(tmp_path)
    result = official_config({"TSE_REAL_CONFIG": "configs/test.json"}, tmp_path / "default")
    assert (
        result.input_dir == location / "json-input"
        and result.output_dir == location / "json-output"
    )
    result = official_config(
        {"TSE_REAL_CONFIG": "configs/test.json", "TSE_REAL_INPUT": "operator-input"},
        tmp_path / "default",
    )
    assert (
        result.input_dir == tmp_path / "operator-input"
        and result.output_dir == location / "json-output"
    )
    result = official_config({"TSE_REAL_INPUT": "operator-input"}, tmp_path / "default")
    assert (
        result.input_dir == tmp_path / "operator-input"
        and result.output_dir == tmp_path / "default"
    )
    with pytest.raises(ValueError, match="Defina"):
        official_config({}, tmp_path / "default")


def test_complete_national_presence_import(tmp_path):
    source = tmp_path / "input"
    source.mkdir()
    write_zip(
        source / "national-fictional.zip",
        (row(turn=turn, uf=uf, votes=1) for turn in (1, 2) for uf in sorted(TERRITORIES)),
    )
    release = run_import(
        Config(
            source,
            tmp_path / "out",
            data_kind="synthetic",
            coverage_requirements=CoverageRequirements(territories=("NATIONAL",), rounds=(1, 2)),
        )
    )
    a = validate_release(release)["assessment"]
    assert a["coverage"]["status"] == "complete"
    assert len(a["coverage"]["observed_pairs"]) == 56
    assert a["coverage"]["section_completeness"]["status"] == "not_assessed"
    assert a["reconciliation"]["status"] == "not_verifiable"
    assert a["local_release"]["status"] == "eligible"
    assert a["public_readiness"]["status"] == "not_ready"


def test_missing_official_input_override_is_not_ignored(source_set, tmp_path):
    path = tmp_path / "official.json"
    path.write_text(
        json.dumps({"input_dir": str(source_set), "output_dir": str(tmp_path / "out")}),
        encoding="utf8",
    )
    config = official_config(
        {"TSE_REAL_CONFIG": str(path), "TSE_REAL_INPUT": str(tmp_path / "missing")},
        tmp_path / "unused",
    )
    with pytest.raises(ImportFailure, match="inexistente"):
        run_import(config)


def test_retained_evidence_is_labelled(source_set, tmp_path):
    release = run_import(Config(source_set, tmp_path / "out", data_kind="synthetic"))
    imported = read_json(release / "validation.json")["assessment"]
    current = validate_release(release)["assessment"]
    assert imported["source_hashes"]["evidence"] == "current_import_hashes"
    assert current["source_hashes"]["evidence"] == "retained_catalog_no_source_reread"
    assert current["reconciliation"]["evidence"] == "retained_report_and_database"


def test_windows_promotion_retry_is_bounded(tmp_path, monkeypatch):
    stage, release = tmp_path / "stage", tmp_path / "release"
    stage.mkdir()
    original = engine.os.replace
    attempts = []

    def replace_with_transient_lock(source, target):
        attempts.append((source, target))
        if len(attempts) == 1:
            error = PermissionError("sharing violation")
            error.winerror = 32
            raise error
        original(source, target)

    monkeypatch.setattr(engine.os, "replace", replace_with_transient_lock)
    monkeypatch.setattr(engine.time, "sleep", lambda seconds: None)
    engine.promote_directory(stage, release)
    assert release.is_dir() and len(attempts) == 2
    other = tmp_path / "other"
    other.mkdir()

    def permanent(source, target):
        attempts.append((source, target))
        error = PermissionError("access denied")
        error.winerror = 5
        raise error

    attempts.clear()
    monkeypatch.setattr(engine.os, "replace", permanent)
    with pytest.raises(PermissionError):
        engine.promote_directory(other, tmp_path / "missing")
    assert len(attempts) == 6 and other.is_dir()

import json
import os
import sqlite3
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from conftest import row, write_zip
from tse_importer import engine, partitioned, workspace
from tse_importer.discovery import inventory
from tse_importer.domain import Config, CoverageRequirements, ImportFailure, StoragePolicy
from tse_importer.engine import run_import, validate_release
from tse_importer.planning import plan
from tse_importer.workspace import WorkRun
from votoaberto_auditor.cli import import_config, parser


def read(path):
    return json.loads(path.read_text(encoding="utf8"))


def ledgers(config):
    return [read(path) for path in (config.output_dir / ".runs").glob("*.json")]


@pytest.mark.parametrize(
    "values",
    [
        {"max_work_disk_bytes": 0},
        {"min_free_disk_bytes": -1},
        {"work_directory": "../elsewhere"},
        {"work_directory": "C:/outside"},
        {"work_directory": "D:"},
        {"work_directory": "C:"},
        {"work_directory": "foo:stream"},
        {"work_directory": "..\\outside"},
        {"retain_checkpoints": 1},
        {"cleanup_policy": "recursive"},
        {"detailed_report_bytes": -1},
        {"projected_peak_bytes": True},
    ],
)
def test_invalid_policy(values):
    with pytest.raises(ImportFailure):
        StoragePolicy(**values)


def test_minimum_free_and_projection_stop_before_work(tmp_path, monkeypatch):
    monkeypatch.setattr(workspace.shutil, "disk_usage", lambda path: SimpleNamespace(free=100))
    with pytest.raises(ImportFailure, match="min_free"):
        WorkRun(tmp_path, StoragePolicy(min_free_disk_bytes=101))
    with pytest.raises(ImportFailure, match="max_work"):
        WorkRun(
            tmp_path,
            StoragePolicy(max_work_disk_bytes=100, min_free_disk_bytes=0, projected_peak_bytes=101),
        )
    assert not (tmp_path / ".work").exists()


def test_next_temporary_would_exceed_budget(tmp_path):
    with WorkRun(
        tmp_path, StoragePolicy(max_work_disk_bytes=1024**2, min_free_disk_bytes=0)
    ) as work:
        with pytest.raises(ImportFailure, match="max_work"):
            work.check(2 * 1024**2)
        assert not (work.root / "too-big.tmp").exists()


def test_unknown_file_and_preexisting_artifacts_never_cleaned(tmp_path):
    previous = tmp_path / "releases" / "previous"
    previous.mkdir(parents=True)
    old = previous / "election.sqlite"
    old.write_bytes(b"preexisting release")
    with WorkRun(tmp_path, StoragePolicy()) as work:
        known = work.file(Path("temporary.partial"))
        known.write_bytes(b"temporary")
        foreign = work.root / "unknown.bin"
        foreign.write_bytes(b"unknown owner")
        with pytest.raises(ImportFailure, match="fora"):
            work.remove(old)
    assert old.read_bytes() == b"preexisting release"
    assert foreign.read_bytes() == b"unknown owner"
    assert not known.exists()


def test_replaced_file_identity_refused(tmp_path):
    with WorkRun(tmp_path, StoragePolicy()) as work:
        known = work.file(Path("replace.partial"))
        known.rename(work.root / "saved-unknown.bin")
        known.write_bytes(b"foreign replacement")
        work.remove(known)
        assert known.exists() and work.refused
    assert known.read_bytes() == b"foreign replacement"


def test_symlink_cleanup_never_follows_target(tmp_path):
    outside = tmp_path / "original.zip"
    outside.write_bytes(b"original")
    work = WorkRun(tmp_path, StoragePolicy())
    owned = work.file(Path("link.partial"))
    owned.unlink()
    try:
        owned.symlink_to(outside)
    except OSError:
        pytest.skip("Host cannot create symlinks")
    work.remove(owned)
    assert work.refused and outside.read_bytes() == b"original"


def test_success_cleans_only_owned_and_restores_process_temp(source_set, tmp_path, monkeypatch):
    monkeypatch.setenv("TEMP", "operator-temp")
    c = Config(source_set, tmp_path / "out", data_kind="synthetic")
    original = {p.name: p.read_bytes() for p in source_set.glob("*.zip")}
    release = run_import(c)
    assert validate_release(release)["structurally_valid"]
    assert not list((c.output_dir / ".work").glob("*"))
    assert os.environ["TEMP"] == "operator-temp"
    assert {p.name: p.read_bytes() for p in source_set.glob("*.zip")} == original
    ledger = ledgers(c)[0]
    assert ledger["status"] == "succeeded"
    assert ledger["metrics"]["remaining_work_bytes"] == 0
    assert ledger["metrics"]["recovered_logical_bytes"] > 0
    assert (release / "divergences-summary.json").is_file()


@pytest.mark.parametrize("failure", ["sqlite", "publish", "cancel"])
def test_failure_cleanup_preserves_pointer(source_set, tmp_path, monkeypatch, failure):
    c = Config(source_set, tmp_path / "out", data_kind="synthetic")
    previous = run_import(c)
    pointer = (c.output_dir / "current.json").read_bytes()
    write_zip(source_set / "additional.zip", [row(uf="AC", turn=1), row(uf="AC", turn=2)])

    def fail(*args, **kwargs):
        if failure == "cancel":
            raise KeyboardInterrupt()
        raise sqlite3.OperationalError("injected failure")

    if failure == "sqlite":
        monkeypatch.setattr(partitioned, "merge_partition", fail)
    else:
        monkeypatch.setattr(engine, "_publish_pointer", fail)
    with pytest.raises(KeyboardInterrupt if failure == "cancel" else sqlite3.OperationalError):
        run_import(c)
    assert (c.output_dir / "current.json").read_bytes() == pointer
    assert validate_release(previous)["structurally_valid"]
    assert not list((c.output_dir / ".work").glob("**/*.sqlite"))
    assert not (c.output_dir / ".import.lock").exists()
    assert any(
        x["status"] == ("cancelled" if failure == "cancel" else "failed") for x in ledgers(c)
    )


def test_resume_after_cancel_and_obsolete_checkpoint(source_set, tmp_path, monkeypatch):
    c = Config(
        source_set,
        tmp_path / "out",
        data_kind="synthetic",
        storage=StoragePolicy(retain_checkpoints=True),
    )
    original = partitioned.merge_partition

    def cancel(*args):
        raise KeyboardInterrupt()

    monkeypatch.setattr(partitioned, "merge_partition", cancel)
    with pytest.raises(KeyboardInterrupt):
        run_import(c)
    old_units = list((c.output_dir / ".work").glob("*/checkpoints/*.sqlite"))
    assert len(old_units) == 2
    monkeypatch.setattr(partitioned, "merge_partition", original)
    release = run_import(c)
    perf = read(release / "validation.json")["performance"]
    assert perf["checkpoints_reused"] == 2
    assert perf["source_csv_uncompressed_bytes_read"] == 0
    # A changed interpretation key invalidates old checkpoints without deleting them.
    monkeypatch.setattr(engine, "rules_digest", lambda: "changed-rules")
    newer = run_import(c)
    assert read(newer / "validation.json")["performance"]["checkpoints_reused"] == 0
    assert all(p.exists() for p in old_units)


def test_summary_absent_incomplete_and_bounded_details(source_set, tmp_path):
    # SC section 2 has no BU, SC section 1 has one votable absent from a valid BU.
    additions = [
        row(section="0002", turn=turn, number=number, votes=votes)
        for turn in (1, 2)
        for number, votes in (("11", 60), ("22", 30), ("95", 0), ("96", 10))
    ]
    write_zip(source_set / "extra.zip", additions)
    bu = [
        row(fmt="bweb", turn=turn, number=number, votes=votes)
        for turn in (1, 2)
        for number, votes in (
            ("11", 60 if turn == 1 else 65),
            ("22", 30 if turn == 1 else 25),
            ("96", 10),
        )
    ]
    write_zip(source_set / "synthetic-bweb.zip", bu, fmt="bweb")
    c = Config(
        source_set,
        tmp_path / "out",
        data_kind="synthetic",
        storage=StoragePolicy(detailed_report_bytes=1),
    )
    release = run_import(c)
    summary = read(release / "divergences-summary.json")
    assert summary["exact_occurrences"]["bweb_source_absent"] == 16
    assert summary["exact_occurrences"]["bweb_section_absent"] == 8
    assert summary["exact_occurrences"]["bweb_votable_absent"] == 2
    assert summary["detail"]["truncated"]
    assert summary["detail"]["omitted_due_to_limit"] == 10
    assert (release / "divergences.jsonl").stat().st_size <= 1
    assert read(release / "validation.json")["reconciliation"]["only_section_rows"] == 26


def test_explicit_source_paths_and_plan(source_set, tmp_path):
    (source_set / "broken.zip").write_bytes(b"invalid")
    c = Config(source_set, tmp_path / "out", data_kind="synthetic")
    assert not plan(c)["input_eligible"]
    selected = replace(c, source_paths=("synthetic-section.zip", "synthetic-bweb.zip"))
    assert plan(selected)["input_eligible"]
    release = run_import(selected)
    assert validate_release(release)["result_rows"] == 24
    with pytest.raises(ImportFailure, match="ausentes"):
        plan(replace(c, source_paths=("missing.zip",)))
    with pytest.raises(ImportFailure, match="source_paths"):
        replace(c, source_paths=("../outside.zip",))


def test_cached_hashes_are_recomputed_if_identity_changes(source_set, tmp_path):
    catalog = inventory(source_set)
    path = tmp_path / "cache.json"
    path.write_text(json.dumps(catalog), encoding="utf8")
    cached = inventory(source_set, cache_path=str(path))
    assert all(i["hash_calculation"] == "reused_local_fingerprint_cache" for i in cached["files"])
    write_zip(source_set / "synthetic-section.zip", [row(turn=1), row(turn=2)])
    changed = inventory(source_set, cache_path=str(path))
    assert (
        next(i for i in changed["files"] if i["name"] == "synthetic-section.zip")[
            "hash_calculation"
        ]
        == "read_current_bytes"
    )


def test_config_and_cli_storage_precedence(tmp_path):
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "input_dir": "source",
                "output_dir": "out",
                "storage": {"max_work_disk_bytes": 123456, "retain_checkpoints": True},
            }
        ),
        encoding="utf8",
    )
    args = parser().parse_args(
        [
            "import",
            "--config",
            str(config),
            "--max-work-disk-bytes",
            "654321",
            "--no-retain-checkpoints",
        ]
    )
    c = import_config(args)
    assert c.storage.max_work_disk_bytes == 654321 and not c.storage.retain_checkpoints


def test_official_national_requires_pilot_estimate(source_set, tmp_path):
    c = Config(
        source_set,
        tmp_path / "out",
        coverage_requirements=CoverageRequirements(("NATIONAL",), (1, 2)),
    )
    with pytest.raises(ImportFailure, match="projeção|projected_peak"):
        run_import(c)
    assert not list((c.output_dir / ".work").glob("**/*.sqlite"))


def test_disk_reserve_loss_during_generation_preserves_release(source_set, tmp_path, monkeypatch):
    c = Config(source_set, tmp_path / "out", data_kind="synthetic")
    previous = run_import(c)
    pointer = (c.output_dir / "current.json").read_bytes()
    write_zip(source_set / "additional.zip", [row(turn=turn, uf="AC") for turn in (1, 2)])

    def progress(message):
        if message.startswith("Consolidando"):
            monkeypatch.setattr(
                workspace.shutil, "disk_usage", lambda path: SimpleNamespace(free=100)
            )

    with pytest.raises(ImportFailure, match="min_free|max_work"):
        run_import(c, progress)
    assert (c.output_dir / "current.json").read_bytes() == pointer
    assert validate_release(previous)["structurally_valid"]
    assert not list((c.output_dir / ".work").glob("**/*.sqlite"))


def test_cached_digest_evidence_cannot_be_public_ready(source_set, tmp_path):
    catalog = inventory(source_set)
    cache = tmp_path / "hashes.json"
    cache.write_text(json.dumps(catalog), encoding="utf8")
    refs = {
        item["path"]: {
            "algorithm": "sha256",
            "digest": item["hashes"]["sha256"],
            "origin": "fictional operator reference",
            "trusted": True,
        }
        for item in catalog["files"]
    }
    from tse_importer.domain import Selection

    release = run_import(
        Config(
            source_set,
            tmp_path / "out",
            selection=Selection(territories=("SC",)),
            references=refs,
            inventory_cache=str(cache),
        )
    )
    a = read(release / "manifest.json")["assessment"]
    assert a["local_release"]["status"] == "eligible"
    assert a["source_hashes"]["evidence"] == "local_fingerprint_cache_and_current_hashes"
    assert a["public_readiness"]["blockers"] == ["source_hashes_reused_from_local_cache"]


def test_failed_diagnostic_retention_can_be_disabled(source_set, tmp_path, monkeypatch):
    c = Config(
        source_set,
        tmp_path / "out",
        data_kind="synthetic",
        storage=StoragePolicy(retain_failed_diagnostics=False),
    )

    def fail(*args):
        raise KeyboardInterrupt()

    monkeypatch.setattr(partitioned, "merge_partition", fail)
    with pytest.raises(KeyboardInterrupt):
        run_import(c)
    assert not list((c.output_dir / ".work").glob("*"))
    assert ledgers(c)[0]["status"] == "cancelled"


def test_zone_codes_and_municipality_zone_pairs_are_distinct(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    write_zip(
        root / "primary.zip",
        [
            row(turn=turn, CD_MUNICIPIO=municipality)
            for turn in (1, 2)
            for municipality in ("00001", "00002")
        ],
    )
    release = run_import(Config(root, tmp_path / "out", data_kind="synthetic"))
    totals = validate_release(release)["territory_totals"]
    assert all(
        (r["municipalities"], r["zones"], r["municipality_zone_pairs"]) == (2, 1, 2) for r in totals
    )


def test_retain_policy_preserves_units_and_partitions(source_set, tmp_path):
    c = Config(
        source_set,
        tmp_path / "out",
        data_kind="synthetic",
        storage=StoragePolicy(cleanup_policy="retain"),
    )
    release = run_import(c)
    assert validate_release(release)["structurally_valid"]
    assert len(list((c.output_dir / ".work").glob("*/checkpoints/*.sqlite"))) == 2
    assert len(list((c.output_dir / ".work").glob("*/partition-*.sqlite"))) == 6


def test_incomplete_checkpoint_not_retained(source_set, tmp_path):
    write_zip(source_set / "synthetic-section.zip", [row(), row()])
    c = Config(
        source_set,
        tmp_path / "out",
        data_kind="synthetic",
        storage=StoragePolicy(retain_checkpoints=True),
    )
    with pytest.raises(ImportFailure, match="duplicado"):
        run_import(c)
    assert not list((c.output_dir / ".work").glob("**/*.sqlite"))


def test_changed_source_reuses_only_unaffected_unit(source_set, tmp_path, monkeypatch):
    c = Config(
        source_set,
        tmp_path / "out",
        data_kind="synthetic",
        storage=StoragePolicy(retain_checkpoints=True),
    )

    def fail(*args):
        raise KeyboardInterrupt()

    original = partitioned.merge_partition
    monkeypatch.setattr(partitioned, "merge_partition", fail)
    with pytest.raises(KeyboardInterrupt):
        run_import(c)
    monkeypatch.setattr(partitioned, "merge_partition", original)
    write_zip(
        source_set / "synthetic-section.zip",
        [
            row(turn=turn, uf=uf, number=number, votes=votes)
            for turn in (1, 2)
            for uf in ("SC", "DF", "ZZ")
            for number, votes in (
                ("11", 60 if turn == 1 else 65),
                ("22", 30 if turn == 1 else 25),
                ("95", 0),
                ("96", 10),
            )
        ],
        extra={"readme.pdf": b"%PDF-example"},
    )
    release = run_import(c)
    assert read(release / "validation.json")["performance"]["checkpoints_reused"] == 1

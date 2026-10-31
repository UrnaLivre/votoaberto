"""Metadata installation must preserve payloads and concurrent edits on failure."""

import importlib.util
import json
from pathlib import Path

import pytest
from tse_importer.domain import ImportFailure
from tse_importer.provenance import sha256


@pytest.fixture
def install(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1] / "tools/provenance/prepare_release.py"
    spec = importlib.util.spec_from_file_location("metadata_install_test", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source, destination = tmp_path / "source", tmp_path / "installed"
    source.mkdir()
    destination.mkdir()
    old = b'{"synthetic":"original test manifest"}'
    (destination / "manifest.json").write_bytes(old)
    (destination / "national.json").write_bytes(b"synthetic test payload")
    (source / "national.json").write_bytes(b"synthetic test payload")
    (source / "provenance.json").write_bytes(b"synthetic test proof")
    manifest = {
        "provenance_review": {"origin_embedded_manifest_sha256": sha256(old)},
        "artifacts": {"national.json": {}, "provenance.json": {}},
    }
    (source / "manifest.json").write_text(json.dumps(manifest), encoding="utf8")
    # Policy validity is covered by test_documented_provenance; isolate atomic I/O here.
    monkeypatch.setattr(module, "resolve_release", lambda path: Path(path))
    monkeypatch.setattr(module, "validate_embedded", lambda *a: None)
    return module, source, destination, old


def test_install_changes_only_metadata(install):
    module, source, destination, old = install
    module.install_metadata(source, destination)
    assert (destination / "national.json").read_bytes() == b"synthetic test payload"
    assert (destination / "manifest.json").read_bytes() == (source / "manifest.json").read_bytes()


@pytest.mark.parametrize("failure", ["payload", "extra_fixture", "validation", "concurrent_edit"])
def test_failed_install_preserves_payload_and_operator_edits(install, monkeypatch, failure):
    module, source, destination, old = install
    if failure == "payload":
        (destination / "national.json").write_bytes(b"different synthetic payload")
    elif failure == "extra_fixture":
        (destination / "undeclared-fixture.json").write_bytes(b"{}")
    elif failure == "validation":

        def validate(path):
            if path == destination and (path / "provenance.json").exists():
                raise ImportFailure("test validation failure")

        monkeypatch.setattr(module, "validate_embedded", validate)
    else:

        def replace(source, target):
            target.write_bytes(b"operator concurrent edit")
            raise PermissionError("simulated sharing violation")

        monkeypatch.setattr(module.os, "replace", replace)
    before = (destination / "national.json").read_bytes()
    with pytest.raises((ImportFailure, PermissionError)):
        module.install_metadata(source, destination)
    expected = b"operator concurrent edit" if failure == "concurrent_edit" else old
    assert (destination / "manifest.json").read_bytes() == expected
    assert (destination / "national.json").read_bytes() == before
    assert not (destination / "provenance.json").exists()

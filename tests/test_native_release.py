"""Native release gates reuse the Web approval, without creating a second dataset."""

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest
from tse_importer.domain import ImportFailure

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "apps/votoaberto_flutter/tool"
sys.path.insert(0, str(TOOL))
import native_release as native  # noqa: E402


@pytest.mark.parametrize("version", ["0.5.0+3", "0.10.0+4", "1.0.0+65535"])
def test_versions(version):
    assert len(native.parse_version(version)) == 4


@pytest.mark.parametrize("version", ["0.5.0", "0.5.0+0", "0.5.0+03", "0.5.0-rc.1+4", "0.5.0+65536"])
def test_invalid_version(version):
    with pytest.raises(ImportFailure):
        native.parse_version(version)


@pytest.mark.parametrize("new", ["0.5.0+4", "0.5.1+4", "0.6.0+10", "0.5.0+3"])
def test_monotonic_builds(new):
    native.validate_progression("0.5.0+3", new)


@pytest.mark.parametrize("new", ["0.5.1+3", "0.6.0+2", "0.4.0+4"])
def test_regressive_build_rejected(new):
    with pytest.raises(ImportFailure):
        native.validate_progression("0.5.0+3", new)


def embedded_tool():
    spec = importlib.util.spec_from_file_location(
        "native_embedded_test", TOOL / "embedded_build.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("platform", ["appbundle", "windows"])
@pytest.mark.parametrize("mode", ["fixture", "demo"])
def test_native_production_rejects_fixture_before_flutter(platform, mode, monkeypatch):
    module = embedded_tool()
    monkeypatch.setattr(module.subprocess, "call", lambda *a, **kw: pytest.fail("Flutter invoked"))
    assert module.main([platform, "--mode", mode, "--production"]) == 2


def test_aab_never_uses_fixture_or_nonproduction():
    assert embedded_tool().main(["appbundle", "--mode", "fixture"]) == 2


@pytest.mark.parametrize(
    "flag",
    [
        "--debug",
        "--build-number=999",
        "--dart-define=VOTOABERTO_DATA=fixture",
        "--target=other.dart",
    ],
)
def test_native_production_rejects_overrides(flag):
    assert embedded_tool().main(["windows", "--mode", "real", "--production", flag]) == 2


def test_native_audit_rejects_mixed_datasets(tmp_path, monkeypatch):
    data = tmp_path / "data"
    real = data / "real"
    real.mkdir(parents=True)
    (real / "manifest.json").write_text(json.dumps({"artifacts": ["catalog.json"]}))
    (real / "catalog.json").write_text("{}")
    monkeypatch.setattr(native, "require_approved", lambda *args: {"dataset_id": "approved"})
    native.audit_dataset(data, tmp_path, {"dataset_id": "approved"})
    fixtures = data / "synthetic"
    fixtures.mkdir()
    (fixtures / "catalog.json").write_text("{}")
    with pytest.raises(ImportFailure, match="misturados"):
        native.audit_dataset(data, tmp_path, {"dataset_id": "approved"})


def test_production_requires_clean_identifiable_commit(tmp_path, monkeypatch):
    (tmp_path / "pubspec.yaml").write_text("version: 0.5.0+3\n")
    monkeypatch.setattr(native, "git", lambda *a: " M lib/main.dart")
    with pytest.raises(ImportFailure, match="checkout limpo"):
        native.prepare_build(tmp_path, "windows", {})


def test_windows_requires_complete_bundle(tmp_path):
    output = native.output_path(tmp_path, "windows")
    output.mkdir(parents=True)
    (output / "votoaberto.exe").write_bytes(b"exe only")
    with pytest.raises(ImportFailure, match="incompleto"):
        native.audit_and_record(tmp_path, "windows", {})


def test_aab_audits_actual_packaged_bytes_before_receipt(tmp_path, monkeypatch):
    output = native.output_path(tmp_path, "appbundle")
    output.parent.mkdir(parents=True)
    prefix = "base/assets/flutter_assets/assets/data/"
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(prefix + "real/manifest.json", json.dumps({"artifacts": ["catalog.json"]}))
        archive.writestr(prefix + "real/catalog.json", "{}")
    seen = []

    def approve(source, approval):
        seen.append((source / "catalog.json").read_bytes())
        return {"dataset_id": "approved"}

    monkeypatch.setattr(native, "require_approved", approve)
    report = native.audit_and_record(tmp_path, "appbundle", {"dataset_id": "approved"})
    receipt = json.loads(report.read_text())
    assert seen == [b"{}"]
    assert receipt["artifacts"][0]["path"] == "app-release.aab"
    assert len(receipt["artifacts"][0]["sha256"]) == 64


def test_existing_approval_and_web_workflow_are_shared():
    workflow = (ROOT / ".github/workflows/native-production.yml").read_text()
    assert "tool/web_release.py unpack" in workflow
    assert "votoaberto-web-data.zip" in workflow
    assert "web-data-approval.json" in workflow
    assert "contents: read" in workflow
    assert "workflow_dispatch:" in workflow
    assert "gh release create" not in workflow

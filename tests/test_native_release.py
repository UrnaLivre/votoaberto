"""Native release gates reuse the Web approval, without creating a second dataset."""

import base64
import importlib.util
import json
import os
import secrets
import shutil
import subprocess
import sys
import textwrap
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


def test_windows_requires_complete_bundle(tmp_path, monkeypatch):
    monkeypatch.setattr(native, "git", lambda app, *args: "" if args[0] == "status" else "commit")
    output = native.output_path(tmp_path, "windows")
    output.mkdir(parents=True)
    (output / "votoaberto.exe").write_bytes(b"exe only")
    with pytest.raises(ImportFailure, match="incompleto"):
        native.audit_and_record(tmp_path, "windows", {"commit": "commit"})


def test_aab_audits_actual_packaged_bytes_before_receipt(tmp_path, monkeypatch):
    monkeypatch.setattr(native, "git", lambda app, *args: "" if args[0] == "status" else "commit")
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
    report = native.audit_and_record(
        tmp_path, "appbundle", {"dataset_id": "approved", "commit": "commit"}
    )
    receipt = json.loads(report.read_text())
    assert seen == [b"{}"]
    assert receipt["artifacts"][0]["path"] == "app-release.aab"
    assert len(receipt["artifacts"][0]["sha256"]) == 64
    assert native.android_distribution_path(tmp_path).read_bytes() == output.read_bytes()
    output.write_bytes(b"raw Gradle output changed after audit")
    assert native.android_distribution_path(tmp_path).read_bytes() != output.read_bytes()


@pytest.mark.parametrize("status,head", [(" M lib/main.dart", "commit"), ("", "another-commit")])
def test_source_change_during_build_never_gets_a_release_receipt(
    tmp_path, monkeypatch, status, head
):
    monkeypatch.setattr(native, "git", lambda app, *args: status if args[0] == "status" else head)
    with pytest.raises(ImportFailure, match="mudou durante"):
        native.audit_and_record(tmp_path, "windows", {"commit": "commit"})


def test_existing_approval_and_web_workflow_are_shared():
    workflow = (ROOT / ".github/workflows/native-production.yml").read_text()
    assert "tool/web_release.py unpack" in workflow
    assert "votoaberto-web-data.zip" in workflow
    assert "web-data-approval.json" in workflow
    assert "contents: read" in workflow
    assert "workflow_dispatch:" in workflow
    assert "gh release create" not in workflow


def encode_defines(values):
    return ",".join(
        base64.b64encode(f"{key}={value}".encode()).decode() for key, value in values.items()
    )


@pytest.fixture
def android_context(tmp_path, monkeypatch):
    app = tmp_path / "app"
    data = app / "assets/data/real"
    data.mkdir(parents=True)
    (data / "manifest.json").write_text(json.dumps({"artifacts": ["catalog.json"]}))
    (data / "catalog.json").write_bytes(b"{}")
    (app / "pubspec.yaml").write_text(
        "version: 0.5.0+3\nflutter:\n  assets:\n    # BEGIN EMBEDDED ASSETS\n    - assets/data/real/\n    - assets/data/real/municipalities/\n    # END EMBEDDED ASSETS\n"
    )
    (app / ".embedded-build.lock").touch()
    (app / "web-data-approval.json").write_text(
        json.dumps({"release_tag": "approved", "metadata_release_id": "metadata"})
    )
    meta = {"dataset_id": "approved", "manifest_sha256": "a" * 64}

    def approve(source, approval):
        if (source / "catalog.json").read_bytes() != b"{}":
            raise ImportFailure("Actual packaged bytes are not approved")
        return meta

    monkeypatch.setattr(native, "require_approved", approve)
    monkeypatch.setattr(native, "git", lambda app, *args: "" if args[0] == "status" else "commit")
    values = {
        "VOTOABERTO_DATA": "real",
        "VOTOABERTO_DATASET": "approved",
        "VOTOABERTO_MANIFEST_SHA256": "a" * 64,
        "VOTOABERTO_APP_COMMIT": "commit",
        "VOTOABERTO_DATA_RELEASE": "approved",
        "FLUTTER_BUILD_NUMBER": "3",
    }
    environment = {
        "VOTOABERTO_RELEASE_PYTHON": sys.executable,
        "VOTOABERTO_GRADLE_DART_DEFINES": encode_defines(values),
    }
    return app, environment, values


def test_android_preflight_requires_active_wrapper(android_context):
    app, environment, _ = android_context
    with pytest.raises(ImportFailure, match="contexto ativo"):
        native.android_preflight(app, {})
    (app / ".embedded-build.lock").unlink()
    with pytest.raises(ImportFailure, match="contexto ativo"):
        native.android_preflight(app, environment)


@pytest.mark.parametrize(
    "key,value",
    [
        ("VOTOABERTO_DATA", "demo"),
        ("VOTOABERTO_DATA", "fixture"),
        ("VOTOABERTO_MANIFEST_SHA256", "b" * 64),
        ("VOTOABERTO_APP_COMMIT", "other"),
        ("VOTOABERTO_DATASET", "unapproved"),
        ("FLUTTER_BUILD_NUMBER", "999"),
    ],
)
def test_android_preflight_rejects_incompatible_effective_defines(android_context, key, value):
    app, environment, values = android_context
    values[key] = value
    environment["VOTOABERTO_GRADLE_DART_DEFINES"] = encode_defines(values)
    with pytest.raises(ImportFailure):
        native.android_preflight(app, environment)


@pytest.mark.parametrize(
    "encoded", ["", "not base64", encode_defines({"A": "1"}) + "," + encode_defines({"A": "2"})]
)
def test_android_preflight_rejects_missing_malformed_duplicate_defines(android_context, encoded):
    app, environment, _ = android_context
    environment["VOTOABERTO_GRADLE_DART_DEFINES"] = encoded
    with pytest.raises(ImportFailure):
        native.android_preflight(app, environment)


def test_android_preflight_checks_files_not_just_claimed_hashes(android_context):
    app, environment, _ = android_context
    native.android_preflight(app, environment)
    (app / "assets/data/real/catalog.json").write_bytes(b"tampered")
    with pytest.raises(ImportFailure, match="not approved"):
        native.android_preflight(app, environment)


@pytest.mark.parametrize("change", ["assets", "target"])
def test_android_preflight_rejects_other_assets_or_entrypoint(android_context, change):
    app, environment, _ = android_context
    if change == "assets":
        pubspec = app / "pubspec.yaml"
        pubspec.write_text(
            pubspec.read_text().replace("assets/data/real/", "assets/data/synthetic/")
        )
    else:
        environment["VOTOABERTO_GRADLE_TARGET"] = "lib/other.dart"
    with pytest.raises(ImportFailure):
        native.android_preflight(app, environment)


def test_real_approval_rejects_fixture_despite_forged_production_context(tmp_path):
    (tmp_path / ".embedded-build.lock").touch()
    shutil.copytree(
        ROOT / "apps/votoaberto_flutter/assets/data/synthetic", tmp_path / "assets/data/real"
    )
    shutil.copyfile(
        ROOT / "apps/votoaberto_flutter/web-data-approval.json", tmp_path / "web-data-approval.json"
    )
    with pytest.raises(ImportFailure):
        native.android_preflight(
            tmp_path,
            {
                "VOTOABERTO_RELEASE_PYTHON": sys.executable,
                "VOTOABERTO_GRADLE_DART_DEFINES": encode_defines({"VOTOABERTO_DATA": "real"}),
            },
        )


def accepted_aab(app):
    output = native.output_path(app, "appbundle")
    output.parent.mkdir(parents=True)
    with zipfile.ZipFile(output, "w") as archive:
        for name in ["manifest.json", "catalog.json"]:
            archive.write(
                app / "assets/data/real" / name,
                "base/assets/flutter_assets/assets/data/real/" + name,
            )
    info = native.prepare_build(
        app, "appbundle", {"dataset_id": "approved", "manifest_sha256": "a" * 64}
    )
    report = native.audit_and_record(app, "appbundle", info)
    return native.android_distribution_path(app), report


def test_official_android_distribution_requires_receipt_and_reaudits_content(android_context):
    app, _, _ = android_context
    accepted, report = accepted_aab(app)
    assert native.verify_android_distribution(app) == accepted
    # Forge a matching checksum/receipt for altered bytes: content audit still rejects it.
    with zipfile.ZipFile(accepted, "w") as archive:
        archive.writestr("base/assets/flutter_assets/assets/data/real/catalog.json", b"tampered")
    receipt = json.loads(report.read_text())
    receipt["artifacts"] = [native.artifact_hash(accepted, accepted.parent)]
    report.write_text(json.dumps(receipt))
    with pytest.raises(ImportFailure, match="not approved"):
        native.verify_android_distribution(app)


@pytest.mark.parametrize("change", ["receipt", "artifact", "commit", "hash"])
def test_official_android_distribution_rejects_missing_or_stale_acceptance(android_context, change):
    app, _, _ = android_context
    accepted, report = accepted_aab(app)
    if change == "receipt":
        report.unlink()
    elif change == "artifact":
        accepted.unlink()
    elif change == "commit":
        receipt = json.loads(report.read_text())
        receipt["commit"] = "other"
        report.write_text(json.dumps(receipt))
    else:
        accepted.write_bytes(b"replaced after audit")
    with pytest.raises((ImportFailure, OSError)):
        native.verify_android_distribution(app)


def test_clean_native_build_invalidates_previous_accepted_aab(android_context):
    app, _, _ = android_context
    accepted, report = accepted_aab(app)
    native.clean_output(app, "appbundle")
    assert not accepted.exists() and not report.exists()


def test_native_workflow_rejects_non_main_and_uploads_only_accepted_android_bytes():
    workflow = (ROOT / ".github/workflows/native-production.yml").read_text()
    assert 'test "$PRODUCTION_REF" = refs/heads/main' in workflow
    assert "needs: authorize-ref" in workflow
    assert "if: github.ref == 'refs/heads/main'" in workflow
    assert "environment: native-production" in workflow
    assert workflow.index("tool/native_release.py verify-android") < workflow.index(
        "uses: actions/upload-artifact"
    )
    assert "build/native-release/appbundle/app-release.aab" in workflow
    assert "build/app/outputs/bundle/release/app-release.aab" not in workflow
    quality = (ROOT / ".github/workflows/data-engine.yml").read_text()
    assert quality.count("'.github/workflows/native-production.yml'") == 2
    assert "docker://rhysd/actionlint:1.7.12" in quality


@pytest.mark.parametrize(
    "ref,allowed",
    [
        ("refs/heads/main", True),
        ("refs/heads/feat/native-release-foundation", False),
        ("refs/tags/main", False),
        ("refs/pull/10/merge", False),
    ],
)
def test_native_ref_guard_executes_for_refs(ref, allowed):
    workflow = (ROOT / ".github/workflows/native-production.yml").read_text()
    guard = textwrap.dedent(workflow.split("run: |\n", 1)[1].split("\n\n", 1)[0])
    bash = shutil.which("bash")
    if os.name == "nt":
        candidate = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git/bin/bash.exe"
        bash = str(candidate) if candidate.is_file() else bash
    if not bash:
        pytest.skip("Bash required; covered by Ubuntu CI")
    result = subprocess.run(
        [bash, "-c", guard],
        env={**os.environ, "PRODUCTION_REF": ref},
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == (0 if allowed else 1)


@pytest.mark.skipif(
    os.environ.get("RUN_ANDROID_RELEASE_GATES") != "true",
    reason="opt-in Android SDK/Gradle integration",
)
def test_gradle_release_gates_without_key_and_outside_wrapper(tmp_path):
    app = ROOT / "apps/votoaberto_flutter"
    if (app / "android/key.properties").exists():
        pytest.skip("Preserve the operator's local signing configuration")
    environment = dict(os.environ)
    for key in [
        "ANDROID_UPLOAD_STORE_FILE",
        "ANDROID_UPLOAD_STORE_PASSWORD",
        "ANDROID_UPLOAD_KEY_ALIAS",
        "ANDROID_UPLOAD_KEY_PASSWORD",
        "VOTOABERTO_RELEASE_PYTHON",
    ]:
        environment.pop(key, None)
    gradle = str(app / "android" / ("gradlew.bat" if os.name == "nt" else "gradlew"))
    command = [gradle, ":app:bundleRelease", "--dry-run", "--console=plain"]

    def rejected(expected):
        result = subprocess.run(
            command,
            cwd=app / "android",
            env=environment,
            capture_output=True,
            text=True,
            timeout=600,
        )
        assert result.returncode != 0
        assert expected in result.stdout + result.stderr, (
            "Gradle did not reject at the expected production gate"
        )

    rejected("Release requires an operator-controlled upload key")
    # Ephemeral, unmistakably non-production signing identity; never printed/uploaded.
    environment["VOTOABERTO_TEST_KEY_PASSWORD"] = secrets.token_urlsafe(24)
    key = tmp_path / "m71-temporary-test.jks"
    subprocess.run(
        [
            shutil.which("keytool") or "keytool",
            "-genkeypair",
            "-keystore",
            str(key),
            "-alias",
            "m71-test-only",
            "-storepass:env",
            "VOTOABERTO_TEST_KEY_PASSWORD",
            "-keypass:env",
            "VOTOABERTO_TEST_KEY_PASSWORD",
            "-keyalg",
            "RSA",
            "-keysize",
            "2048",
            "-validity",
            "1",
            "-dname",
            "CN=VotoAberto M7.1 Temporary Test",
        ],
        env=environment,
        capture_output=True,
        check=True,
        timeout=60,
    )
    environment.update(
        ANDROID_UPLOAD_STORE_FILE=str(key),
        ANDROID_UPLOAD_KEY_ALIAS="m71-test-only",
        ANDROID_UPLOAD_STORE_PASSWORD=environment["VOTOABERTO_TEST_KEY_PASSWORD"],
        ANDROID_UPLOAD_KEY_PASSWORD=environment["VOTOABERTO_TEST_KEY_PASSWORD"],
    )
    try:
        rejected("Android Release requires tool/embedded_build.py")
        environment["VOTOABERTO_RELEASE_PYTHON"] = sys.executable
        rejected("Android Release preflight rejected")
    finally:
        key.unlink(missing_ok=True)

"""Release gates must reject preview data, tampered assets and unsafe bundles."""

import importlib.util
import json
import shutil
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def tool():
    spec = importlib.util.spec_from_file_location(
        "web_release_test", ROOT / "apps/votoaberto_flutter/tool/web_release.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def artifact(tmp_path):
    module = tool()
    build = tmp_path / "web"
    for name in [
        "index.html",
        "flutter_bootstrap.js",
        "flutter.js",
        "main.dart.js",
        "manifest.json",
        "favicon.png",
        "icons/Icon-192.png",
        "icons/Icon-512.png",
        "icons/Icon-maskable-192.png",
        "icons/Icon-maskable-512.png",
        "canvaskit/canvaskit.js",
        "canvaskit/canvaskit.wasm",
        "assets/AssetManifest.bin",
        "assets/FontManifest.json",
        "assets/NOTICES",
    ]:
        target = build / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("test fixture", encoding="utf8")
    (build / "index.html").write_text('<base href="/">', encoding="utf8")
    (build / "flutter_bootstrap.js").write_text('{"useLocalCanvasKit":true}', encoding="utf8")
    shutil.copyfile(module.APP / "web/_headers", build / "_headers")
    for folder in ["geo", "fonts", "data/synthetic"]:
        shutil.copytree(module.APP / "assets" / folder, build / "assets/assets" / folder)
    meta = module.build_metadata(build / "assets/assets/data/synthetic", "synthetic")
    (build / "web-build.json").write_text(
        json.dumps({"data_mode": "fixture", **meta}), encoding="utf8"
    )
    return module, build


def test_fixture_artifact_valid_but_never_public(artifact):
    module, build = artifact
    report = module.audit(build, "fixture")
    assert report["cloudflare_free_limits"]["passed"] is True
    assert report["production_approved"] is False
    with pytest.raises(module.ImportFailure, match="Fixtures nunca"):
        module.audit(build, "fixture", production=True)


@pytest.mark.parametrize("path", ["main.dart.js", "assets/assets/fonts/roboto-regular.ttf"])
def test_missing_required_resources_fail(artifact, path):
    module, build = artifact
    (build / path).unlink()
    with pytest.raises(module.ImportFailure, match="ausente"):
        module.audit(build, "fixture")


def test_electoral_tampering_is_rejected(artifact):
    module, build = artifact
    data = build / "assets/assets/data/synthetic/national.json"
    data.write_bytes(data.read_bytes() + b" ")
    with pytest.raises(module.ImportFailure, match="Hash/tamanho"):
        module.audit(build, "fixture")


def test_mixed_assets_are_rejected(artifact):
    module, build = artifact
    target = build / "assets/assets/data/real/leaked.json"
    target.parent.mkdir()
    target.write_text("{}", encoding="utf8")
    with pytest.raises(module.ImportFailure, match="misturados"):
        module.audit(build, "fixture")


@pytest.mark.parametrize("limit", ["MAX_FILES", "MAX_FILE_BYTES"])
def test_cloudflare_limit_violation_blocks_release(artifact, monkeypatch, limit):
    module, build = artifact
    monkeypatch.setattr(module, limit, 1)
    with pytest.raises(module.ImportFailure, match="limites Workers Free"):
        module.audit(build, "fixture")


@pytest.mark.parametrize(
    "readiness",
    [
        {"status": "not_ready", "blockers": ["source_hashes_reused_from_local_cache"]},
        {"status": "ready_for_declared_scope", "blockers": ["operator_trusted_hashes_incomplete"]},
        {},
    ],
)
def test_readiness_cannot_be_overridden_by_operator_approval(tmp_path, monkeypatch, readiness):
    module = tool()
    (tmp_path / "manifest.json").write_text(
        json.dumps({"public_readiness": readiness}), encoding="utf8"
    )
    monkeypatch.setattr(module, "resolve_release", lambda path: tmp_path)
    monkeypatch.setattr(module, "build_metadata", lambda *args: {})
    with pytest.raises(module.ImportFailure, match="avaliação dos dados"):
        module.require_approved(tmp_path)


def test_approval_pins_exact_dataset_and_terms(tmp_path, monkeypatch):
    module = tool()
    ready = {"status": "ready_for_declared_scope", "blockers": []}
    (tmp_path / "manifest.json").write_text(
        json.dumps(
            {
                "public_readiness": ready,
                "source_assessment": {"public_readiness": ready},
            }
        ),
        encoding="utf8",
    )
    monkeypatch.setattr(module, "resolve_release", lambda path: tmp_path)
    meta = {"dataset_id": "test-only", "manifest_sha256": "a" * 64}
    monkeypatch.setattr(module, "build_metadata", lambda *args: meta)
    approval = tmp_path / "approval.json"
    payload = {
        **meta,
        "release_tag": "test-only",
        "redistribution_review": {
            "approved": True,
            "source_terms_url": "https://example.org/terms",
            "reviewed_by": "test operator",
            "reviewed_on": "2026-10-31",
        },
    }
    approval.write_text(json.dumps(payload), encoding="utf8")
    assert module.require_approved(tmp_path, approval) == meta
    payload["manifest_sha256"] = "b" * 64
    approval.write_text(json.dumps(payload), encoding="utf8")
    with pytest.raises(module.ImportFailure, match="aprovação"):
        module.require_approved(tmp_path, approval)


@pytest.mark.parametrize("name", ["../escape.json", "C:/escape.json", "nested\\escape.json"])
def test_untrusted_bundle_cannot_escape_destination(tmp_path, name):
    module = tool()
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as file:
        file.writestr("manifest.json", json.dumps({"artifacts": {name: {}}}))
        file.writestr(name, "{}")
    with pytest.raises(module.ImportFailure, match="Caminho/tamanho|manifesto"):
        module.unpack(archive, tmp_path / "destination")
    assert not (tmp_path / "destination").exists()


def test_bundle_roundtrip_preserves_every_byte(tmp_path, monkeypatch):
    module = tool()
    # A synthetic transport test; it does not approve fixtures for deployment.
    monkeypatch.setattr(
        module,
        "require_approved",
        lambda source, approval_path=None: module.build_metadata(source, "synthetic"),
    )
    source = module.APP / "assets/data/synthetic"
    archive = tmp_path / "transport.zip"
    destination = tmp_path / "restored"
    module.bundle(source, archive)
    module.unpack(archive, destination)
    for file in source.rglob("*.json"):
        assert (destination / file.relative_to(source)).read_bytes() == file.read_bytes()

"""The build preflight must fail before Flutter, and restore packaging on failure."""

import importlib.util
from pathlib import Path

from tse_importer.domain import Config
from tse_importer.embedded_assets import install_assets
from tse_importer.embedded_exporter import export_embedded
from tse_importer.engine import run_import


def tool():
    path = Path(__file__).resolve().parents[1] / "apps/votoaberto_flutter/tool/embedded_build.py"
    spec = importlib.util.spec_from_file_location("embedded_build_test_target", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_real_assets_never_invokes_flutter(tmp_path, monkeypatch):
    module = tool()
    monkeypatch.setattr(module, "APP", tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("Flutter should not run")

    monkeypatch.setattr(module.subprocess, "call", forbidden)
    assert module.main(["web", "--mode", "real"]) == 2
    assert not (tmp_path / ".embedded-build.lock").exists()


def test_only_selected_assets_and_restore_even_failed_build(source_set, tmp_path, monkeypatch):
    module = tool()
    release = run_import(Config(source_set, tmp_path / "sqlite", data_kind="synthetic"))
    embedded = Path(export_embedded(release, tmp_path / "embedded")["release"])
    app = tmp_path / "app"
    app.mkdir()
    install_assets(embedded, app / "assets/data/synthetic")
    original = b"flutter:\r\n  assets:\r\n    # BEGIN EMBEDDED ASSETS\r\n    - assets/data/real/\r\n    # END EMBEDDED ASSETS\r\n"
    (app / "pubspec.yaml").write_bytes(original)
    monkeypatch.setattr(module, "APP", app)

    def fail_build(command, cwd, env):
        selected = (app / "pubspec.yaml").read_text(encoding="utf8")
        assert "assets/data/synthetic/municipalities/" in selected
        assert "assets/data/real/" not in selected
        assert "--dart-define=VOTOABERTO_DATA=fixture" in command
        assert "--pwa-strategy=none" in command
        assert cwd == app
        return 17

    monkeypatch.setattr(module.subprocess, "call", fail_build)
    assert module.main(["web", "--mode", "fixture", "--flutter", "fake-flutter"]) == 17
    assert (app / "pubspec.yaml").read_bytes() == original
    assert not (app / ".embedded-build.lock").exists()

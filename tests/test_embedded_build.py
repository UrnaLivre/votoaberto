"""The build preflight must fail before Flutter, and restore packaging on failure."""

import importlib.util
import os
import subprocess
from pathlib import Path

import pytest
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


@pytest.mark.parametrize("outcome", [0, 17, "launch_error"])
def test_only_selected_assets_and_restore_after_build(
    source_set, tmp_path, monkeypatch, capsys, outcome
):
    module = tool()
    release = run_import(Config(source_set, tmp_path / "sqlite", data_kind="synthetic"))
    embedded = Path(export_embedded(release, tmp_path / "embedded")["release"])
    app = tmp_path / "app"
    app.mkdir()
    install_assets(embedded, app / "assets/data/synthetic")
    original = b"flutter:\r\n  assets:\r\n    # BEGIN EMBEDDED ASSETS\r\n    - assets/data/real/\r\n    # END EMBEDDED ASSETS\r\n"
    (app / "pubspec.yaml").write_bytes(original)
    stale = app / "build/web/assets/assets/data/real/leftover.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("previous build only", encoding="utf8")
    monkeypatch.setattr(module, "APP", app)
    resolved = tmp_path / "Flutter SDK with spaces" / "flutter.bat"
    monkeypatch.setattr(module.shutil, "which", lambda name: str(resolved))

    def build(command, cwd, env, shell):
        assert not stale.exists(), "A Web build must not leak another mode's assets"
        selected = (app / "pubspec.yaml").read_text(encoding="utf8")
        assert "assets/data/synthetic/municipalities/" in selected
        assert "assets/data/real/" not in selected
        assert "--dart-define=VOTOABERTO_DATA=fixture" in command
        meta = module.build_metadata(app / "assets/data/synthetic", "synthetic")
        assert "--dart-define=VOTOABERTO_DATASET=" + meta["dataset_id"] in command
        assert "--dart-define=VOTOABERTO_MANIFEST_SHA256=" + meta["manifest_sha256"] in command
        assert "--pwa-strategy=none" in command
        assert command[0] == str(resolved.resolve())
        assert command[-1] == "assets path with spaces.dart"
        assert shell is False
        assert cwd == app
        if outcome == "launch_error":
            raise PermissionError("execução recusada")
        return outcome

    monkeypatch.setattr(module.subprocess, "call", build)
    code = module.main(
        [
            "web",
            "--mode",
            "fixture",
            "--flutter",
            "fake-flutter",
            "--target",
            "assets path with spaces.dart",
        ]
    )
    assert code == (2 if outcome == "launch_error" else outcome)
    error = capsys.readouterr().err
    if outcome == 17:
        assert "Comando Flutter falhou (código 17)" in error
    elif outcome == "launch_error":
        assert "Não foi possível iniciar o Flutter resolvido" in error
    else:
        assert not error
    assert (app / "pubspec.yaml").read_bytes() == original
    assert not (app / ".embedded-build.lock").exists()


@pytest.mark.parametrize("filename", ["flutter.bat", "flutter"])
def test_resolver_uses_path_result_as_one_absolute_argument(tmp_path, monkeypatch, filename):
    module = tool()
    resolved = tmp_path / "SDK with spaces" / filename
    requests = []

    def which(name):
        requests.append(name)
        return str(resolved)

    monkeypatch.setattr(module.shutil, "which", which)
    assert module.resolve_flutter("flutter") == str(resolved.resolve())
    assert requests == ["flutter"]


def fake_flutter(tmp_path):
    folder = tmp_path / "SDK with spaces" / "bin"
    folder.mkdir(parents=True)
    script = folder / ("flutter.bat" if os.name == "nt" else "flutter")
    script.write_text(
        "@echo off\necho [%~1]\nexit /b 0\n"
        if os.name == "nt"
        else '#!/bin/sh\nprintf "[%s]\\n" "$1"\n',
        encoding="utf8",
    )
    script.chmod(0o755)
    return script


def test_native_path_resolution_and_launch_preserve_spaces(tmp_path, monkeypatch):
    """Runs real shutil.which and subprocess on the Windows/Linux CI matrix."""
    module = tool()
    script = fake_flutter(tmp_path)
    monkeypatch.setenv("PATH", str(script.parent) + os.pathsep + os.environ.get("PATH", ""))
    if os.name == "nt":
        monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    resolved = module.resolve_flutter("flutter")
    assert Path(resolved) == script.resolve()
    result = subprocess.run(
        [resolved, "argument with spaces"], capture_output=True, text=True, check=True, shell=False
    )
    assert result.stdout.strip() == "[argument with spaces]"


def test_explicit_relative_and_absolute_paths_use_operator_cwd(tmp_path, monkeypatch):
    module = tool()
    script = fake_flutter(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "APP", tmp_path / "another application directory")
    assert module.resolve_flutter(str(script)) == str(script.resolve())
    assert module.resolve_flutter(str(script.relative_to(tmp_path))) == str(script.resolve())
    if os.name == "nt":
        assert module.resolve_flutter(str(script.with_suffix(""))) == str(script.resolve())
        assert module.resolve_flutter(str(script.with_suffix("").relative_to(tmp_path))) == str(
            script.resolve()
        )


def legacy_explicit_which(monkeypatch, module):
    """Reproduce Python 3.11's direct check before PATHEXT for a directory path."""
    native_which = module.shutil.which

    def which(command):
        if os.path.dirname(command):
            return command if os.path.isfile(command) and os.access(command, os.X_OK) else None
        return native_which(command)

    monkeypatch.setattr(module.shutil, "which", which)


@pytest.mark.skipif(os.name != "nt", reason="Windows PATHEXT compatibility")
@pytest.mark.parametrize("legacy", [False, True], ids=["native", "python311_semantics"])
@pytest.mark.parametrize("relative", [False, True], ids=["absolute", "relative"])
@pytest.mark.parametrize("extension", [False, True], ids=["extensionless", "bat"])
def test_windows_explicit_paths_across_which_versions(
    tmp_path, monkeypatch, legacy, relative, extension
):
    module = tool()
    script = fake_flutter(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    monkeypatch.setattr(module, "APP", tmp_path / "different app directory")
    if legacy:
        legacy_explicit_which(monkeypatch, module)
    requested = script if extension else script.with_suffix("")
    if relative:
        requested = requested.relative_to(tmp_path)
    assert Path(module.resolve_flutter(str(requested))) == script.resolve()


@pytest.mark.skipif(os.name != "nt", reason="Windows PATHEXT compatibility")
def test_legacy_fallback_obeys_pathext_order_and_ignores_directory_components(
    tmp_path, monkeypatch
):
    module = tool()
    script = fake_flutter(tmp_path)
    command_script = script.with_suffix(".cmd")
    command_script.write_bytes(script.read_bytes())
    legacy_explicit_which(monkeypatch, module)
    # Only suffixes can participate; malformed entries must not change directory.
    monkeypatch.setenv("PATHEXT", r"..\elsewhere\flutter.BAT;BAT;.CMD;.BAT")
    assert Path(module.resolve_flutter(str(script.with_suffix("")))) == command_script.resolve()
    monkeypatch.setenv("PATHEXT", ".BAT;.CMD")
    assert Path(module.resolve_flutter(str(script.with_suffix("")))) == script.resolve()
    monkeypatch.setenv("PATHEXT", ".EXE")
    with pytest.raises(module.ImportFailure, match="Executável Flutter não encontrado"):
        module.resolve_flutter(str(script.with_suffix("")))


@pytest.mark.skipif(os.name != "nt", reason="Windows PATHEXT compatibility")
@pytest.mark.parametrize("kind", ["missing", "directory", "not_executable"])
def test_legacy_fallback_requires_existing_executable_file(tmp_path, monkeypatch, kind):
    module = tool()
    folder = tmp_path / "Explicit SDK with spaces"
    folder.mkdir()
    candidate = folder / "flutter.bat"
    if kind == "directory":
        candidate.mkdir()
    elif kind == "not_executable":
        candidate.write_text("@echo off\n", encoding="utf8")
        monkeypatch.setattr(module.os, "access", lambda *args: False)
    monkeypatch.setenv("PATHEXT", ".BAT")
    legacy_explicit_which(monkeypatch, module)
    with pytest.raises(module.ImportFailure, match="Executável Flutter não encontrado"):
        module.resolve_flutter(str(candidate.with_suffix("")))


def test_explicit_missing_path_never_falls_back_to_path(tmp_path, monkeypatch):
    module = tool()
    script = fake_flutter(tmp_path)
    monkeypatch.setenv("PATH", str(script.parent) + os.pathsep + os.environ.get("PATH", ""))
    with pytest.raises(module.ImportFailure, match="Executável Flutter não encontrado"):
        module.resolve_flutter(str(tmp_path / "missing SDK" / "flutter"))


def test_missing_flutter_has_clear_error_before_pubspec_change(tmp_path, monkeypatch, capsys):
    module = tool()
    monkeypatch.setattr(module, "APP", tmp_path)
    monkeypatch.setattr(module.shutil, "which", lambda name: None)
    monkeypatch.setattr(
        module.subprocess, "call", lambda *a, **kw: pytest.fail("Should not launch")
    )
    assert module.main(["windows", "--mode", "demo"]) == 2
    assert "Executável Flutter não encontrado: flutter" in capsys.readouterr().err
    assert not (tmp_path / "pubspec.yaml").exists()
    assert not (tmp_path / ".embedded-build.lock").exists()

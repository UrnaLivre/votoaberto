"""Native production version/provenance gate and packaged-data audit. No publishing."""

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "pipelines"))
from tse_importer.domain import ImportFailure  # noqa: E402
from tse_importer.workspace import no_links  # noqa: E402
from web_release import require_approved  # noqa: E402

VERSION = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)\+([1-9]\d*)")


def parse_version(value):
    match = VERSION.fullmatch(value)
    if not match or any(int(part) > 65535 for part in match.groups()):
        raise ImportFailure("Versão estável exige X.Y.Z+N; componentes <=65535; N >0")
    return tuple(int(part) for part in match.groups())


def validate_progression(previous, current):
    old, new = parse_version(previous), parse_version(current)
    if new != old and (new[:3] < old[:3] or new[3] <= old[3]):
        raise ImportFailure("Nova versão exige produto não regressivo e build number crescente")


def app_version(app):
    return version_from_pubspec((app / "pubspec.yaml").read_text("utf8"))


def version_from_pubspec(text):
    match = re.search(r"^version: (\S+)\s*$", text, re.M)
    if not match:
        raise ImportFailure("Versão ausente no pubspec")
    parse_version(match[1])
    return match[1]


def git(app, *arguments):
    return subprocess.check_output(["git", *arguments], cwd=app, text=True).strip()


def prepare_build(app, platform, meta):
    version = app_version(app)
    if git(app, "status", "--porcelain"):
        raise ImportFailure("Build nativo de produção exige checkout limpo e commit identificável")
    commit = git(app, "rev-parse", "HEAD")
    approval = json.loads((app / "web-data-approval.json").read_text("utf8"))
    return {
        "schema_version": 1,
        "repository": "UrnaLivre/votoaberto",
        "platform": platform,
        "version": version,
        "app_release_tag": "app-v" + version,
        "windows_file_version": ".".join(map(str, parse_version(version))),
        "commit": commit,
        "data_mode": "real",
        "data_release_tag": approval["release_tag"],
        "metadata_release_id": approval["metadata_release_id"],
        **meta,
    }


def output_path(app, platform):
    return app / (
        "build/windows/x64/runner/Release"
        if platform == "windows"
        else "build/app/outputs/bundle/release/app-release.aab"
    )


def clean_output(app, platform):
    output = output_path(app, platform)
    no_links(output)
    if not output.resolve().is_relative_to((app / "build").resolve()):
        raise ImportFailure("Limpeza nativa fora da área de build recusada")
    if output.is_dir():
        shutil.rmtree(output)
    else:
        output.unlink(missing_ok=True)
    (app / "build/native-release" / platform / "native-release.json").unlink(missing_ok=True)
    if platform == "appbundle":
        accepted = android_distribution_path(app)
        no_links(accepted)
        accepted.unlink(missing_ok=True)


def android_preflight(app, environment):
    """Intent is not integrity proof: verify actual assets and effective Gradle inputs."""
    if (
        not environment.get("VOTOABERTO_RELEASE_PYTHON")
        or not (app / ".embedded-build.lock").is_file()
    ):
        raise ImportFailure("Android Release exige o contexto ativo do wrapper de produção")
    meta = require_approved(app / "assets/data/real", app / "web-data-approval.json")
    entries = re.findall(
        r"^\s*-\s+(assets/data/\S+)\s*$", (app / "pubspec.yaml").read_text("utf8"), re.M
    )
    if entries != ["assets/data/real/", "assets/data/real/municipalities/"]:
        raise ImportFailure("Android Release exige exclusivamente os assets reais aprovados")
    target = Path(environment.get("VOTOABERTO_GRADLE_TARGET", "lib/main.dart"))
    if not target.is_absolute():
        target = app / target
    if target.resolve() != (app / "lib/main.dart").resolve():
        raise ImportFailure("Entrypoint Android de produção divergente")
    defines = {}
    for encoded in environment.get("VOTOABERTO_GRADLE_DART_DEFINES", "").split(","):
        try:
            key, value = base64.b64decode(encoded, validate=True).decode("utf8").split("=", 1)
        except (ValueError, UnicodeError) as error:
            raise ImportFailure("Dart defines Android ausentes ou inválidos") from error
        if key in defines:
            raise ImportFailure("Dart defines Android duplicados")
        defines[key] = value
    expected = {
        "VOTOABERTO_DATA": "real",
        "VOTOABERTO_DATASET": meta["dataset_id"],
        "VOTOABERTO_MANIFEST_SHA256": meta["manifest_sha256"],
        "VOTOABERTO_APP_COMMIT": git(app, "rev-parse", "HEAD"),
        "VOTOABERTO_DATA_RELEASE": json.loads((app / "web-data-approval.json").read_text("utf8"))[
            "release_tag"
        ],
    }
    if any(defines.get(key) != value for key, value in expected.items()):
        raise ImportFailure("Configuração Android Release diverge dos arquivos aprovados")
    version = app_version(app).split("+")
    if (
        defines.get("FLUTTER_BUILD_NAME", version[0]) != version[0]
        or defines.get("FLUTTER_BUILD_NUMBER", version[1]) != version[1]
    ):
        raise ImportFailure("Versão Android Release divergente")
    return meta


def android_distribution_path(app):
    return app / "build/native-release/appbundle/app-release.aab"


def audit_android_bundle(output, app, info):
    prefix = "base/assets/flutter_assets/assets/data/"
    with zipfile.ZipFile(output) as archive, tempfile.TemporaryDirectory(dir=output.parent) as temp:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ImportFailure("AAB contém caminhos duplicados")
        for name in names:
            if not name.startswith(prefix) or name.endswith("/"):
                continue
            relative = name[len(prefix) :]
            path = Path(relative)
            if path.is_absolute() or ".." in path.parts or "\\" in relative or ":" in relative:
                raise ImportFailure("Caminho inválido no AAB")
            target = Path(temp) / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
        audit_dataset(Path(temp), app, info)


def artifact_hash(path, root):
    return {
        "path": path.relative_to(root).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def audit_dataset(root, app, info):
    """Validate the actual package, including all hashes and absence of fixtures."""
    real = root / "real"
    meta = require_approved(real, app / "web-data-approval.json")
    if any(info.get(key) != value for key, value in meta.items()):
        raise ImportFailure("Dados empacotados divergem do preflight")
    manifest = json.loads((real / "manifest.json").read_text("utf8"))
    expected = {"manifest.json", *manifest["artifacts"]}
    files = [p for p in root.rglob("*") if p.is_file() and p.name != ".gitkeep"]
    if (
        any(not p.is_relative_to(real) for p in files)
        or {p.relative_to(real).as_posix() for p in files} != expected
    ):
        raise ImportFailure("Pacote nativo contém dados misturados ou não declarados")


def audit_and_record(app, platform, info):
    if git(app, "status", "--porcelain") or git(app, "rev-parse", "HEAD") != info["commit"]:
        raise ImportFailure("Código/commit mudou durante o build; recibo recusado")
    output = output_path(app, platform)
    no_links(output)
    if platform == "windows":
        for name in (
            "votoaberto.exe",
            "flutter_windows.dll",
            "data/icudtl.dat",
            "data/flutter_assets/AssetManifest.bin",
        ):
            if not (output / name).is_file():
                raise ImportFailure("Bundle Windows incompleto: " + name)
        if any(p.is_symlink() for p in output.rglob("*")):
            raise ImportFailure("Bundle Windows contém links")
        audit_dataset(output / "data/flutter_assets/assets/data", app, info)
        files = sorted(p for p in output.rglob("*") if p.is_file())
    else:
        # Audit the copy that the official workflow will actually accept/upload.
        accepted = android_distribution_path(app)
        no_links(accepted)
        accepted.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=accepted.parent) as temp:
            staged = Path(temp) / accepted.name
            shutil.copyfile(output, staged)
            audit_android_bundle(staged, app, info)
            staged.replace(accepted)
        output = accepted
        files = [accepted]
    artifacts = [artifact_hash(p, output if output.is_dir() else output.parent) for p in files]
    report = app / "build/native-release" / platform / "native-release.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({**info, "artifacts": artifacts}, indent=2) + "\n", "utf8")
    return report


def verify_android_distribution(app):
    """Reject missing, stale or forged receipts; re-audit the accepted AAB bytes."""
    accepted = android_distribution_path(app)
    no_links(accepted)
    report = accepted.parent / "native-release.json"
    receipt = json.loads(report.read_text("utf8"))
    meta = require_approved(app / "assets/data/real", app / "web-data-approval.json")
    expected = prepare_build(app, "appbundle", meta)
    if any(receipt.get(key) != value for key, value in expected.items()) or receipt.get(
        "artifacts"
    ) != [artifact_hash(accepted, accepted.parent)]:
        raise ImportFailure("AAB aceito/recibo ausente, alterado ou divergente do checkout")
    audit_android_bundle(accepted, app, expected)
    return accepted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check-version", "android-preflight", "verify-android"])
    parser.add_argument("--previous-ref")
    args = parser.parse_args()
    app = Path(__file__).resolve().parents[1]
    try:
        if args.command == "android-preflight":
            android_preflight(app, os.environ)
            print("Android Release: preflight de arquivos/configuração aprovado")
            return 0
        if args.command == "verify-android":
            verify_android_distribution(app)
            print("AAB auditado e recibo verificados para distribuição controlada")
            return 0
        if not args.previous_ref:
            parser.error("check-version exige --previous-ref")
        old = git(app, "show", args.previous_ref + ":apps/votoaberto_flutter/pubspec.yaml")
        validate_progression(version_from_pubspec(old), app_version(app))
        print("Versão e build number válidos: " + app_version(app))
        return 0
    except (
        ImportFailure,
        OSError,
        ValueError,
        KeyError,
        zipfile.BadZipFile,
        subprocess.SubprocessError,
    ) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

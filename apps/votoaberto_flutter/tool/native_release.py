"""Native production version/provenance gate and packaged-data audit. No publishing."""

import argparse
import hashlib
import json
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
        prefix = "base/assets/flutter_assets/assets/data/"
        with (
            zipfile.ZipFile(output) as archive,
            tempfile.TemporaryDirectory(dir=output.parent) as temp,
        ):
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
        files = [output]
    artifacts = [
        {
            "path": p.relative_to(output if output.is_dir() else output.parent).as_posix(),
            "bytes": p.stat().st_size,
            "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
        }
        for p in files
    ]
    report = app / "build/native-release" / platform / "native-release.json"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps({**info, "artifacts": artifacts}, indent=2) + "\n", "utf8")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["check-version"])
    parser.add_argument("--previous-ref", required=True)
    args = parser.parse_args()
    app = Path(__file__).resolve().parents[1]
    try:
        old = git(app, "show", args.previous_ref + ":apps/votoaberto_flutter/pubspec.yaml")
        validate_progression(version_from_pubspec(old), app_version(app))
        print("Versão e build number válidos: " + app_version(app))
        return 0
    except (ImportFailure, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Supported build/run entrypoint: reject missing/mixed real assets before Flutter."""

import argparse
import json
import os
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP.parents[1] / "pipelines"))
from tse_importer.domain import ImportFailure  # noqa: E402
from tse_importer.embedded_assets import build_metadata, install_assets  # noqa: E402


def resolve_flutter(requested):
    """Resolve PATH/PATHEXT before subprocess; explicit paths use the caller's cwd."""
    explicit = "/" in requested or "\\" in requested
    candidate = str(Path(requested).resolve()) if explicit else requested
    resolved = shutil.which(candidate)
    if resolved is None and os.name == "nt" and explicit and not Path(candidate).suffix:
        # Python 3.11 checks an explicit path without expanding PATHEXT.
        # Append only suffixes in the requested directory, never search PATH.
        for extension in (os.environ.get("PATHEXT") or ".COM;.EXE;.BAT;.CMD").split(";"):
            extension = extension.strip()
            if not extension.startswith(".") or not extension[1:].isalnum():
                continue
            executable = candidate + extension
            if os.path.isfile(executable) and os.access(executable, os.F_OK | os.X_OK):
                resolved = executable
                break
    if resolved is None:
        raise ImportFailure(
            f"Executável Flutter não encontrado: {requested}. "
            "Inclua o SDK no PATH ou informe --flutter com o caminho do executável "
            "(flutter.bat no Windows)."
        )
    return str(Path(resolved).resolve())


@contextmanager
def selected_assets(mode):
    """Package only the chosen dataset, restoring pubspec byte-for-byte afterwards."""
    pubspec = APP / "pubspec.yaml"
    lock = APP / ".embedded-build.lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    lock_identity = (lock.stat().st_dev, lock.stat().st_ino)
    original = pubspec.read_bytes()
    try:
        start, end = "    # BEGIN EMBEDDED ASSETS\n", "    # END EMBEDDED ASSETS\n"
        text = original.decode("utf8").replace("\r\n", "\n")
        if text.count(start) != 1 or text.count(end) != 1:
            raise ImportFailure("Configuração de assets do pubspec não reconhecida")
        first, rest = text.split(start)
        _, last = rest.split(end)
        folder = "real" if mode == "real" else "synthetic"
        entries = (
            ""
            if mode == "demo"
            else f"    - assets/data/{folder}/\n    - assets/data/{folder}/municipalities/\n"
        )
        selected = (first + start + entries + end + last).encode("utf8")
        pubspec.write_bytes(selected)
        try:
            yield
        finally:
            if pubspec.read_bytes() == selected:
                pubspec.write_bytes(original)
            else:
                raise ImportFailure(
                    "pubspec foi alterado durante o build; edição externa preservada"
                )
    finally:
        if lock.exists() and (lock.stat().st_dev, lock.stat().st_ino) == lock_identity:
            lock.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["run", "web", "windows", "apk", "native-test"])
    parser.add_argument("--mode", choices=["demo", "fixture", "real"], required=True)
    parser.add_argument(
        "--source", type=Path, help="Release JSON validada, obrigatória na primeira instalação real"
    )
    parser.add_argument("--flutter", default="flutter")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--device", default="windows", help="Dispositivo do smoke nativo opcional")
    args, extra = parser.parse_known_args(argv)
    try:
        if args.command == "native-test" and args.mode != "real":
            raise ImportFailure("O smoke nativo real exige --mode real")
        flags = ["--dart-define=VOTOABERTO_DATA=" + args.mode]
        if args.mode != "demo":
            assets = APP / "assets/data" / ("real" if args.mode == "real" else "synthetic")
            if args.source:
                install_assets(args.source, assets)
            meta = build_metadata(
                assets, "official-derived" if args.mode == "real" else "synthetic"
            )
            flags += [
                "--dart-define=VOTOABERTO_DATASET=" + meta["dataset_id"],
                "--dart-define=VOTOABERTO_MANIFEST_SHA256=" + meta["manifest_sha256"],
            ]
            print(json.dumps(meta), flush=True)
        flutter = resolve_flutter(args.flutter)
        command = (
            [flutter, "run"]
            if args.command == "run"
            else [
                flutter,
                "build",
                args.command,
                "--debug" if args.command == "apk" else "--release",
            ]
        )
        if args.command == "native-test":
            command = [
                flutter,
                "test",
                "integration_test/offline_results_test.dart",
                "-d",
                args.device,
                "--dart-define=RUN_REAL_EMBEDDED=true",
            ]
        if args.command == "web":
            # This SDK still defaults to its deprecated offline-first worker.
            # Opt out explicitly until a cache/update policy is tested separately.
            command += ["--no-web-resources-cdn", "--pwa-strategy=none"]
        command += flags + [value for value in extra if value != "--"]
        print(json.dumps({"command": command, "cwd": str(APP)}, ensure_ascii=False), flush=True)
        if args.dry_run:
            return 0
        environment = {
            **os.environ,
            "FLUTTER_SUPPRESS_ANALYTICS": "true",
            "DART_SUPPRESS_ANALYTICS": "true",
            "CI": "true",
        }
        with selected_assets(args.mode):
            try:
                code = subprocess.call(command, cwd=APP, env=environment, shell=False)
            except OSError as error:
                raise ImportFailure(
                    f"Não foi possível iniciar o Flutter resolvido em {flutter}: {error}"
                ) from error
        if code:
            print(f"Comando Flutter falhou (código {code}): {flutter}", file=sys.stderr)
        return code
    except (OSError, ValueError, KeyError, TypeError, ImportFailure) as error:
        print("Erro: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Read-only release gates, artifact audit and verified CI dataset handoff."""

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP.parents[1] / "pipelines"))
from tse_importer.domain import ImportFailure  # noqa: E402
from tse_importer.embedded_assets import build_metadata  # noqa: E402
from tse_importer.embedded_exporter import resolve_release  # noqa: E402

MAX_FILES = 20_000
MAX_FILE_BYTES = 25 * 1024 * 1024
# Operational budget, NOT a Cloudflare total-deployment limit.
MAX_BUNDLE_BYTES = 256 * 1024 * 1024


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require_approved(source, approval_path=None):
    """Never promote a local preview by rewriting its readiness or provenance."""
    source = resolve_release(source)
    meta = build_metadata(source, "official-derived")
    manifest = read_json(source / "manifest.json")
    readiness = manifest.get("public_readiness", {})
    assessment = manifest.get("source_assessment", {}).get("public_readiness", {})
    for evaluation in (readiness, assessment):
        if (
            evaluation.get("status") != "ready_for_declared_scope"
            or evaluation.get("blockers") != []
        ):
            raise ImportFailure(
                "Publicação bloqueada pela avaliação dos dados: "
                + json.dumps(evaluation, ensure_ascii=False)
            )
    approval = read_json(approval_path or APP / "web-data-approval.json")
    review = approval.get("redistribution_review", {})
    if "provenance_review" in manifest:
        provenance = manifest["provenance_review"]
        decision = approval.get("provenance_approval", {})
        if (
            approval.get("metadata_release_id") != manifest["metadata_release_id"]
            or decision.get("approved") is not True
            or decision.get("policy_id") != provenance["policy_id"]
            or decision.get("review_sha256") != provenance["review_sha256"]
            or not decision.get("reviewed_by")
            or not decision.get("reviewed_on")
        ):
            raise ImportFailure(
                "Publicação bloqueada: aprovação explícita de proveniência/política ausente ou divergente"
            )
    if (
        approval.get("dataset_id") != meta["dataset_id"]
        or approval.get("manifest_sha256") != meta["manifest_sha256"]
        or not approval.get("release_tag")
        or review.get("approved") is not True
        or not str(review.get("source_terms_url", "")).startswith("https://")
        or not review.get("reviewed_by")
        or not review.get("reviewed_on")
    ):
        raise ImportFailure(
            "Publicação bloqueada: aprovação de redistribuição/hash ausente ou divergente"
        )
    return meta


def write_build_info(app, mode):
    data = app / "assets/data" / ("real" if mode == "real" else "synthetic")
    meta = build_metadata(data, "official-derived" if mode == "real" else "synthetic")
    info = {"data_mode": mode, **meta}
    output = app / "build/web"
    # Only generated build markers; the source datasets and .gitkeep stay intact.
    folder = "real" if mode == "real" else "synthetic"
    for marker in [
        output / ".last_build_id",
        output / "assets/assets/data" / folder / ".gitkeep",
        output / "assets/assets/data" / folder / "municipalities/.gitkeep",
    ]:
        marker.unlink(missing_ok=True)
    (app / "build/web/web-build.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
    )


def audit(build=None, mode="real", production=False, approval_path=None):
    build = Path(build or APP / "build/web")
    if mode not in {"real", "fixture"}:
        raise ImportFailure("Auditoria Web exige dados reais ou fixture explícita")
    folder = "real" if mode == "real" else "synthetic"
    data = build / "assets/assets/data" / folder
    meta = build_metadata(data, "official-derived" if mode == "real" else "synthetic")
    manifest = read_json(data / "manifest.json")
    info = read_json(build / "web-build.json")
    if any(info.get(key) != value for key, value in {"data_mode": mode, **meta}.items()):
        raise ImportFailure("Identidade do build não corresponde aos dados empacotados")
    if production:
        if mode != "real":
            raise ImportFailure("Fixtures nunca podem ser publicadas")
        require_approved(data, approval_path)
    required = [
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
        "_headers",
        "canvaskit/canvaskit.js",
        "canvaskit/canvaskit.wasm",
        "assets/AssetManifest.bin",
        "assets/FontManifest.json",
        "assets/NOTICES",
    ]
    for name in required:
        if not (build / name).is_file() or (build / name).stat().st_size == 0:
            raise ImportFailure("Asset obrigatório ausente/vazio: " + name)
    for source in [*(APP / "assets/geo").glob("*"), *(APP / "assets/fonts").glob("*")]:
        if source.is_file() and source.suffix in {".json", ".geojson", ".ttf", ".txt"}:
            target = build / "assets/assets" / source.relative_to(APP / "assets")
            if not target.is_file() or sha256(source) != sha256(target):
                raise ImportFailure("Asset geográfico/fonte ausente ou alterado: " + source.name)
    if (build / "_headers").read_bytes() != (APP / "web/_headers").read_bytes():
        raise ImportFailure("Política de cabeçalhos ausente ou divergente")
    html = (build / "index.html").read_text(encoding="utf8")
    bootstrap = (build / "flutter_bootstrap.js").read_text(encoding="utf8")
    if '<base href="/">' not in html or re.search(
        r"_flutter\.loader\.load\(\s*\{[^}]*serviceWorkerSettings", bootstrap
    ):
        raise ImportFailure("Base href ou bootstrap/service worker incompatível")
    if '"useLocalCanvasKit":true' not in bootstrap.replace(" ", ""):
        raise ImportFailure("CanvasKit deve ser servido localmente")
    if "MVP" in html or "MVP" in (build / "manifest.json").read_text(encoding="utf8"):
        raise ImportFailure("Metadados públicos contêm nomenclatura de prévia")
    files = [p for p in build.rglob("*") if p.is_file()]
    if any(p.is_symlink() for p in build.rglob("*")):
        raise ImportFailure("Links simbólicos não pertencem ao artefato")
    if len(files) > MAX_FILES or any(p.stat().st_size > MAX_FILE_BYTES for p in files):
        raise ImportFailure(
            "Artefato excede limites Workers Free (20.000 arquivos / 25 MiB por arquivo)"
        )
    data_files = {"manifest.json", *manifest["artifacts"]}
    packaged_data = [p for p in (build / "assets/assets/data").rglob("*") if p.is_file()]
    if (
        any(not p.is_relative_to(data) for p in packaged_data)
        or {p.relative_to(data).as_posix() for p in packaged_data} != data_files
    ):
        raise ImportFailure("Assets de dados misturados, duplicados ou não declarados")
    for p in files:
        if p.suffix.lower() in {
            ".zip",
            ".sqlite",
            ".sqlite3",
            ".db",
            ".map",
            ".pem",
            ".key",
        } or p.name.startswith(".env"):
            raise ImportFailure(
                "Arquivo não destinado ao público: " + p.relative_to(build).as_posix()
            )
    sizes = sorted(files, key=lambda p: p.stat().st_size, reverse=True)
    duplicates = {}
    for p in files:
        duplicates.setdefault(sha256(p), []).append(p.relative_to(build).as_posix())
    return {
        "data_mode": mode,
        **meta,
        "elections": [
            {k: e[k] for k in ("year", "round", "office")} for e in manifest["elections"]
        ],
        "municipalities": sum(manifest["municipality_counts"].values()),
        "file_count": len(files),
        "total_bytes": sum(p.stat().st_size for p in files),
        "largest_files": [
            {"path": p.relative_to(build).as_posix(), "bytes": p.stat().st_size} for p in sizes[:10]
        ],
        "data_files": [
            {"path": name, "bytes": (data / name).stat().st_size} for name in sorted(data_files)
        ],
        "duplicate_groups": [paths for paths in duplicates.values() if len(paths) > 1],
        "cloudflare_free_limits": {
            "files": MAX_FILES,
            "individual_bytes": MAX_FILE_BYTES,
            "passed": True,
        },
        "production_approved": production,
    }


def bundle(source, output, approval_path=None):
    """ZIP_STORED only transports approved bytes outside Git; no recompression."""
    source = resolve_release(source)
    require_approved(source, approval_path)
    manifest = read_json(source / "manifest.json")
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_STORED) as archive:
        for name in ["manifest.json", *sorted(manifest["artifacts"])]:
            archive.write(source / name, name)


def unpack(archive_path, destination, approval_path=None):
    """Reject extra paths, duplicate names, bombs and symlinks before extraction."""
    destination = Path(destination)
    if destination.exists():
        raise ImportFailure("Destino já existe; dados preservados")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        names = [item.filename for item in members]
        if len(names) != len(set(names)) or len(names) > 33:
            raise ImportFailure("Bundle duplicado ou com arquivos inesperados")
        manifest_info = archive.getinfo("manifest.json")
        if manifest_info.file_size > MAX_FILE_BYTES:
            raise ImportFailure("Manifesto excessivo")
        manifest = json.loads(archive.read(manifest_info))
        if set(names) != {"manifest.json", *manifest["artifacts"]}:
            raise ImportFailure("Bundle não corresponde ao manifesto")
        if sum(item.file_size for item in members) > MAX_BUNDLE_BYTES:
            raise ImportFailure("Bundle excede orçamento operacional de 256 MiB")
        for item in members:
            path = Path(item.filename)
            if (
                path.is_absolute()
                or ".." in path.parts
                or "\\" in item.filename
                or ":" in item.filename
                or item.file_size > MAX_FILE_BYTES
                or (item.external_attr >> 16) & 0o170000 == 0o120000
            ):
                raise ImportFailure("Caminho/tamanho inválido no bundle")
        with tempfile.TemporaryDirectory(prefix="web-data-", dir=destination.parent) as temp:
            stage = Path(temp) / "dataset"
            for item in members:
                target = stage / item.filename
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(item) as src, target.open("xb") as dst:
                    shutil.copyfileobj(src, dst)
            require_approved(stage, approval_path)
            stage.rename(destination)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("audit")
    check.add_argument("--build", type=Path)
    check.add_argument("--mode", choices=["real", "fixture"], required=True)
    check.add_argument("--production", action="store_true")
    check.add_argument("--report", type=Path)
    gate = sub.add_parser("preflight")
    gate.add_argument("--source", type=Path, required=True)
    pack = sub.add_parser("bundle")
    pack.add_argument("--source", type=Path, required=True)
    pack.add_argument("--output", type=Path, required=True)
    extract = sub.add_parser("unpack")
    extract.add_argument("--archive", type=Path, required=True)
    extract.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = {"passed": True}
        if args.command == "audit":
            result = audit(args.build, args.mode, args.production)
            if args.report:
                args.report.parent.mkdir(parents=True, exist_ok=True)
                args.report.write_text(
                    json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8"
                )
        elif args.command == "preflight":
            result = require_approved(args.source)
        elif args.command == "bundle":
            bundle(args.source, args.output)
        elif args.command == "unpack":
            unpack(args.archive, args.destination)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ImportFailure, OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        print("Release bloqueada: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Reusable pipeline: per-member checkpoints, validation, immutable releases."""

import hashlib
import json
import os
import time
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.resources import files
from pathlib import Path

from . import ASSESSMENT_VERSION, SCHEMA_VERSION, __version__
from .assessment import assess_release, source_hash_assessment
from .discovery import inventory
from .domain import Config, CoverageRequirements, ImportFailure, Selection
from .integrity import hashes
from .storage import (
    connect,
)
from .validation import validate_database
from .workspace import ACTIVE_WORK, WorkRun, no_links


def write_json(path: Path, value) -> None:
    if work := ACTIVE_WORK.get():
        if not path.exists():
            work.file(path)
        work.allowed(path)
        no_links(path)
        info = path.stat()
        if work.owned.get(str(path)) != (info.st_dev, info.st_ino):
            raise ImportFailure(
                "Artefato substituído ou de propriedade desconhecida; escrita recusada"
            )
        work.check(len(json.dumps(value, ensure_ascii=False).encode("utf8")) * 2 + 1024)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf8"
    )


def identity(value) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()


def rules_digest() -> str:
    """Invalidate checkpoints even for an unversioned local change to ingestion rules."""
    digest = hashlib.sha256()
    for resource in sorted(files("tse_importer").iterdir(), key=lambda item: item.name):
        if resource.name.endswith((".py", ".json")):
            digest.update(resource.name.encode())
            digest.update(resource.read_bytes())
    return digest.hexdigest()


def peak_memory() -> dict:
    try:
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes

            class Counters(ctypes.Structure):
                _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                    (name, ctypes.c_size_t)
                    for name in (
                        "PeakWorkingSetSize",
                        "WorkingSetSize",
                        "QuotaPeakPagedPoolUsage",
                        "QuotaPagedPoolUsage",
                        "QuotaPeakNonPagedPoolUsage",
                        "QuotaNonPagedPoolUsage",
                        "PagefileUsage",
                        "PeakPagefileUsage",
                    )
                ]

            counters = Counters()
            counters.cb = ctypes.sizeof(counters)
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.GetCurrentProcess.restype = wintypes.HANDLE
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            psapi.GetProcessMemoryInfo.argtypes = [
                wintypes.HANDLE,
                ctypes.POINTER(Counters),
                wintypes.DWORD,
            ]
            if not psapi.GetProcessMemoryInfo(
                kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb
            ):
                raise OSError("GetProcessMemoryInfo failed")
            return {
                "peak_bytes": counters.PeakWorkingSetSize,
                "method": "Windows PeakWorkingSetSize",
            }
        import resource
        import sys

        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return {
            "peak_bytes": value if sys.platform == "darwin" else value * 1024,
            "method": "getrusage peak RSS",
        }
    except (ImportError, OSError):
        return {"peak_bytes": None, "method": "unavailable"}


def validate_release(directory: Path) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf8"))
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ImportFailure("Release incompatível com este schema")
    if manifest.get("assessment_version", 1) not in (1, ASSESSMENT_VERSION):
        raise ImportFailure("Versão de avaliação não suportada")
    for name, digest in manifest["artifacts"].items():
        if name not in (
            "election.sqlite",
            "validation.json",
            "divergences.jsonl",
            "divergences-summary.json",
        ):
            raise ImportFailure("Artefato desconhecido no manifesto")
        if hashes(directory / name)["sha256"] != digest["sha256"]:
            raise ImportFailure(f"Hash de artefato divergente: {name}")
    required = {"election.sqlite", "validation.json", "divergences.jsonl"}
    if manifest.get("report_version") == 2:
        required.add("divergences-summary.json")
    if set(manifest["artifacts"]) != required:
        raise ImportFailure("Manifesto incompleto")
    report = json.loads((directory / "validation.json").read_text(encoding="utf8"))
    result = validate_database(directory / "election.sqlite")
    options = dict(manifest["selection"])
    for key in ("offices", "rounds", "territories"):
        options[key] = tuple(options[key])
    requirements = {
        key: tuple(value) for key, value in manifest.get("coverage_requirements", {}).items()
    }
    result["assessment"] = assess_release(
        result,
        Selection(**options),
        CoverageRequirements(**requirements),
        manifest["sources"],
        report.get("reconciliation"),
        manifest["data_kind"],
        require_verified=manifest.get("require_verified", False),
        evidence="retained_report_and_database",
    )
    result["assessment_scope"] = "release_with_retained_source_evidence"
    result["assessment_version"] = ASSESSMENT_VERSION
    result.pop("public_readiness")
    return result


def run_import(config: Config, progress=lambda message: None) -> Path:
    start = time.perf_counter()
    no_links(config.output_dir.absolute())
    root, output = config.input_dir.resolve(), config.output_dir.resolve()
    if output == root or root.is_relative_to(output) or output.is_relative_to(root):
        raise ImportFailure("Entrada e saída devem ser diretórios separados, sem sobreposição")
    output.mkdir(parents=True, exist_ok=True)
    lock = output / ".import.lock"
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise ImportFailure(
            "Importação já ativa ou lock residual; confirme ausência do processo antes de remover .import.lock"
        ) from exc
    try:
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        with WorkRun(output, config.storage) as work:
            try:
                return _run(config, root, output, start, progress, work)
            except Exception:
                if work.failure:
                    raise work.failure from None
                raise
    finally:
        lock.unlink(missing_ok=True)


def promote_directory(stage: Path, release: Path) -> None:
    """Retry transient Windows sharing/access errors without changing atomic promotion."""
    delays = (0.05, 0.1, 0.2, 0.4, 0.8)
    for attempt in range(len(delays) + 1):
        if release.exists():
            raise ImportFailure("Destino de release já existe; promoção recusada")
        try:
            os.replace(stage, release)
            return
        except PermissionError as exc:
            if getattr(exc, "winerror", None) not in (5, 32, 33) or attempt == len(delays):
                raise
            time.sleep(delays[attempt])


def _run(config, root, output, start, progress, work):
    progress("Inventariando e calculando SHA-256/SHA-512")
    catalog = inventory(
        root, config.limits, config.references, config.inventory_cache, config.source_paths
    )
    write_json(work.root / "inventory.json", catalog)
    archives = [item for item in catalog["files"] if item["name"].lower().endswith(".zip")]
    if set(config.source_metadata) - {item["path"] for item in archives}:
        raise ImportFailure("source_metadata contém fonte não encontrada")
    for item in archives:
        item["metadata"] = config.source_metadata.get(item["path"], {})
    if not archives:
        raise ImportFailure("Nenhum ZIP encontrado")
    for item in archives:
        status = item.get("verification", {}).get("status")
        if item["status"] != "ok" or status in ("mismatch", "error", "unsupported"):
            raise ImportFailure(
                f"Fonte recusada {item['path']}: {item.get('error', status or item['status'])}"
            )
        if config.require_verified and status != "verified":
            raise ImportFailure(f"Referência confiável exigida: {item['path']}")
    semantics = {
        "selection": asdict(config.selection),
        "limits": asdict(config.limits),
        "data_kind": config.data_kind,
        "schema_version": SCHEMA_VERSION,
        "importer_version": __version__,
        "require_verified": config.require_verified,
        "coverage_requirements": asdict(config.coverage_requirements),
        "assessment_version": ASSESSMENT_VERSION,
        "rules_sha256": rules_digest(),
    }
    if (
        config.data_kind == "official"
        and config.coverage_requirements.territories == ("NATIONAL",)
        and not config.storage.projected_peak_bytes
    ):
        raise ImportFailure(
            "Carga NATIONAL oficial exige projected_peak_bytes fundamentado em piloto; execute plan"
        )
    release_id = identity({"config": semantics, "sources": catalog})[:24]
    work.checkpoint_key = identity(semantics)
    work.save("running")
    releases = output / "releases"
    no_links(releases)
    releases.mkdir(exist_ok=True)
    release = releases / release_id
    no_links(release)
    if release.exists():
        result = validate_release(release)
        if result["assessment"]["local_release"]["status"] != "eligible":
            raise ImportFailure("Release anterior inválida; não reutilizada")
        _publish_pointer(output, release_id)
        progress(f"Release idempotente reutilizada: {release_id}")
        return release
    stage = work.root / "staging"
    stage.mkdir()
    from .partitioned import build

    reconciliation, source_stats, reused, timings = build(
        config, root, archives, semantics, work, stage, progress, identity, write_json
    )
    db_path = stage / "election.sqlite"
    connection = connect(db_path, config.limits)
    try:
        connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        connection.executemany(
            "INSERT INTO metadata VALUES (?,?)",
            [
                ("schema_version", str(SCHEMA_VERSION)),
                ("importer_version", __version__),
                ("configuration", json.dumps(semantics, sort_keys=True)),
                ("source_hash_status", source_hash_assessment(catalog)["status"]),
                (
                    "data_nature",
                    "official-derived" if config.data_kind == "official" else "synthetic",
                ),
            ],
        )
        connection.commit()
    finally:
        connection.close()
    validation_start = time.perf_counter()
    validation = validate_database(db_path)
    validation["assessment"] = assess_release(
        validation,
        config.selection,
        config.coverage_requirements,
        catalog,
        reconciliation,
        config.data_kind,
        require_verified=config.require_verified,
    )
    validation["assessment_scope"] = "import_streams_and_database"
    validation["assessment_version"] = ASSESSMENT_VERSION
    validation.pop("public_readiness")
    validation["reconciliation"] = reconciliation
    validation["sources"] = source_stats
    validation["performance"] = {
        "elapsed_seconds": round(time.perf_counter() - start, 3),
        "memory": peak_memory(),
        "sqlite_bytes": db_path.stat().st_size,
        "checkpoints_reused": reused,
        "source_csv_uncompressed_bytes_read": sum(
            item.get("uncompressed_bytes_read", 0)
            for item in source_stats
            if not item.get("checkpoint_reused")
        ),
        "source_read_measurement": "CSV bytes decompressed to EOF (excludes header probes, PDF and ZIP index reads); compressed OS read bytes not measured",
        **timings,
        "validation_seconds": round(time.perf_counter() - validation_start, 3),
        "storage_before_cleanup": work.metrics(),
    }
    write_json(stage / "validation.json", validation)
    if validation["assessment"]["local_release"]["status"] != "eligible":
        raise ImportFailure(f"Validação recusou publicação; diagnóstico preservado em {stage}")
    limitations = [
        "Hash não é assinatura digital nem certificação eleitoral",
        "Cobertura restrita às fontes e filtros; ALL significa abrangências disponíveis",
        "Categorias sem linha permanecem ausentes, não são convertidas em zero",
        "Seção, BU e equipamento não têm correspondência universal 1:1",
        "Correspondência entre fontes refere-se ao recorte tabular comparado",
        "BUs ambíguos não fornecem totais nem conferência; detalhes em divergences.jsonl",
        "Licença dos dados deve ser conferida no recurso; MIT refere-se ao código",
    ]
    manifest = {
        "dataset": "VotoAberto presidencial",
        "report_version": 2,
        "storage_policy": asdict(config.storage),
        "run_id": work.run_id,
        "data_nature": "official-derived" if config.data_kind == "official" else "synthetic",
        "release_id": release_id,
        **semantics,
        "processed_at": datetime.now(UTC).isoformat(),
        "sources": catalog,
        "source_stats": source_stats,
        "attribution": "Tribunal Superior Eleitoral (fontes declaradas como oficiais); fixtures sintéticos são demonstração",
        "observed_coverage": validation["observed_coverage"],
        "assessment": validation["assessment"],
        "limitations": limitations,
        "artifacts": {
            name: {"sha256": hashes(stage / name)["sha256"], "bytes": (stage / name).stat().st_size}
            for name in (
                "election.sqlite",
                "validation.json",
                "divergences.jsonl",
                "divergences-summary.json",
            )
        },
    }
    write_json(stage / "manifest.json", manifest)
    work.check()
    if validate_release(stage)["assessment"]["local_release"]["status"] != "eligible":
        raise ImportFailure("Validação final recusou promoção")
    with work.mutex:
        promote_directory(stage, release)
        work.promoted_to(stage, release)
    work.check()
    try:
        _publish_pointer(output, release_id)
    except BaseException:
        # Return this run's unreferenced directory to diagnostics; never touch an older release.
        try:
            with work.mutex:
                promote_directory(release, stage)
                work.demoted_to(release, stage)
        except (OSError, ImportFailure) as exc:
            work.refused.append({"path": str(release), "reason": f"Rollback de promoção: {exc}"})
        raise
    work.published = True
    progress(f"Release concluída: {release}")
    return release


def _publish_pointer(output: Path, release_id: str):
    work = ACTIVE_WORK.get()
    pending = (
        work.root / "current.tmp" if work else output / ("current-" + uuid.uuid4().hex + ".tmp")
    )
    write_json(pending, {"release_id": release_id, "path": f"releases/{release_id}"})
    os.replace(pending, output / "current.json")

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

from . import SCHEMA_VERSION, __version__
from .discovery import drain, inventory, member_stream
from .domain import Config, ImportFailure
from .integrity import fingerprint, hashes
from .parsers import inspect_member, parse
from .storage import (
    RECORD_COLUMNS,
    compact,
    connect,
    create_stage,
    create_unit,
    insert_records,
    project,
)
from .validation import reconcile, validate_database


def write_json(path: Path, value) -> None:
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
    if manifest["schema_version"] != SCHEMA_VERSION or manifest["importer_version"] != __version__:
        raise ImportFailure("Release incompatível com este importador/schema")
    for name, digest in manifest["artifacts"].items():
        if name not in ("election.sqlite", "validation.json", "divergences.jsonl"):
            raise ImportFailure("Artefato desconhecido no manifesto")
        if hashes(directory / name)["sha256"] != digest["sha256"]:
            raise ImportFailure(f"Hash de artefato divergente: {name}")
    required = {"election.sqlite", "validation.json", "divergences.jsonl"}
    if set(manifest["artifacts"]) != required:
        raise ImportFailure("Manifesto incompleto")
    return validate_database(directory / "election.sqlite")


def run_import(config: Config, progress=lambda message: None) -> Path:
    start = time.perf_counter()
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
        return _run(config, root, output, start, progress)
    finally:
        lock.unlink(missing_ok=True)


def _run(config, root, output, start, progress):
    progress("Inventariando e calculando SHA-256/SHA-512")
    catalog = inventory(root, config.limits, config.references)
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
        "rules_sha256": rules_digest(),
    }
    release_id = identity({"config": semantics, "sources": catalog})[:24]
    releases = output / "releases"
    releases.mkdir(exist_ok=True)
    release = releases / release_id
    if release.exists():
        result = validate_release(release)
        if not result["valid"]:
            raise ImportFailure("Release anterior inválida; não reutilizada")
        _publish_pointer(output, release_id)
        progress(f"Release idempotente reutilizada: {release_id}")
        return release
    stage = output / ".staging" / (release_id + "-" + uuid.uuid4().hex[:8])
    stage.mkdir(parents=True)
    cache = output / ".checkpoints"
    cache.mkdir(exist_ok=True)
    write_json(stage / "inventory.json", catalog)
    checkpoints = []
    reused = 0
    source_stats = []
    for item in archives:
        path = root / item["path"]
        source_before = fingerprint(path)
        for member in item["members"]:
            if member["directory"]:
                continue
            description = inspect_member(path, member["name"], config.limits, sample_rows=0)
            if description["status"] != "supported":
                if member["extension"] != ".pdf":
                    raise ImportFailure(
                        f"Formato não suportado: {item['path']}:{member['name']}; {description['reason']}"
                    )
                with member_stream(path, member["name"], config.limits) as stream:
                    drain(stream, config.limits)
                source_stats.append(
                    {
                        "archive": item["path"],
                        "member": member["name"],
                        "status": "auxiliary_unsupported",
                        "crc_checked": True,
                    }
                )
                continue
            source_id = identity([item["hashes"]["sha256"], member["name"]])
            unit_id = identity([source_id, semantics])
            unit_path = cache / (unit_id + ".sqlite")
            unit_meta = cache / (unit_id + ".json")
            valid_cache = False
            if config.resume and unit_path.is_file() and unit_meta.is_file():
                try:
                    meta = json.loads(unit_meta.read_text(encoding="utf8"))
                    valid_cache = (
                        meta["unit_id"] == unit_id and hashes(unit_path)["sha256"] == meta["sha256"]
                    )
                except (OSError, ValueError, KeyError):
                    valid_cache = False
            if valid_cache:
                stats = meta["stats"]
                reused += 1
                progress(f"Checkpoint conferido: {item['name']}:{member['name']}")
            else:
                stats = {}
                pending = cache / (unit_id + "-" + uuid.uuid4().hex + ".partial")
                progress(f"Processando em fluxo: {item['name']}:{member['name']}")
                db = connect(pending, config.limits)
                try:
                    create_unit(db)
                    insert_records(
                        db, parse(path, member["name"], config.selection, config.limits, stats)
                    )
                    db.execute(
                        "INSERT INTO checkpoint VALUES (?)",
                        (json.dumps({"unit_id": unit_id, "stats": stats}),),
                    )
                    db.commit()
                finally:
                    db.close()
                if fingerprint(path) != source_before or hashes(path) != item["hashes"]:
                    raise ImportFailure("Fonte mudou durante parsing; checkpoint não publicado")
                os.replace(pending, unit_path)
                write_json(
                    unit_meta,
                    {"unit_id": unit_id, "sha256": hashes(unit_path)["sha256"], "stats": stats},
                )
            source_stats.append({"archive": item["path"], "member": member["name"], **stats})
            checkpoints.append((unit_path, source_id, item, member, stats["format"]))
        if fingerprint(path) != source_before or hashes(path) != item["hashes"]:
            raise ImportFailure("Fonte alterada antes da consolidação")
    db_path = stage / "election.sqlite"
    connection = connect(db_path, config.limits)
    try:
        create_stage(connection)
        for unit_path, source_id, item, member, fmt in checkpoints:
            connection.execute("ATTACH DATABASE ? AS unit", (str(unit_path),))
            connection.execute(
                f"INSERT INTO raw SELECT ?,?,{RECORD_COLUMNS} FROM unit.records", (source_id, fmt)
            )
            connection.execute(
                "INSERT INTO sources VALUES (?,?,?,?,?,?)",
                (
                    source_id,
                    item["path"],
                    member["name"],
                    item["hashes"]["sha256"],
                    fmt,
                    json.dumps(item["verification"], sort_keys=True),
                ),
            )
            connection.commit()
            connection.execute("DETACH DATABASE unit")
        project(connection, config.selection.profile)
        reconciliation = reconcile(connection, stage / "divergences.jsonl")
        connection.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        connection.executemany(
            "INSERT INTO metadata VALUES (?,?)",
            [
                ("schema_version", str(SCHEMA_VERSION)),
                ("importer_version", __version__),
                ("configuration", json.dumps(semantics, sort_keys=True)),
                (
                    "source_integrity",
                    "verified"
                    if all(i["verification"]["status"] == "verified" for i in archives)
                    else "unverified",
                ),
            ],
        )
        compact(connection)
    finally:
        connection.close()
    validation = validate_database(db_path)
    actual_rounds = {r["round"] for r in validation["coverage"]}
    actual_territories = {r["uf"] for r in validation["coverage"]}
    if actual_rounds != set(config.selection.rounds):
        validation["valid"] = False
        validation["missing_rounds"] = sorted(set(config.selection.rounds) - actual_rounds)
    if (
        config.selection.territories != ("ALL",)
        and not set(config.selection.territories) <= actual_territories
    ):
        validation["valid"] = False
        validation["missing_territories"] = sorted(
            set(config.selection.territories) - actual_territories
        )
    if config.selection.territories != ("ALL",):
        present = {(r["round"], r["uf"]) for r in validation["coverage"]}
        missing = sorted(
            (turn, uf)
            for turn in config.selection.rounds
            for uf in config.selection.territories
            if (turn, uf) not in present
        )
        if missing:
            validation["valid"] = False
            validation["missing_round_territory_pairs"] = missing
    if reconciliation["different_rows"] or reconciliation["bu_math_errors"]:
        validation["valid"] = False
    validation["reconciliation"] = reconciliation
    validation["sources"] = source_stats
    validation["performance"] = {
        "elapsed_seconds": round(time.perf_counter() - start, 3),
        "memory": peak_memory(),
        "sqlite_bytes": db_path.stat().st_size,
        "checkpoints_reused": reused,
    }
    write_json(stage / "validation.json", validation)
    if not validation["valid"]:
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
        "release_id": release_id,
        **semantics,
        "processed_at": datetime.now(UTC).isoformat(),
        "sources": catalog,
        "source_stats": source_stats,
        "attribution": "Tribunal Superior Eleitoral (fontes declaradas como oficiais); fixtures sintéticos são demonstração",
        "coverage": validation["coverage"],
        "validation": {"valid": True, "reconciliation": reconciliation},
        "source_integrity": "verified"
        if all(i["verification"]["status"] == "verified" for i in archives)
        else "unverified",
        "limitations": limitations,
        "artifacts": {
            name: {"sha256": hashes(stage / name)["sha256"], "bytes": (stage / name).stat().st_size}
            for name in ("election.sqlite", "validation.json", "divergences.jsonl")
        },
    }
    write_json(stage / "manifest.json", manifest)
    os.replace(stage, release)
    _publish_pointer(output, release_id)
    progress(f"Release concluída: {release}")
    return release


def _publish_pointer(output: Path, release_id: str):
    pending = output / ("current-" + uuid.uuid4().hex + ".tmp")
    write_json(pending, {"release_id": release_id, "path": f"releases/{release_id}"})
    os.replace(pending, output / "current.json")

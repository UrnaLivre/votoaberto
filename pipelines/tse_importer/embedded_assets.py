"""Install one verified JSON version into Flutter's fixed asset paths, without mixing."""

import json
from pathlib import Path

from .domain import TERRITORIES, ImportFailure, StoragePolicy
from .embedded_exporter import resolve_release, validate_embedded
from .workspace import WorkRun, no_links


def install_assets(source, destination):
    no_links(Path(destination).absolute())
    source, destination = resolve_release(source), Path(destination).resolve()
    no_links(destination)
    validate_embedded(source)
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf8"))
    names = ["manifest.json", *manifest["artifacts"]]
    if destination.exists():
        existing = {
            p.relative_to(destination).as_posix()
            for p in destination.rglob("*")
            if p.is_file() and p.name != ".gitkeep"
        }
        if existing:
            validate_embedded(destination)
            if existing != set(names) or any(
                (destination / n).read_bytes() != (source / n).read_bytes() for n in names
            ):
                raise ImportFailure(
                    "Assets existentes de outra versão; preservados. Selecione uma nova área de build."
                )
            return destination
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    # Empty tracked .gitkeep directories may stay in place; install into them only
    # after staging verification, with per-file rollback on a failed initial copy.
    with WorkRun(parent, StoragePolicy()) as work:
        stage = work.root / "staging"
        for name in names:
            payload = (source / name).read_bytes()
            work.check(len(payload) * 2)
            work.file(stage / name).write_bytes(payload)
        validate_embedded(stage)
        created = []
        try:
            if not destination.exists():
                with work.mutex:
                    stage.rename(destination)
                    work.promoted_to(stage, destination)
                work.published = True
            else:
                # .gitkeep is not owned and is never moved/deleted. The build runs
                # only after the final marker; failures remove only new exact files.
                work.promoted = destination
                for name in [n for n in names if n != "manifest.json"] + ["manifest.json"]:
                    target = destination / name
                    no_links(target)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    work.check((stage / name).stat().st_size * 2)
                    with target.open("xb") as file:
                        identity = target.stat()
                        created.append((target, identity.st_dev, identity.st_ino))
                        work.owned[str(target)] = (identity.st_dev, identity.st_ino)
                        file.write((stage / name).read_bytes())
                validate_embedded(destination)
                work.published = True
        except BaseException:
            for target, device, inode in created:
                no_links(target)
                info = target.stat()
                if (info.st_dev, info.st_ino) == (device, inode):
                    work.remove(target)
            raise
    return destination


def build_metadata(asset_root, nature):
    asset_root = Path(asset_root)
    if not (asset_root / "manifest.json").is_file():
        raise ImportFailure(
            "Build interrompido: manifesto dos assets obrigatórios ausente; não há fallback fictício"
        )
    validate_embedded(asset_root)
    manifest = json.loads((asset_root / "manifest.json").read_text(encoding="utf8"))
    if manifest["data_nature"] != nature or manifest["local_preview"] is not True:
        raise ImportFailure(
            "Build interrompido: natureza/versão incompatível com o modo solicitado"
        )
    if manifest.get("source_schema_version") != 1 or any(
        e["year"] != 2026 or e["office"] != "president" for e in manifest["elections"]
    ):
        raise ImportFailure("Build interrompido: eleição/schema de origem incompatível com o MVP")
    if nature == "official-derived":
        states = json.loads((asset_root / "states.json").read_text(encoding="utf8"))["territories"]
        if (
            set(manifest["territories"]) != TERRITORIES
            or {e["round"] for e in manifest["elections"]} != {1, 2}
            or any({r["round"] for r in state["rounds"]} != {1, 2} for state in states)
        ):
            raise ImportFailure(
                "Build interrompido: a prévia nacional exige 27 UFs + ZZ nos dois turnos"
            )
    import hashlib

    return {
        "dataset_id": manifest["dataset_id"],
        "manifest_sha256": hashlib.sha256((asset_root / "manifest.json").read_bytes()).hexdigest(),
        "public_readiness": manifest["public_readiness"],
        "bytes": sum(
            (asset_root / n).stat().st_size for n in ["manifest.json", *manifest["artifacts"]]
        ),
        "schema_version": manifest["schema_version"],
    }

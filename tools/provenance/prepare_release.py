"""Prepare an immutable metadata release using current hashes and retained electoral artifacts."""

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipelines"))
from tse_importer.domain import ImportFailure  # noqa: E402
from tse_importer.embedded_exporter import (  # noqa: E402
    read_only,
    resolve_release,
    validate_embedded,
)
from tse_importer.engine import validate_release  # noqa: E402
from tse_importer.integrity import hashes  # noqa: E402
from tse_importer.provenance import (  # noqa: E402
    POLICY_ID,
    PROOF_FILE,
    canonical,
    make_manifest,
    sha256,
)
from tse_importer.workspace import no_links  # noqa: E402


def document(path):
    raw = Path(path).read_bytes()
    return {"sha256": sha256(raw), "content": raw.decode("utf8")}


def prepare(national, embedded, references, current_hashes, testimony, output):
    national, embedded = resolve_release(national), resolve_release(embedded)
    documents = {
        "national_manifest": document(national / "manifest.json"),
        "national_validation_report": document(national / "validation.json"),
        "embedded_manifest": document(embedded / "manifest.json"),
        "source_references": document(references),
        "current_hashes": document(current_hashes),
        "acquisition_testimony": document(testimony),
    }
    original = json.loads(documents["embedded_manifest"]["content"])
    snapshot = validate_release(national)
    # Recheck the database identity; do not replay original ZIP streams or import records.
    database = national / "election.sqlite"
    require_hash = original["source_sqlite_sha256"]
    if hashes(database)["sha256"] != require_hash:
        raise ImportFailure("SQLite de origem divergente")
    selected = {
        key: snapshot[key]
        for key in (
            "assessment_scope",
            "structurally_valid",
            "checks",
            "comparison",
            "result_rows",
            "observed_coverage",
        )
    }
    selected["sqlite_sha256"] = require_hash
    review = {
        "schema_version": 1,
        "policy_id": POLICY_ID,
        "documents": documents,
        "current_validation": selected,
    }
    proof = canonical(review)
    manifest = make_manifest(review, proof)
    output = Path(output).resolve()
    no_links(output)
    if any(
        output == origin or output.is_relative_to(origin) or origin.is_relative_to(output)
        for origin in (national, embedded)
    ):
        raise ImportFailure("Saída deve ser separada das releases históricas")
    destination = output / "releases" / manifest["metadata_release_id"]
    no_links(destination)
    if destination.exists():
        raise ImportFailure("Release de metadados já existe; não será sobrescrita")
    (output / "releases").mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="metadata-", dir=output) as temp:
        stage = Path(temp) / "dataset"
        stage.mkdir()
        for name in original["artifacts"]:
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(embedded / name, target)
        (stage / PROOF_FILE).write_bytes(proof)
        (stage / "manifest.json").write_bytes(canonical(manifest))
        with read_only(database) as db:
            check = validate_embedded(stage, db)
        if check["status"] != "passed" or hashes(database)["sha256"] != require_hash:
            raise ImportFailure("Validação independente ou preservação do SQLite falhou")
        # Rename publishes only a new directory. Historical national/embedded releases stay intact.
        stage.rename(destination)
    pointer = canonical({"release_id": destination.name, "path": "releases/" + destination.name})
    if (output / "current.json").exists():
        raise ImportFailure("Ponteiro de saída já existe; release criada sem substituí-lo")
    (output / "current.json").write_bytes(pointer)
    return destination


def install_metadata(source, destination):
    """Explicit metadata-only installation; reject any different electoral payload."""
    source, destination = resolve_release(source), Path(destination).resolve()
    no_links(destination)
    validate_embedded(source)
    validate_embedded(destination)
    manifest = json.loads((source / "manifest.json").read_bytes())
    old = (destination / "manifest.json").read_bytes()
    replacement = (source / "manifest.json").read_bytes()
    origin_sha = manifest["provenance_review"]["origin_embedded_manifest_sha256"]
    if sha256(old) != origin_sha or (destination / PROOF_FILE).exists():
        raise ImportFailure("Instalação existente não corresponde à origem da revisão")
    for name in manifest["artifacts"]:
        if name != PROOF_FILE and (source / name).read_bytes() != (destination / name).read_bytes():
            raise ImportFailure("JSON eleitoral divergente; instalação recusada")
    allowed = {"manifest.json", *manifest["artifacts"]} - {PROOF_FILE}
    existing = {
        p.relative_to(destination).as_posix()
        for p in destination.rglob("*")
        if p.is_file() and p.name != ".gitkeep"
    }
    if existing != allowed:
        raise ImportFailure("Assets existentes misturados ou não declarados")
    proof = (source / PROOF_FILE).read_bytes()
    with (destination / PROOF_FILE).open("xb") as stream:
        stream.write(proof)
    try:
        # Same-volume atomic replacement; payload files and .gitkeep remain untouched.
        with tempfile.NamedTemporaryFile(
            dir=destination, prefix="manifest-", suffix=".tmp", delete=False
        ) as stream:
            temp = Path(stream.name)
            stream.write(replacement)
        try:
            if (destination / "manifest.json").read_bytes() != old:
                raise ImportFailure("Manifesto editado durante a instalação; edição preservada")
            os.replace(temp, destination / "manifest.json")
        finally:
            temp.unlink(missing_ok=True)
        validate_embedded(destination)
    except BaseException:
        if (destination / "manifest.json").read_bytes() == replacement:
            (destination / "manifest.json").write_bytes(old)
        if (destination / PROOF_FILE).read_bytes() == proof:
            (destination / PROOF_FILE).unlink()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--national", type=Path, required=True)
    parser.add_argument("--embedded", type=Path, required=True)
    parser.add_argument("--references", type=Path, required=True)
    parser.add_argument("--hashes", type=Path, required=True)
    parser.add_argument("--testimony", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--install-to", type=Path)
    args = parser.parse_args()
    try:
        release = prepare(
            args.national, args.embedded, args.references, args.hashes, args.testimony, args.output
        )
        if args.install_to:
            install_metadata(release, args.install_to)
        print(release)
        return 0
    except (ImportFailure, OSError, KeyError, ValueError) as error:
        print("Preparação bloqueada: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""One sequential read per original ZIP, two digests, no extraction or network."""

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipelines"))
from tse_importer.domain import ImportFailure  # noqa: E402
from tse_importer.integrity import fingerprint  # noqa: E402
from tse_importer.workspace import no_links  # noqa: E402


def now():
    return datetime.now(UTC).isoformat()


def hash_once(path):
    no_links(path)
    before = fingerprint(path)
    digests = {algorithm: hashlib.new(algorithm) for algorithm in ("sha256", "sha512")}
    count = 0
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            count += len(chunk)
            for digest in digests.values():
                digest.update(chunk)
    if fingerprint(path) != before or count != before[0]:
        raise ImportFailure("Arquivo alterado durante a leitura: " + path.name)
    return {key: value.hexdigest() for key, value in digests.items()}, count


def collect(manifest_path, references_path, progress=print):
    raw = Path(manifest_path).read_bytes()
    manifest = json.loads(raw)
    reference_raw = Path(references_path).read_bytes()
    references = json.loads(reference_raw)
    manifest_sha = hashlib.sha256(raw).hexdigest()
    if references["national_manifest_sha256"] != manifest_sha:
        raise ImportFailure("Referências pertencem a outro manifesto nacional")
    sources = [s for s in manifest["sources"]["files"] if s["name"].endswith(".zip")]
    refs = {r["path"]: r for r in references["sources"]}
    if len(refs) != len(sources) or set(refs) != {s["path"] for s in sources}:
        raise ImportFailure("Conjunto de referências incompleto/duplicado")
    root = Path(manifest["sources"]["source_root"]).resolve()
    records = []
    started = now()
    for index, source in enumerate(sources, 1):
        path = root / source["path"]
        record = {
            "path": source["path"],
            "name": source["name"],
            "started_at": now(),
            "historical_hashes": source["hashes"],
            "historical_bytes": source["bytes"],
            "method": "single_sequential_read_sha256_sha512",
            "zip_extracted": False,
        }
        try:
            if not path.resolve().is_relative_to(root) or path.name != source["name"]:
                raise ImportFailure("Caminho de fonte inválido")
            current, count = hash_once(path)
            ref = refs[source["path"]].get("proposed_reference")
            record.update(
                current_hashes=current,
                bytes_read=count,
                bytes=count,
                historical_match=current == source["hashes"] and count == source["bytes"],
                official_reference_match=(
                    current.get(ref["algorithm"]) == ref["digest"] if ref else None
                ),
                official_reference=ref,
            )
            record["status"] = (
                "passed"
                if record["historical_match"] and record["official_reference_match"] is not False
                else "failed"
            )
        except (OSError, ImportFailure) as error:
            record.update(status="failed", error=str(error))
        record["finished_at"] = now()
        records.append(record)
        progress(f"{index}/{len(sources)} {source['name']}: {record['status']}")
    return {
        "schema_version": 1,
        "started_at": started,
        "finished_at": now(),
        "origin_release_id": manifest["release_id"],
        "origin_manifest_sha256": manifest_sha,
        "reference_evidence_sha256": hashlib.sha256(reference_raw).hexdigest(),
        "method": "single_sequential_read_sha256_sha512",
        "sources": records,
        "summary": {
            "sources": len(records),
            "passed": sum(s["status"] == "passed" for s in records),
            "bytes_read": sum(s.get("bytes_read", 0) for s in records),
            "official_reference_matches": sum(
                s.get("official_reference_match") is True for s in records
            ),
            "without_official_reference": sum(
                s.get("official_reference_match") is None for s in records
            ),
            "failures": sum(s["status"] != "passed" for s in records),
            "zip_downloads": 0,
            "zip_extractions": 0,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--references", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists():
        parser.error("Relatório existente é imutável; escolha outro destino")
    try:
        report = collect(args.manifest, args.references)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_bytes(
            (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf8")
        )
        print(json.dumps(report["summary"]))
        return 1 if report["summary"]["failures"] else 0
    except (ImportFailure, OSError, KeyError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

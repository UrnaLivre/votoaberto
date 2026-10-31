"""Validated, read-only SQLite -> immutable municipal JSON assets. No Flutter dependency."""

import hashlib
import json
import os
import sqlite3
import time
from collections import defaultdict
from pathlib import Path

from . import SCHEMA_VERSION, __version__
from .domain import TERRITORIES, ImportFailure, StoragePolicy
from .engine import _publish_pointer, peak_memory, validate_release
from .integrity import fingerprint, hashes
from .workspace import WorkRun, no_links

JSON_SCHEMA = 1
RULES_VERSION = "municipal-1"
METRICS = {
    "counted": "counted",
    "valid": "nominal",
    "blank": "blank",
    "null": "null_votes",
    "eligible": "eligible",
    "turnout": "turnout",
    "abstention": "abstention",
}


def canonical(value):
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf8")


def resolve_release(path):
    path = Path(path).absolute()
    no_links(path)
    if (path / "current.json").is_file():
        pointer = json.loads((path / "current.json").read_text(encoding="utf8"))
        target = (path / pointer["path"]).resolve()
        if target.parent != path.resolve() / "releases" or target.name != pointer["release_id"]:
            raise ImportFailure("Ponteiro de release inválido")
        path = target
    no_links(path)
    if not (path / "manifest.json").is_file():
        raise ImportFailure("Release e manifesto não encontrados")
    return path.resolve()


def read_only(path, work=None):
    no_links(path)
    db = sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA query_only=ON")
    db.execute("PRAGMA temp_store=FILE")
    if work:
        db.set_progress_handler(work.sql_progress, 20000)
    return db


def _write(work, stage, name, value):
    payload = canonical(value)
    work.check(len(payload) * 2)
    path = stage / name
    if path.exists():
        no_links(path)
        info = path.stat()
        if work.owned.get(str(path)) != (info.st_dev, info.st_ino):
            raise ImportFailure("Arquivo de exportação substituído")
    else:
        path = work.file(path)
    path.write_bytes(payload)


def _empty(election, turn):
    return {
        "election": election,
        "round": turn,
        "sections": 0,
        "candidates": {},
        "totals": dict.fromkeys(METRICS),
        "available_sections": dict.fromkeys(METRICS, 0),
    }


def _add(target, source):
    target["sections"] += source["sections"]
    for key in METRICS:
        value = source["totals"][key]
        if value is not None:
            target["totals"][key] = (target["totals"][key] or 0) + value
        target["available_sections"][key] += source["available_sections"][key]
    for key, votes in source["candidates"].items():
        target["candidates"][key] = target["candidates"].get(key, 0) + votes


def _check_round(record, catalog):
    total, available, count = record["totals"], record["available_sections"], record["sections"]
    if not count or any(type(v) is not int or not 0 <= v <= count for v in available.values()):
        raise ImportFailure("Cobertura de totais inválida")
    if any(value is not None and (type(value) is not int or value < 0) for value in total.values()):
        raise ImportFailure("Total inválido")
    if any((total[k] is None) != (available[k] == 0) for k in METRICS):
        raise ImportFailure("Disponibilidade inconsistente")
    if not record["candidates"] or any(
        k not in catalog or type(v) is not int or v < 0 for k, v in record["candidates"].items()
    ):
        raise ImportFailure("Candidato inválido")
    if sum(record["candidates"].values()) != total["valid"]:
        raise ImportFailure("Soma nominal divergente")
    if all(available[k] == count for k in ("valid", "blank", "null")):
        if total["valid"] + total["blank"] + total["null"] != total["counted"]:
            raise ImportFailure("Categorias divergentes")
    if available["turnout"] == count and total["turnout"] != total["counted"]:
        raise ImportFailure("Comparecimento divergente")
    if all(available[k] == count for k in ("eligible", "turnout", "abstention")):
        if total["eligible"] != total["turnout"] + total["abstention"]:
            raise ImportFailure("Aptos divergentes")


def _municipalities(db, work):
    """Section totals and candidate results deliberately use independent queries."""
    groups = {}
    fields = ",".join(
        f'SUM(t.{column}) "{key}",COUNT(t.{column}) n_{key}' for key, column in METRICS.items()
    )
    for row in db.execute(f"""SELECT s.election,e.round,s.uf,s.municipality,
        MIN(s.municipality_name) name,COUNT(DISTINCT s.municipality_name) names,
        COUNT(*) sections,{fields} FROM sections s JOIN elections e ON e.id=s.election
        JOIN section_totals t ON t.section_id=s.id
        GROUP BY s.election,s.uf,s.municipality ORDER BY s.uf,s.municipality,e.round"""):
        if row["names"] != 1:
            raise ImportFailure("Nome municipal inconsistente na eleição")
        record = _empty(row["election"], row["round"])
        record.update(
            sections=row["sections"],
            totals={k: row[k] for k in METRICS},
            available_sections={k: row["n_" + k] for k in METRICS},
        )
        groups[(row["election"], row["uf"], row["municipality"])] = (row["name"], record)
    # Bounded by municipal results, never section-level Python objects.
    for row in db.execute("""SELECT s.election,s.uf,s.municipality,c.number,SUM(r.votes) votes
        FROM results r JOIN sections s ON s.id=r.section_id JOIN candidates c ON c.id=r.candidate_id
        WHERE c.kind='nominal' GROUP BY s.election,s.uf,s.municipality,c.number"""):
        groups[(row["election"], row["uf"], row["municipality"])][1]["candidates"][
            row["election"] + ":" + row["number"]
        ] = row["votes"]
    work.check()
    return groups


def validate_embedded(directory, db=None, *, allow_pending=False):
    """Read serialized artifacts, re-sum hierarchy and independently compare SQLite GROUP BYs."""
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf8"))
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != JSON_SCHEMA:
        raise ImportFailure("Schema JSON incompatível")
    if manifest.get("validation") != "passed" and not allow_pending:
        raise ImportFailure("Dataset ainda não validado")
    dataset_id = manifest["dataset_id"]
    assessment = manifest.get("source_assessment", {})
    new_policy = (
        assessment.get("source_hashes", {}).get("status")
        == "current_local_integrity_and_available_official_references_matched"
    )
    if (
        "metadata_release_id" in manifest
        or "provenance_review" in manifest
        or "provenance" in assessment
        or new_policy
    ):
        if "metadata_release_id" not in manifest or "provenance_review" not in manifest:
            raise ImportFailure("Proveniência: release de metadados sem dossiê/identidade completa")
    uf_codes = manifest["territories"]
    if not uf_codes or uf_codes != sorted(set(uf_codes)) or not set(uf_codes) <= TERRITORIES:
        raise ImportFailure("Abrangências JSON inválidas")
    expected = {"national.json", "states.json", "validation.json"} | {
        f"municipalities/{uf}.json" for uf in uf_codes
    }
    if "provenance_review" in manifest:
        expected.add("provenance.json")
    if set(manifest["artifacts"]) != expected:
        raise ImportFailure("Lista de artefatos incompleta")
    for name, info in manifest["artifacts"].items():
        no_links(directory / name)
        if (
            hashes(directory / name)["sha256"] != info["sha256"]
            or (directory / name).stat().st_size != info["bytes"]
        ):
            raise ImportFailure("Hash/tamanho JSON divergente: " + name)
    if "provenance_review" in manifest:
        from .provenance import validate_metadata_release

        validate_metadata_release(directory, manifest)

    def load(name):
        data = json.loads((directory / name).read_text(encoding="utf8"))
        if data.get("schema_version") != JSON_SCHEMA or data.get("dataset_id") != dataset_id:
            raise ImportFailure("Versões de dataset misturadas")
        return data

    elections = {e["id"]: e for e in manifest["elections"]}
    if len(elections) != len(manifest["elections"]) or any(
        e["office"] != "president" or e["round"] not in (1, 2) for e in elections.values()
    ):
        raise ImportFailure("Eleições incompatíveis no manifesto")
    catalogs = {key: {c["id"] for c in e["candidates"]} for key, e in elections.items()}
    states = load("states.json")["territories"]
    if [s["code"] for s in states] != uf_codes:
        raise ImportFailure("Abrangências inconsistentes")
    municipal_count = {}
    by_state = {}
    municipal_rows = 0
    municipal_results = {}
    municipal_names = {}
    for state in states:
        uf = state["code"]
        data = load(f"municipalities/{uf}.json")
        if data["uf"] != uf:
            raise ImportFailure("UF municipal divergente")
        codes = set()
        sums = {}
        for city in data["municipalities"]:
            if (
                not isinstance(city["code"], str)
                or not city["code"]
                or city["code"] in codes
                or not city["name"]
            ):
                raise ImportFailure("Identificador municipal inválido/duplicado")
            codes.add(city["code"])
            seen = set()
            for record in city["rounds"]:
                election = record["election"]
                if (
                    election not in elections
                    or election in seen
                    or record["round"] != elections[election]["round"]
                ):
                    raise ImportFailure("Eleição/turno inválido")
                seen.add(election)
                _check_round(record, catalogs[election])
                _add(sums.setdefault(election, _empty(election, record["round"])), record)
                municipal_results[(election, uf, city["code"])] = record
                municipal_names[(election, uf, city["code"])] = city["name"]
                municipal_rows += 1
        if len(codes) != manifest["municipality_counts"][uf]:
            raise ImportFailure("Quantidade municipal divergente")
        municipal_count[uf] = len(codes)
        if list(sums.values()) != state["rounds"]:
            raise ImportFailure("Soma municipal/estadual divergente")
        by_state[uf] = sums
    national = load("national.json")
    for key, selected in (
        ("rounds", uf_codes),
        ("domestic_rounds", [uf for uf in uf_codes if uf != "ZZ"]),
    ):
        sums = {}
        for uf in selected:
            for election, record in by_state[uf].items():
                _add(sums.setdefault(election, _empty(election, record["round"])), record)
        if list(sums.values()) != national[key]:
            raise ImportFailure("Soma nacional divergente: " + key)
    if db:
        actual_elections = [
            dict(row) for row in db.execute("SELECT * FROM elections ORDER BY round,id")
        ]
        if actual_elections != [
            {k: e[k] for k in ("id", "year", "round", "office")} for e in manifest["elections"]
        ]:
            raise ImportFailure("Identidade das eleições JSON/SQLite divergente")
        for election, entry in elections.items():
            actual = [
                {
                    "id": election + ":" + row["number"],
                    "number": row["number"],
                    "name": row["name"],
                    "source_candidate_id": row["source_candidate_id"],
                }
                for row in db.execute(
                    "SELECT * FROM candidates WHERE election=? AND kind='nominal' ORDER BY number",
                    (election,),
                )
            ]
            if actual != entry["candidates"]:
                raise ImportFailure("Identidade dos candidatos JSON/SQLite divergente")
        # Independent direct SQLite totals: no results JOIN in this totals query.
        fields = ",".join(f"SUM(t.{column}),COUNT(t.{column})" for column in METRICS.values())
        checked = set()
        for row in db.execute(f"""SELECT s.election,s.uf,s.municipality,COUNT(*),{fields}
            FROM section_totals t JOIN sections s ON s.id=t.section_id
            GROUP BY s.election,s.uf,s.municipality"""):
            key = tuple(row[:3])
            record = municipal_results.get(key)
            if record is None or record["sections"] != row[3]:
                raise ImportFailure("Cobertura JSON/SQLite divergente")
            for i, metric in enumerate(METRICS):
                if (record["totals"][metric], record["available_sections"][metric]) != (
                    row[4 + i * 2],
                    row[5 + i * 2],
                ):
                    raise ImportFailure("Total municipal JSON/SQLite divergente")
            checked.add(key)
        if checked != set(municipal_results):
            raise ImportFailure("Municípios adicionais no JSON")
        for row in db.execute(
            "SELECT election,uf,municipality,MIN(municipality_name),COUNT(DISTINCT municipality_name) FROM sections GROUP BY election,uf,municipality"
        ):
            if row[4] != 1 or municipal_names.get(tuple(row[:3])) != row[3]:
                raise ImportFailure("Nome municipal JSON/SQLite divergente")
        votes = defaultdict(dict)
        for row in db.execute("""SELECT s.election,s.uf,s.municipality,c.number,SUM(r.votes)
            FROM candidates c JOIN results r ON r.candidate_id=c.id JOIN sections s ON s.id=r.section_id
            WHERE c.kind='nominal' GROUP BY s.election,s.uf,s.municipality,c.number"""):
            votes[tuple(row[:3])][row[0] + ":" + row[3]] = row[4]
        if any(record["candidates"] != votes[key] for key, record in municipal_results.items()):
            raise ImportFailure("Votos municipais JSON/SQLite divergentes")
        for row in db.execute("""SELECT s.election,s.uf,s.municipality,c.kind,SUM(r.votes)
            FROM results r JOIN sections s ON s.id=r.section_id JOIN candidates c ON c.id=r.candidate_id
            GROUP BY s.election,s.uf,s.municipality,c.kind"""):
            category = {"nominal": "valid", "blank": "blank", "null": "null"}.get(row[3])
            if category is None or municipal_results[tuple(row[:3])]["totals"][category] != row[4]:
                raise ImportFailure("Categoria municipal JSON/SQLite divergente")
        # A second aggregation directly at UF level guards hierarchy/key mistakes.
        for row in db.execute("""SELECT s.election,s.uf,c.number,SUM(r.votes) FROM results r
            JOIN sections s ON s.id=r.section_id JOIN candidates c ON c.id=r.candidate_id
            WHERE c.kind='nominal' GROUP BY s.election,s.uf,c.number"""):
            if by_state[row[1]][row[0]]["candidates"].get(row[0] + ":" + row[2]) != row[3]:
                raise ImportFailure("Voto estadual JSON/SQLite divergente")
    return {
        "status": "passed",
        "differences": [],
        "municipality_counts": municipal_count,
        "municipal_round_records": municipal_rows,
        "sqlite_comparison": "passed" if db else "not_repeated",
        "national": national,
        "territories": states,
    }


def export_embedded(source, output, policy=None, progress=lambda message: None):
    policy = policy or StoragePolicy()
    start = time.perf_counter()
    no_links(Path(output).absolute())
    source, output = resolve_release(source), Path(output).resolve()
    no_links(output)
    if output == source or output.is_relative_to(source) or source.is_relative_to(output):
        raise ImportFailure("Saída deve ser separada da release original")
    output.mkdir(parents=True, exist_ok=True)
    lock = output / ".export.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        with WorkRun(output, policy) as work:
            original = source / "election.sqlite"
            original_identity = fingerprint(original)
            manifest_identity = fingerprint(source / "manifest.json")
            origin = json.loads((source / "manifest.json").read_text(encoding="utf8"))
            if origin.get("data_kind") not in ("official", "synthetic"):
                raise ImportFailure("Natureza dos dados da release não suportada")
            if (
                type(origin.get("schema_version")) is not int
                or origin["schema_version"] != SCHEMA_VERSION
            ):
                raise ImportFailure("Schema SQLite de origem incompatível")
            progress("Validando a release SQLite original em modo somente leitura")
            result = validate_release(source)
            if fingerprint(source / "manifest.json") != manifest_identity:
                raise ImportFailure("Manifesto original mudou durante validação")
            for name, info in origin["artifacts"].items():
                if (
                    type(info.get("bytes")) is not int
                    or (source / name).stat().st_size != info["bytes"]
                ):
                    raise ImportFailure("Tamanho de artefato de origem divergente: " + name)
            if result["assessment"]["local_release"]["status"] != "eligible":
                raise ImportFailure("Release original inelegível")
            db = read_only(original, work)
            try:
                if db.execute("PRAGMA user_version").fetchone()[0] != SCHEMA_VERSION:
                    raise ImportFailure("Schema SQLite incompatível")
                elections = []
                for election in db.execute("SELECT * FROM elections ORDER BY round,id"):
                    entry = dict(election)
                    entry["candidates"] = [
                        {
                            "id": election["id"] + ":" + r["number"],
                            "number": r["number"],
                            "source_candidate_id": r["source_candidate_id"],
                            "name": r["name"],
                        }
                        for r in db.execute(
                            "SELECT * FROM candidates WHERE election=? AND kind='nominal' ORDER BY number",
                            (election["id"],),
                        )
                    ]
                    elections.append(entry)
                if not elections or any(e["office"] != "president" for e in elections):
                    raise ImportFailure("Eleição não suportada")
                rules_sha = hashlib.sha256(
                    Path(__file__).read_bytes().replace(b"\r\n", b"\n")
                ).hexdigest()
                dataset_id = hashlib.sha256(
                    canonical(
                        {
                            "source": origin["artifacts"]["election.sqlite"]["sha256"],
                            "schema": JSON_SCHEMA,
                            "rules": rules_sha,
                        }
                    )
                ).hexdigest()[:24]
                envelope = {"schema_version": JSON_SCHEMA, "dataset_id": dataset_id}
                stage = work.root / "staging"
                stage.mkdir()
                progress("Agregando municípios e totais de seção separadamente")
                groups = _municipalities(db, work)
                cities, states = {}, {}
                for (election, uf, code), (name, record) in groups.items():
                    city = cities.setdefault(uf, {}).setdefault(
                        code, {"code": code, "name": name, "rounds": []}
                    )
                    if city["name"] != name:
                        raise ImportFailure(
                            "Nome municipal varia entre turnos; interpretação necessária"
                        )
                    city["rounds"].append(record)
                    _add(
                        states.setdefault(uf, {}).setdefault(
                            election, _empty(election, record["round"])
                        ),
                        record,
                    )
                national, domestic = {}, {}
                for uf, rounds in sorted(states.items()):
                    for election, record in rounds.items():
                        _add(
                            national.setdefault(election, _empty(election, record["round"])), record
                        )
                        if uf != "ZZ":
                            _add(
                                domestic.setdefault(election, _empty(election, record["round"])),
                                record,
                            )
                _write(
                    work,
                    stage,
                    "national.json",
                    {
                        **envelope,
                        "includes_abroad": "ZZ" in states,
                        "rounds": list(national.values()),
                        "domestic_rounds": list(domestic.values()),
                    },
                )
                _write(
                    work,
                    stage,
                    "states.json",
                    {
                        **envelope,
                        "territories": [
                            {"code": uf, "rounds": list(rounds.values())}
                            for uf, rounds in sorted(states.items())
                        ],
                    },
                )
                for uf, municipalities in sorted(cities.items()):
                    _write(
                        work,
                        stage,
                        f"municipalities/{uf}.json",
                        {
                            **envelope,
                            "uf": uf,
                            "municipalities": [city for _, city in sorted(municipalities.items())],
                        },
                    )
                data_files = [p.relative_to(stage).as_posix() for p in stage.rglob("*.json")]
                normalized_bytes = sum((stage / name).stat().st_size for name in data_files)
                catalog = {c["id"]: c for e in elections for c in e["candidates"]}

                # Serialize the alternative, without keeping another dataset on disk.
                def inline(value):
                    if isinstance(value, list):
                        return [inline(v) for v in value]
                    if not isinstance(value, dict):
                        return value
                    return {
                        k: [{**catalog[c], "votes": votes} for c, votes in v.items()]
                        if k == "candidates"
                        else inline(v)
                        for k, v in value.items()
                    }

                simple_bytes = sum(
                    len(canonical(inline(json.loads((stage / name).read_text(encoding="utf8")))))
                    for name in data_files
                )
                _write(
                    work,
                    stage,
                    "validation.json",
                    {
                        **envelope,
                        "status": "pending",
                        "method": "municipal JSON versus independent SQLite totals/results, UF direct SQL and hierarchy sums",
                        "differences": [],
                        "municipality_counts": {uf: len(c) for uf, c in sorted(cities.items())},
                        "municipal_round_records": len(groups),
                        "representation_bytes": {
                            "normalized": normalized_bytes,
                            "inline_names": simple_bytes,
                        },
                    },
                )
                manifest = {
                    **envelope,
                    "exporter_version": __version__,
                    "rules_version": RULES_VERSION,
                    "rules_sha256": rules_sha,
                    "data_nature": "synthetic"
                    if origin["data_kind"] == "synthetic"
                    else "official-derived",
                    "source_release": origin["release_id"],
                    "source_sqlite_sha256": origin["artifacts"]["election.sqlite"]["sha256"],
                    "source_schema_version": origin["schema_version"],
                    "source_assessment": result["assessment"],
                    "public_readiness": result["assessment"]["public_readiness"],
                    "local_preview": True,
                    "elections": elections,
                    "territories": sorted(states),
                    "municipality_counts": {uf: len(c) for uf, c in sorted(cities.items())},
                    "attribution": "Tribunal Superior Eleitoral; processamento independente VotoAberto"
                    if origin["data_kind"] != "synthetic"
                    else "FICTÍCIO — fixture sintético VotoAberto",
                    "source_metadata": [
                        s["metadata"] for s in origin["sources"]["files"] if s.get("metadata")
                    ],
                    "limitations": origin["limitations"]
                    + [
                        "TSE municipality identifiers are not IBGE codes",
                        "No section completeness or origin authentication implied",
                        "Partial totals retain counts of sections with values; missing values are not zero",
                    ],
                    "validation": "pending",
                    "artifacts": {
                        name: {
                            "bytes": (stage / name).stat().st_size,
                            "sha256": hashes(stage / name)["sha256"],
                        }
                        for name in sorted(data_files + ["validation.json"])
                    },
                }
                _write(work, stage, "manifest.json", manifest)
                progress("Conferindo JSONs serializados contra a release original")
                validation_summary = validate_embedded(stage, db, allow_pending=True)
                final_validation = json.loads(
                    (stage / "validation.json").read_text(encoding="utf8")
                )
                final_validation["status"] = "passed"
                _write(work, stage, "validation.json", final_validation)
                manifest["validation"] = "passed"
                manifest["artifacts"]["validation.json"] = {
                    "bytes": (stage / "validation.json").stat().st_size,
                    "sha256": hashes(stage / "validation.json")["sha256"],
                }
                _write(work, stage, "manifest.json", manifest)
                if fingerprint(original) != original_identity:
                    raise ImportFailure("SQLite original mudou durante a exportação")
                work.check()
            finally:
                db.close()
            releases = output / "releases"
            no_links(releases)
            releases.mkdir(exist_ok=True)
            release = releases / dataset_id
            no_links(release)
            if release.exists():
                validate_embedded(release)
                if (release / "manifest.json").read_bytes() != (
                    stage / "manifest.json"
                ).read_bytes():
                    raise ImportFailure("Versão imutável já existe com conteúdo diferente")
            else:
                with work.mutex:
                    stage.rename(release)
                    work.promoted_to(stage, release)
            try:
                _publish_pointer(output, dataset_id)
            except BaseException:
                if work.promoted:
                    with work.mutex:
                        release.rename(stage)
                        work.demoted_to(release, stage)
                raise
            work.published = True
        return {
            "release": str(release),
            "dataset_id": dataset_id,
            "elapsed_seconds": round(time.perf_counter() - start, 3),
            "memory": peak_memory(),
            "storage": json.loads(work.ledger.read_text(encoding="utf8"))["metrics"],
            "dataset_bytes": sum(p.stat().st_size for p in release.rglob("*") if p.is_file()),
            "validation": validation_summary,
        }
    except sqlite3.Error:
        if "work" in locals() and work.failure is not None:
            work.save("failed", str(work.failure))
            raise work.failure from None
        raise
    finally:
        lock.unlink(missing_ok=True)

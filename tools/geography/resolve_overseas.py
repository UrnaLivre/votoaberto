"""Reproduce M5.2 from a reviewed TSE register and read-only observed section keys.

No network, electoral ZIP import, national rebuild, or write to existing releases.
Country literals are individually reviewed in zz_review_2026.json; names never
serve as join keys. The register describes locations, not certified voting events.
"""

import argparse
import copy
import csv
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "pipelines"))
from tse_importer.domain import ImportFailure  # noqa: E402
from tse_importer.embedded_exporter import canonical  # noqa: E402
from tse_importer.overseas_evidence import REGISTER_STATUS, validate_correspondence  # noqa: E402

BASELINE_SHA256 = "3b9924c27d4ae691d16f5e8f80d75363445bc5abac29e5621578a395dd404d5f"
FIELDS = ("NM_LOCAL_VOTACAO", "DS_ENDERECO", "NM_BAIRRO")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def register_rows(path):
    """Keep physical CSV record numbers; reject repeated identities, even identical."""
    with path.open(encoding="latin1", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        required = {
            *FIELDS,
            "AA_ELEICAO",
            "CD_MUNICIPIO",
            "SG_UF",
            "NR_TURNO",
            "NR_ZONA",
            "NR_SECAO",
            "NR_LOCAL_VOTACAO",
            "NR_SECAO_PRINCIPAL",
            "CD_TIPO_SECAO_AGREGADA",
            "DT_GERACAO",
            "HH_GERACAO",
        }
        if not required.issubset(reader.fieldnames or []):
            raise ImportFailure("Esquema do cadastro TSE incompatível")
        result = {}
        for number, row in enumerate(reader, 2):
            if row["SG_UF"] != "ZZ" or row["AA_ELEICAO"] != "2026":
                raise ImportFailure("Cadastro fora do exterior/ano investigado")
            key = tuple(row[k] for k in ("CD_MUNICIPIO", "NR_TURNO", "NR_ZONA", "NR_SECAO"))
            if key in result:
                raise ImportFailure("Identificador duplicado no cadastro oficial")
            result[key] = (number, row)
    return result


def reviewed_locality(old, decision, register, observed, source_id):
    """All observed keys, in each actual turn, must match a reviewed primary row."""
    keys = sorted(k for k in observed if k[0] == old["tse"])
    if not keys:
        raise ImportFailure("Localidade sem seções observadas")
    evidence = []
    for key in keys:
        if key not in register:
            raise ImportFailure(f"Seção observada ausente do cadastro: {key}")
        number, row = register[key]
        if row["CD_TIPO_SECAO_AGREGADA"] != "1" or row["NR_SECAO_PRINCIPAL"] != "-1":
            raise ImportFailure("Registro observado não é seção principal")
        if observed[key] != row["NR_LOCAL_VOTACAO"]:
            raise ImportFailure("Local de votação incompatível com o SQLite")
        evidence.append(
            {
                "source": source_id,
                "record": number,
                "iso": decision["iso"],
                "tse": key[0],
                "round": int(key[1]),
                "zone": key[2],
                "section": key[3],
                "local": row["NR_LOCAL_VOTACAO"],
                "primary_section": row["NR_SECAO_PRINCIPAL"],
                "country_field": decision["country_field"],
                "country_literal": decision["country_literal"],
                "fields": {field: row[field] for field in FIELDS},
            }
        )
    # Review covers all registered rows for this code, including aggregated rows.
    # The raw field values must be precisely the ones reviewed, not fuzzy matches.
    for key, (_, row) in register.items():
        if (
            key[0] == old["tse"]
            and {field: row[field] for field in FIELDS} != decision["reviewed_fields"]
        ):
            raise ImportFailure("Referências incompatíveis dentro da localidade")
    return {
        "tse": old["tse"],
        "name": old["name"],
        "iso": decision["iso"],
        "country": decision["country"],
        "status": REGISTER_STATUS,
        "origin": source_id,
        "verified_rounds": sorted({e["round"] for e in evidence}),
        "evidence": evidence,
        "candidate_countries": [decision["iso"]],
    }


def build(baseline, source, csv_path, sqlite_path, review_path, output):
    if output.exists():
        raise ImportFailure("Destino geográfico existente; sobreposição recusada")
    original = (baseline / "overseas_correspondence.json").read_bytes()
    if sha(original) != BASELINE_SHA256:
        raise ImportFailure("Baseline M5 incompatível")
    crosswalk = json.loads(original)
    review = json.loads(review_path.read_text(encoding="utf8"))
    evidence_source = review["source"]
    if sha(csv_path.read_bytes()) != evidence_source["member_sha256"]:
        raise ImportFailure("Cadastro difere dos bytes oficialmente inspecionados")
    register = register_rows(csv_path)
    if any(
        f"{row['DT_GERACAO']} {row['HH_GERACAO']}" != evidence_source["version"]
        for _, row in register.values()
    ):
        raise ImportFailure("Versão interna do cadastro incompatível")
    with sqlite3.connect(sqlite_path.resolve().as_uri() + "?mode=ro", uri=True) as db:
        db.execute("PRAGMA query_only=ON")
        observed = {}
        for code, turn, zone, section, local in db.execute(
            "SELECT s.municipality,e.round,s.zone,s.section,s.local FROM sections s "
            "JOIN elections e ON s.election=e.id WHERE s.uf='ZZ' AND e.year=2026"
        ):
            key = (code, str(turn), zone, section)
            if key in observed:
                raise ImportFailure("Identificador duplicado no SQLite")
            observed[key] = local
    zz = json.loads((source / "municipalities/ZZ.json").read_text(encoding="utf8"))
    if zz["dataset_id"] != crosswalk["source_dataset_id"]:
        raise ImportFailure("Outra versão eleitoral M4")
    decisions = {d["tse"]: d for d in review["decisions"]}
    pending = {r["tse"] for r in crosswalk["localities"] if r["iso"] is None}
    if len(decisions) != len(review["decisions"]) or set(decisions) != pending:
        raise ImportFailure("Revisão deve cobrir exatamente as 28 pendências sem duplicação")
    baseline_rows = copy.deepcopy(crosswalk["localities"])
    source_id = "tse_locations_2026"
    for i, old in enumerate(crosswalk["localities"]):
        decision = decisions.get(old["tse"])
        if decision and decision["status"] == "verified":
            crosswalk["localities"][i] = reviewed_locality(
                old, decision, register, observed, source_id
            )
    crosswalk["schema_version"] = 2
    crosswalk["evidence_sources"] = {source_id: evidence_source}
    mapping = validate_correspondence(crosswalk["localities"], crosswalk["evidence_sources"])
    for loc in zz["municipalities"]:
        match = mapping[loc["code"]]
        if match["status"] == REGISTER_STATUS:
            if match["verified_rounds"] != sorted(r["round"] for r in loc["rounds"]) or any(
                sum(e["round"] == r["round"] for e in match["evidence"]) != r["sections"]
                for r in loc["rounds"]
            ):
                raise ImportFailure("Seções/turnos não reconciliam com M4")
    assert all(mapping[r["tse"]] == r for r in baseline_rows if r["iso"])
    manifest = json.loads((baseline / "manifest.json").read_bytes())
    for name, info in manifest["artifacts"].items():
        raw = (baseline / name).read_bytes()
        if len(raw) != info["bytes"] or sha(raw) != info["sha256"]:
            raise ImportFailure("Baseline geográfico adulterado")
    manifest["version"] = "geography-2026-2"
    manifest["sources"][source_id] = evidence_source
    manifest["derivation"] = {
        "baseline_correspondence_sha256": BASELINE_SHA256,
        "review_sha256": sha(review_path.read_bytes()),
        "source_dataset_id": crosswalk["source_dataset_id"],
    }
    output.mkdir(parents=True, exist_ok=False)
    for name in manifest["artifacts"]:
        raw = (
            canonical(crosswalk)
            if name == "overseas_correspondence.json"
            else (baseline / name).read_bytes()
        )
        (output / name).write_bytes(raw)
        manifest["artifacts"][name] = {"bytes": len(raw), "sha256": sha(raw)}
    (output / "manifest.json").write_bytes(canonical(manifest))
    return {
        "mapped": sum(bool(r["iso"]) for r in mapping.values()),
        "countries": len({r["iso"] for r in mapping.values() if r["iso"]}),
        "manifest_sha256": sha(canonical(manifest)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("baseline", "source", "register", "sqlite", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    parser.add_argument(
        "--review", type=Path, default=Path(__file__).with_name("zz_review_2026.json")
    )
    args = parser.parse_args()
    print(
        json.dumps(
            build(args.baseline, args.source, args.register, args.sqlite, args.review, args.output)
        )
    )


if __name__ == "__main__":
    main()

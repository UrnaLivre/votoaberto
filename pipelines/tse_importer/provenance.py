"""Versioned, scope-limited evidence policy; technical eligibility is not human approval."""

import copy
import hashlib
import json
from pathlib import PurePosixPath
from types import SimpleNamespace
from urllib.parse import urlsplit

from .assessment import coverage_assessment, reconciliation_assessment
from .domain import TERRITORIES, CoverageRequirements, ImportFailure
from .integrity import checksum_line

POLICY_ID = "tse-presidential-documented-provenance-1"
PROOF_FILE = "provenance.json"
DOCUMENTS = {
    "national_manifest",
    "national_validation_report",
    "embedded_manifest",
    "source_references",
    "current_hashes",
    "acquisition_testimony",
}


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
    ).encode("utf8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ImportFailure("Proveniência: " + message)


def official(url, host):
    parsed = urlsplit(url or "")
    return (
        parsed.scheme == "https"
        and parsed.hostname == host
        and not parsed.username
        and not parsed.password
        and parsed.port in (None, 443)
    )


def indexed(items, key):
    result = {item[key]: item for item in items}
    require(len(result) == len(items), "fontes duplicadas")
    return result


def unpack_documents(review):
    require(review.get("schema_version") == 1, "schema de evidência desconhecido")
    require(review.get("policy_id") == POLICY_ID, "política desconhecida")
    require(set(review.get("documents", {})) == DOCUMENTS, "documentação incompleta")
    result = {}
    for key, document in review["documents"].items():
        raw = document["content"].encode("utf8")
        require(sha256(raw) == document["sha256"], "hash documental divergente: " + key)
        result[key] = json.loads(raw)
    return result


def official_reference(evidence, current, name):
    """Verify the actual recorded checksum text, not a 'trusted' or 'match' flag."""
    reference = evidence.get("proposed_reference")
    if not reference:
        return False
    require(
        evidence.get("official_reference_in_catalog") is True, "referência sem vínculo ao catálogo"
    )
    request = evidence["reference_requests"][-1]
    url = reference["origin"]
    require(official(url, "cdn.tse.jus.br"), "URL de checksum não oficial/HTTPS")
    require(
        request["http_status"] == 200
        and request["requested_url"] == url
        and request["final_url"] == url,
        "consulta de checksum incompleta",
    )
    require(
        request.get("tls_verification") == "platform_default_trust_store",
        "consulta sem evidência TLS",
    )
    require(request.get("finished_at") and request.get("started_at"), "consulta sem data")
    require(
        request["catalog_resource"]["id"] and request["catalog_resource"]["url"] == url,
        "recurso de checksum inexistente",
    )
    body = request["checksum_text"].encode("ascii")
    require(sha256(body) == request["body_sha256"], "corpo de checksum divergente")
    algorithm = reference["algorithm"]
    require(algorithm == "sha512", "esta versão da política exige referência BWEB SHA-512")
    digest = checksum_line(body.decode("ascii").replace("\r\n", "\n"), name, algorithm)
    require(digest == reference["digest"] == current[algorithm], "hash oficial divergente")
    return True


def supported_scope(stats, rounds):
    return {
        (int(row["round"]), row["uf"])
        for item in stats
        for row in item["coverage_read"]
        if row["office"] == "1" and int(row["round"]) in rounds and row["rows"] > 0
    }


def evaluate(review):
    """Recompute eligibility from bound documents; never create operator trust declarations."""
    try:
        return _evaluate(review)
    except (KeyError, TypeError, ValueError, IndexError, UnicodeError) as error:
        raise ImportFailure(
            "Proveniência: evidência incompleta ou inválida: " + str(error)
        ) from error


def _evaluate(review):
    docs = unpack_documents(review)
    national, mini = docs["national_manifest"], docs["embedded_manifest"]
    historical, references = docs["national_validation_report"], docs["source_references"]
    current, testimony = docs["current_hashes"], docs["acquisition_testimony"]
    national_sha = review["documents"]["national_manifest"]["sha256"]
    require(
        national["data_kind"] == "official" and mini["data_nature"] == "official-derived",
        "fixtures/natureza incompatível",
    )
    require(mini["source_release"] == national["release_id"], "release de origem divergente")
    require(
        mini["source_sqlite_sha256"] == national["artifacts"]["election.sqlite"]["sha256"],
        "SQLite de outra release",
    )
    require(
        review["documents"]["national_validation_report"]["sha256"]
        == national["artifacts"]["validation.json"]["sha256"],
        "reconciliação não vinculada ao manifesto",
    )
    require(
        current["origin_manifest_sha256"] == references["national_manifest_sha256"] == national_sha,
        "evidências de outro manifesto",
    )
    require(
        current["origin_release_id"] == references["national_release_id"] == national["release_id"],
        "evidências de outra release",
    )
    require(
        current["reference_evidence_sha256"] == review["documents"]["source_references"]["sha256"],
        "referências diferentes das usadas no recálculo",
    )
    require(
        testimony["origin_manifest_sha256"] == national_sha
        and testimony["origin_release_id"] == national["release_id"],
        "aquisição de outra release",
    )
    require(
        testimony["basis"] == "operator_testimony_from_user_message"
        and testimony["statement"]
        and testimony["declared_by"]
        and testimony["recorded_on"],
        "testemunho de aquisição ausente",
    )
    require(
        testimony["is_digital_signature"] is False
        and testimony["is_independent_cryptographic_proof"] is False,
        "testemunho descrito incorretamente",
    )

    selection = copy.deepcopy(national["selection"])
    require(
        selection["offices"] == ["president"] and selection["profile"] == "public",
        "política limitada a resultados presidenciais derivados",
    )
    require(
        all(
            e["office"] == "president" and e["year"] == selection["election_year"]
            for e in mini["elections"]
        ),
        "escopo eleitoral incompatível",
    )
    for key in ("offices", "rounds", "territories"):
        selection[key] = tuple(selection[key])
    # This policy evaluates already imported evidence; it does not enable parsers
    # for a future election. Import Selection deliberately remains layout-2026-only.
    require(
        type(selection["election_year"]) is int and selection["election_year"] > 0, "ano inválido"
    )
    require(
        bool(selection["rounds"])
        and all(type(r) is int and r in (1, 2) for r in selection["rounds"]),
        "turnos inválidos",
    )
    require(
        bool(selection["territories"])
        and (selection["territories"] == ("ALL",) or set(selection["territories"]) <= TERRITORIES),
        "territórios inválidos",
    )
    require(
        all(len(selection[k]) == len(set(selection[k])) for k in ("rounds", "territories")),
        "escopo duplicado",
    )
    requirements = CoverageRequirements(
        **{key: tuple(value) for key, value in national["coverage_requirements"].items()}
    )
    snapshot = review["current_validation"]
    require(
        snapshot["assessment_scope"] == "release_with_retained_source_evidence",
        "validação não demonstra a linhagem da release",
    )
    require(
        snapshot["sqlite_sha256"] == mini["source_sqlite_sha256"],
        "validação vinculada a outro banco",
    )
    require(snapshot["structurally_valid"] is True, "estrutura inválida")
    for key in ("sqlite_integrity", "referential_integrity", "mathematics", "data_structure"):
        require(snapshot["checks"][key]["status"] == "passed", "validação insuficiente: " + key)
    require(
        snapshot["checks"]["mathematics"]["errors"] == 0
        and snapshot["checks"]["mathematics"]["sections_with_unavailable_totals"] == 0,
        "matemática incompleta",
    )
    coverage = coverage_assessment(
        snapshot["observed_coverage"], SimpleNamespace(**selection), requirements
    )
    require(coverage["status"] == "complete", "cobertura territorial incompleta")
    reconciliation = reconciliation_assessment(
        historical["reconciliation"],
        snapshot,
        evidence="retained_report_bound_to_current_database_and_current_source_bytes",
    )
    require(reconciliation["status"] == "complete", "reconciliação incompleta/divergente")
    require(
        reconciliation["matched_rows"] == snapshot["result_rows"] > 0,
        "linhas reconciliadas não cobrem os resultados",
    )

    sources = indexed(
        [s for s in national["sources"]["files"] if s["name"].lower().endswith(".zip")], "path"
    )
    calculated, external = (
        indexed(current["sources"], "path"),
        indexed(references["sources"], "path"),
    )
    require(
        bool(sources) and set(sources) == set(calculated) == set(external), "fontes ausentes/extras"
    )
    require(testimony["source_count"] == len(sources), "testemunho incompleto")
    for catalog in references["catalogs"]:
        require(
            official(catalog["catalog_url"], "dadosabertos.tse.jus.br")
            and catalog["request"]["http_status"] == 200,
            "catálogo indisponível/não oficial",
        )
    require(bool(references["catalogs"]), "catálogo ausente")

    stats = {}
    for item in national["source_stats"]:
        if item.get("format"):
            stats.setdefault(item["archive"], []).append(item)
    anchors, without_checksum, rows = set(), [], {"bweb": 0, "section": 0}
    records = []
    for path, source in sources.items():
        relative = PurePosixPath(path)
        require(
            not relative.is_absolute() and ".." not in relative.parts and "\\" not in path,
            "caminho de fonte inválido",
        )
        require(relative.name == source["name"], "nome de fonte divergente")
        entry, evidence = calculated[path], external[path]
        require(
            entry["status"] == "passed"
            and entry["method"] == "single_sequential_read_sha256_sha512",
            "recálculo atual ausente",
        )
        require(
            entry["started_at"] and entry["finished_at"] and entry["zip_extracted"] is False,
            "leitura atual sem registro",
        )
        require(
            entry["bytes_read"] == entry["bytes"] == source["bytes"] > 0, "tamanho atual divergente"
        )
        require(
            entry["current_hashes"]
            == entry["historical_hashes"]
            == source["hashes"]
            == evidence["retained_hashes"],
            "hash local atual divergente",
        )
        for algorithm, length in (("sha256", 64), ("sha512", 128)):
            digest = entry["current_hashes"][algorithm]
            require(
                len(digest) == length and all(c in "0123456789abcdef" for c in digest),
                "digest inválido",
            )
        members = stats.get(path, [])
        require(bool(members), "fonte sem importação/reconciliação demonstrada")
        formats = {s["format"] for s in members}
        require(
            len(formats) == 1 and formats <= {"bweb", "section"},
            "formato não coberto pela política",
        )
        fmt = next(iter(formats))
        require(
            all(s["crc_checked"] is True and s["quarantined_records"] == 0 for s in members),
            "integridade de importação insuficiente",
        )
        selected_rows = sum(s["rows_selected"] for s in members)
        require(selected_rows > 0, "fonte sem registros selecionados")
        rows[fmt] += selected_rows
        pairs = supported_scope(members, selection["rounds"])
        has_reference = official_reference(evidence, entry["current_hashes"], source["name"])
        if has_reference:
            require(entry["official_reference_match"] is True, "comparação oficial atual ausente")
            if fmt == "bweb":
                anchors |= pairs
        else:
            require(
                entry["official_reference_match"] is None and fmt == "section",
                "fonte sem referência fora da política",
            )
            resource = evidence["resource"]
            require(
                resource["id"]
                and not resource.get("hash")
                and official(resource["url"], "cdn.tse.jus.br"),
                "recurso oficial não identificado",
            )
            requests = evidence["reference_requests"]
            require(
                bool(requests)
                and all(
                    r["http_status"] in (404, 410)
                    and official(r["requested_url"], "cdn.tse.jus.br")
                    for r in requests
                ),
                "ausência de checksum não demonstrada",
            )
            head = evidence["additional_official_metadata"]
            require(
                head["method"] == "HEAD"
                and head["status"] == 200
                and head["url"] == resource["url"]
                and head["final_url"] == resource["url"],
                "metadados oficiais insuficientes",
            )
            require(
                int(head["headers"]["Content-Length"]) == source["bytes"],
                "tamanho oficial divergente",
            )
            without_checksum.append((path, pairs))
        records.append(
            {
                "path": path,
                "local_byte_integrity": "current_sha256_sha512_match_historical",
                "external_reference_integrity": "current_sha512_matches_recorded_official_reference"
                if has_reference
                else "not_published_at_checked_endpoints",
                "provenance": "official_catalog_and_operator_acquisition_testimony",
                "content_reconciliation": "complete_for_declared_presidential_scope",
                "signature_verification": "not_performed",
                "operator_reference_approval": "pending",
            }
        )
    require(
        rows["bweb"] == rows["section"] == reconciliation["matched_rows"],
        "reconciliação não cobre todas as fontes selecionadas",
    )
    for path, pairs in without_checksum:
        require(
            bool(pairs) and pairs <= anchors,
            "fonte sem checksum não coberta por BWEBs com checksum: " + path,
        )
    expected = {(p["round"], p["uf"]) for p in coverage["expected_pairs"]}
    require(expected <= anchors, "faltam BWEBs com referência para o recorte declarado")
    return {
        **snapshot["checks"],
        "coverage": coverage,
        "reconciliation": reconciliation,
        "source_hashes": {
            "status": "current_local_integrity_and_available_official_references_matched",
            "source_count": len(sources),
            "current_local_matches": len(sources),
            "official_reference_matches": len(sources) - len(without_checksum),
            "without_published_reference": len(without_checksum),
            "sources": records,
            "signature_verification": "not_performed",
            "origin_authentication": "not_performed",
        },
        "provenance": {
            "status": "documented_for_declared_scope",
            "policy_id": POLICY_ID,
            "operator_policy_approval": "pending",
        },
        "local_release": {"status": "eligible", "blockers": []},
        "public_readiness": {
            "status": "ready_for_declared_scope",
            "blockers": [],
            "scope": coverage["expected_pairs"],
            "section_completeness": "not_assessed",
            "origin_authentication": "not_performed",
            "meaning": "Elegibilidade técnica de derivados presidenciais; aprovação humana de política, referências e redistribuição ainda obrigatória",
        },
    }


def make_manifest(review, proof_bytes):
    assessment = evaluate(review)
    original = unpack_documents(review)["embedded_manifest"]
    result = copy.deepcopy(original)
    result["source_assessment"] = assessment
    result["public_readiness"] = assessment["public_readiness"]
    result["artifacts"][PROOF_FILE] = {"bytes": len(proof_bytes), "sha256": sha256(proof_bytes)}
    result["provenance_review"] = {
        "policy_id": POLICY_ID,
        "file": PROOF_FILE,
        "origin_embedded_manifest_sha256": review["documents"]["embedded_manifest"]["sha256"],
        "origin_national_manifest_sha256": review["documents"]["national_manifest"]["sha256"],
        "review_sha256": sha256(proof_bytes),
    }
    result["metadata_release_id"] = sha256(canonical(result))[:24]
    return result


def validate_metadata_release(directory, manifest):
    proof = (directory / PROOF_FILE).read_bytes()
    review = json.loads(proof)
    require(
        manifest == make_manifest(review, proof),
        "manifesto/avaliação não corresponde às evidências",
    )
    original = unpack_documents(review)["embedded_manifest"]
    # Dataset identity belongs to the unchanged electoral payload; metadata has its own identity.
    require(manifest["dataset_id"] == original["dataset_id"], "identidade dos dados alterada")

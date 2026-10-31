"""Fictional policy inputs: no network, real ZIPs, operator approval or publication."""

import copy
import importlib.util
import json
import shutil
from pathlib import Path

import pytest
from tse_importer.domain import ImportFailure
from tse_importer.embedded_exporter import validate_embedded
from tse_importer.provenance import (
    POLICY_ID,
    canonical,
    evaluate,
    make_manifest,
    sha256,
    validate_metadata_release,
)


def bind(value):
    raw = canonical(value)
    return {"content": raw.decode(), "sha256": sha256(raw)}


@pytest.fixture
def review():
    # 2030 proves this policy is not hardcoded to the production election/year.
    hashes = {"sha256": "a" * 64, "sha512": "b" * 128}
    sources, stats, refs, calculated = [], [], [], []
    for i, fmt in enumerate(["bweb", "bweb", "section"], 1):
        name = f"fictional-{i}.zip"
        sources.append({"path": name, "name": name, "bytes": 16, "hashes": hashes})
        stats.append(
            {
                "archive": name,
                "format": fmt,
                "crc_checked": True,
                "quarantined_records": 0,
                "rows_selected": 8 if i == 3 else 4,
                "coverage_read": [
                    {"office": "1", "round": str(r), "uf": "SC", "rows": 4}
                    for r in ([i] if i < 3 else [1, 2])
                ],
            }
        )
        url = "https://cdn.tse.jus.br/test-fixture/" + name
        ref = {
            "path": name,
            "retained_hashes": hashes,
            "resource": {"id": str(i), "url": url, "hash": ""},
        }
        if fmt == "bweb":
            text = hashes["sha512"] + "  " + name + "\n"
            ref.update(
                official_reference_in_catalog=True,
                proposed_reference={
                    "algorithm": "sha512",
                    "digest": hashes["sha512"],
                    "origin": url + ".sha512",
                    "trusted": False,
                },
                reference_requests=[
                    {
                        "http_status": 200,
                        "requested_url": url + ".sha512",
                        "final_url": url + ".sha512",
                        "tls_verification": "platform_default_trust_store",
                        "started_at": "2030-01-01T00:00:00Z",
                        "finished_at": "2030-01-01T00:00:01Z",
                        "catalog_resource": {"id": str(i), "url": url + ".sha512"},
                        "checksum_text": text,
                        "body_sha256": sha256(text.encode()),
                    }
                ],
            )
        else:
            ref.update(
                reference_requests=[{"http_status": 404, "requested_url": url + ".sha512"}],
                additional_official_metadata={
                    "method": "HEAD",
                    "status": 200,
                    "url": url,
                    "final_url": url,
                    "headers": {"Content-Length": "16"},
                },
            )
        refs.append(ref)
        calculated.append(
            {
                "path": name,
                "status": "passed",
                "method": "single_sequential_read_sha256_sha512",
                "started_at": "2030-01-01",
                "finished_at": "2030-01-01",
                "zip_extracted": False,
                "bytes": 16,
                "bytes_read": 16,
                "current_hashes": hashes,
                "historical_hashes": hashes,
                "official_reference_match": True if fmt == "bweb" else None,
            }
        )
    report = {
        "reconciliation": {
            "matched_rows": 8,
            "different_rows": 0,
            "bu_math_errors": 0,
            "only_section_rows": 0,
            "only_bu_rows": 0,
            "ambiguous_locations": 0,
        }
    }
    national = {
        "release_id": "fictional",
        "data_kind": "official",
        "selection": {
            "election_year": 2030,
            "offices": ["president"],
            "profile": "public",
            "rounds": [1, 2],
            "territories": ["SC"],
        },
        "coverage_requirements": {"territories": ["SC"], "rounds": [1, 2]},
        "sources": {"files": sources},
        "source_stats": stats,
        "artifacts": {
            "election.sqlite": {"sha256": "c" * 64},
            "validation.json": {"sha256": bind(report)["sha256"]},
        },
    }
    mini = {
        "dataset_id": "fictional-payload",
        "data_nature": "official-derived",
        "source_release": "fictional",
        "source_sqlite_sha256": "c" * 64,
        "elections": [{"year": 2030, "office": "president"}],
        "artifacts": {},
        "public_readiness": {"status": "not_ready"},
    }
    national_sha = bind(national)["sha256"]
    references = {
        "national_manifest_sha256": national_sha,
        "national_release_id": "fictional",
        "sources": refs,
        "catalogs": [
            {
                "catalog_url": "https://dadosabertos.tse.jus.br/dataset/test-fixture",
                "request": {"http_status": 200},
            }
        ],
    }
    current = {
        "origin_manifest_sha256": national_sha,
        "origin_release_id": "fictional",
        "reference_evidence_sha256": bind(references)["sha256"],
        "sources": calculated,
    }
    testimony = {
        "origin_manifest_sha256": national_sha,
        "origin_release_id": "fictional",
        "basis": "operator_testimony_from_user_message",
        "statement": "Fictional test testimony",
        "declared_by": "test harness",
        "recorded_on": "2030-01-01",
        "is_digital_signature": False,
        "is_independent_cryptographic_proof": False,
        "source_count": 3,
    }
    return {
        "schema_version": 1,
        "policy_id": POLICY_ID,
        "documents": {
            key: bind(value)
            for key, value in {
                "national_manifest": national,
                "national_validation_report": report,
                "embedded_manifest": mini,
                "source_references": references,
                "current_hashes": current,
                "acquisition_testimony": testimony,
            }.items()
        },
        "current_validation": {
            "assessment_scope": "release_with_retained_source_evidence",
            "sqlite_sha256": "c" * 64,
            "structurally_valid": True,
            "result_rows": 8,
            "comparison": {"matched": 2},
            "observed_coverage": [{"round": r, "uf": "SC", "sections": 1} for r in [1, 2]],
            "checks": {
                "sqlite_integrity": {"status": "passed"},
                "referential_integrity": {"status": "passed"},
                "data_structure": {"status": "passed"},
                "mathematics": {
                    "status": "passed",
                    "errors": 0,
                    "sections_with_unavailable_totals": 0,
                },
            },
        },
    }


def change(review, key, mutate):
    value = json.loads(review["documents"][key]["content"])
    mutate(value)
    review["documents"][key] = bind(value)


def test_policy_accepts_reconciled_source_without_supplier_checksum(review):
    result = evaluate(review)
    assert result["public_readiness"]["status"] == "ready_for_declared_scope"
    assert result["public_readiness"]["section_completeness"] == "not_assessed"
    assert result["source_hashes"]["official_reference_matches"] == 2
    assert result["source_hashes"]["without_published_reference"] == 1
    assert result["source_hashes"]["signature_verification"] == "not_performed"
    assert result["provenance"]["operator_policy_approval"] == "pending"


@pytest.mark.parametrize(
    "case",
    [
        "local_hash",
        "missing_source",
        "fingerprint_only",
        "different_origin",
        "short_read",
        "missing_testimony",
        "signature_claim",
    ],
)
def test_bad_current_hash_or_acquisition_evidence_blocks(review, case):
    if case == "missing_testimony":
        del review["documents"]["acquisition_testimony"]
    elif case == "signature_claim":
        change(review, "acquisition_testimony", lambda d: d.update(is_digital_signature=True))
    else:

        def mutate(d):
            if case == "local_hash":
                d["sources"][0]["current_hashes"] = {"sha256": "d" * 64, "sha512": "e" * 128}
            elif case == "missing_source":
                d["sources"].pop()
            elif case == "fingerprint_only":
                d["sources"][0]["method"] = "reused_local_fingerprint_cache"
            elif case == "different_origin":
                d["origin_manifest_sha256"] = "f" * 64
            else:
                d["sources"][0]["bytes_read"] = 15

        change(review, "current_hashes", mutate)
    with pytest.raises(ImportFailure):
        evaluate(review)


@pytest.mark.parametrize(
    "case", ["incomplete", "different_votes", "missing_coverage", "bad_math", "missing_anchor"]
)
def test_content_and_coverage_must_be_demonstrated(review, case):
    if case == "incomplete":
        review["current_validation"]["comparison"]["matched"] = 1
    elif case == "different_votes":
        review["current_validation"]["result_rows"] = 9
    elif case == "missing_coverage":
        review["current_validation"]["observed_coverage"].pop()
    elif case == "bad_math":
        review["current_validation"]["checks"]["mathematics"]["errors"] = 1
    else:
        change(review, "source_references", lambda d: d["sources"][0].pop("proposed_reference"))
        change(
            review,
            "current_hashes",
            lambda d: d.update(
                reference_evidence_sha256=review["documents"]["source_references"]["sha256"]
            ),
        )
    with pytest.raises(ImportFailure):
        evaluate(review)


@pytest.mark.parametrize(
    "case", ["missing", "checksum", "body", "http", "nonofficial", "head_size"]
)
def test_incomplete_external_evidence_cannot_pass(review, case):
    def mutate(d):
        first = d["sources"][0]
        if case == "missing":
            first["reference_requests"] = []
        elif case == "checksum":
            first["proposed_reference"]["digest"] = "d" * 128
        elif case == "body":
            first["reference_requests"][0]["checksum_text"] += "altered"
        elif case == "http":
            first["reference_requests"][0]["http_status"] = 503
        elif case == "nonofficial":
            first["proposed_reference"]["origin"] = "https://example.invalid/fake.sha512"
        else:
            d["sources"][2]["additional_official_metadata"]["headers"]["Content-Length"] = "17"

    change(review, "source_references", mutate)
    change(
        review,
        "current_hashes",
        lambda d: d.update(
            reference_evidence_sha256=review["documents"]["source_references"]["sha256"]
        ),
    )
    with pytest.raises(ImportFailure):
        evaluate(review)


@pytest.mark.parametrize("case", ["fixture", "other_office", "unbound_report", "bad_document_hash"])
def test_policy_never_extends_to_fixtures_or_unexamined_offices(review, case):
    if case == "fixture":
        change(review, "embedded_manifest", lambda d: d.update(data_nature="synthetic"))
    elif case == "other_office":
        change(review, "embedded_manifest", lambda d: d["elections"][0].update(office="senator"))
    elif case == "unbound_report":
        change(
            review,
            "national_validation_report",
            lambda d: d["reconciliation"].update(different_rows=1),
        )
    else:
        review["documents"]["current_hashes"]["sha256"] = "d" * 64
    with pytest.raises(ImportFailure):
        evaluate(review)


def test_metadata_has_new_identity_preserving_electoral_dataset_identity(review, tmp_path):
    original = copy.deepcopy(review)
    proof = canonical(review)
    manifest = make_manifest(review, proof)
    assert manifest["dataset_id"] == "fictional-payload"
    assert len(manifest["metadata_release_id"]) == 24
    (tmp_path / "provenance.json").write_bytes(proof)
    validate_metadata_release(tmp_path, manifest)
    manifest["public_readiness"]["status"] = "operator-forced"
    with pytest.raises(ImportFailure):
        validate_metadata_release(tmp_path, manifest)
    assert review == original


def test_rehash_reads_file_once_for_both_algorithms(tmp_path, monkeypatch):
    path = ROOT / "tools/provenance/rehash_local.py"
    spec = importlib.util.spec_from_file_location("rehash_local_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "fictional.zip"
    payload = b"synthetic test bytes" * 100
    source.write_bytes(payload)
    opened = []
    original = Path.open

    def counted(self, *args, **kwargs):
        opened.append(self)
        return original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", counted)
    digests, count = module.hash_once(source)
    assert opened == [source]
    assert count == len(payload) and digests["sha256"] == sha256(payload)


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("marker", ["metadata_release_id", "provenance", "new_hash_status"])
def test_removing_dossier_cannot_turn_new_policy_into_legacy_validation(tmp_path, marker):
    source = ROOT / "apps/votoaberto_flutter/assets/data/synthetic"
    target = tmp_path / "mixed"
    shutil.copytree(source, target)
    manifest_path = target / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    if marker == "metadata_release_id":
        manifest[marker] = "incomplete"
    elif marker == "provenance":
        manifest.setdefault("source_assessment", {})[marker] = {"policy_id": POLICY_ID}
    else:
        manifest.setdefault("source_assessment", {})["source_hashes"] = {
            "status": "current_local_integrity_and_available_official_references_matched"
        }
    manifest_path.write_bytes(canonical(manifest))
    with pytest.raises(ImportFailure, match="sem dossiê/identidade"):
        validate_embedded(target)

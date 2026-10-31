"""Offline regressions for evidence collection, distinct from publication approval."""

import copy
import importlib.util
import io
import json
import urllib.error
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "review_sources_test", ROOT / "tools/provenance/review_sources.py"
)
review = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(review)

URL = "https://cdn.tse.jus.br/example/sample.zip"
DIGEST = "a" * 128


@pytest.fixture
def source(tmp_path):
    # Not a ZIP: review_source must only stat it, never read electoral bytes.
    local = tmp_path / "sample.zip"
    local.write_bytes(b"synthetic test bytes")
    item = {
        "name": local.name,
        "path": local.name,
        "bytes": local.stat().st_size,
        "hashes": {"sha512": DIGEST, "sha256": "b" * 64},
        "fingerprint": list(review.fingerprint(local)),
        "hash_calculation": "reused_local_fingerprint_cache",
        "verification": {"reference": {"trusted": False}},
    }
    return item, tmp_path


def resource(url=URL, **extra):
    return {"id": "synthetic-resource", "name": "Synthetic test resource", "url": url, **extra}


def fetch_checksum(digest=DIGEST, filename="sample.zip", status=200):
    def fetch(url, **kw):
        review.safe_url(url)
        return {"http_status": status, "requested_url": url}, (
            f"{digest}  {filename}\r\n".encode() if status == 200 else b"not found"
        )

    return fetch


def test_new_official_reference_is_a_proposal_without_assigning_trust(source, monkeypatch):
    item, root = source
    before = copy.deepcopy(item)
    monkeypatch.setattr(Path, "open", lambda *a, **kw: pytest.fail("ZIP bytes were opened"))
    result = review.review_source(
        item, [resource(), resource(URL + ".sha512")], root, fetch_checksum()
    )
    assert result["digest_comparison"] == "match"
    assert result["official_reference_in_catalog"]
    assert result["proposed_reference"]["trusted"] is False
    assert result["operator_confirmation"] == "pending"
    assert result["local_byte_hash_recomputed"] is False
    assert result["origin_authentication"] == result["signature_verification"] == "not_performed"
    assert "pending_operator_and_byte_refresh" in result["confidence_proposal"]
    assert item == before


def test_digest_mismatch_is_explicit_and_never_trusted(source):
    item, root = source
    result = review.review_source(item, [resource()], root, fetch_checksum("c" * 128))
    assert result["digest_comparison"] == "mismatch"
    assert result["confidence_proposal"] == "blocked_local_file_changed_or_digest_mismatch"
    assert result["proposed_reference"]["trusted"] is False


@pytest.mark.parametrize("condition", ["missing", "changed"])
def test_fingerprint_cannot_certify_changed_or_missing_local_bytes(source, condition):
    item, root = source
    if condition == "missing":
        (root / item["name"]).unlink()
    else:
        (root / item["name"]).write_bytes(b"different fixture")
    result = review.review_source(item, [resource()], root, fetch_checksum())
    assert result["digest_comparison"] == "match"  # Only the retained digest was compared.
    assert not result["local_fingerprint_matches_manifest"]
    assert result["confidence_proposal"] == "blocked_local_file_changed_or_digest_mismatch"


@pytest.mark.parametrize("kind", ["absent", "wrong_filename", "html", "wrong_algorithm"])
def test_missing_or_invalid_references_remain_uncompared(source, kind):
    item, root = source

    def fetch(url):
        if kind == "absent":
            return {"http_status": 404}, b"not found"
        body = {
            "wrong_filename": f"{DIGEST}  unrelated.zip\n".encode(),
            "html": b"<html>not a checksum</html>",
            "wrong_algorithm": b"deadbeef  sample.zip\n",
        }[kind]
        return {"http_status": 200}, body

    result = review.review_source(item, [resource()], root, fetch)
    assert result["digest_comparison"] == "not_compared"
    assert "proposed_reference" not in result
    assert len(result["reference_requests"]) == 2


def test_catalog_typo_preserves_both_aliases_and_missing_zip_binding(source):
    item, root = source
    entries = [
        resource(URL + ".sha512", id="zip-entry", name="Wrong ZIP entry"),
        resource(URL + ".sha512", id="hash-entry", name="Hash entry"),
    ]
    result = review.review_source(item, entries, root, fetch_checksum())
    assert result["resource"] is None
    assert result["source_url"] == URL
    assert result["source_url_evidence"] == "inferred_from_catalog_checksum_url_not_zip_fetch"
    aliases = result["reference_requests"][0]["catalog_resource"]["catalog_aliases"]
    assert {entry["id"] for entry in aliases} == {"zip-entry", "hash-entry"}
    assert result["digest_comparison"] == "match"


def test_same_filename_at_different_urls_is_ambiguous():
    with pytest.raises(review.ImportFailure, match="ambíguo"):
        review.resource_for([resource(), resource(URL.replace("example", "other"))], "sample.zip")


def test_unknown_resource_does_not_invent_origin(source):
    item, root = source
    result = review.review_source(item, [], root, lambda url: pytest.fail("unexpected request"))
    assert result["reference_state"] == "source_resource_not_found_in_current_catalog"
    assert result["reference_requests"] == []


@pytest.mark.parametrize(
    "url",
    [
        URL,
        URL.replace(".zip", ".%7Aip"),
        "http://cdn.tse.jus.br/a.sha512",
        "https://unrelated.example/a.sha512",
        "https://user@cdn.tse.jus.br/a.sha512",
    ],
)
def test_nonofficial_insecure_and_zip_requests_are_refused(url):
    with pytest.raises(review.ImportFailure):
        review.safe_url(url)


def test_redirect_cannot_download_zip_or_leave_official_https():
    with pytest.raises(review.ImportFailure):
        review.OfficialRedirects().redirect_request(None, None, 302, "Found", {}, URL)


class Response(io.BytesIO):
    status = 200
    url = URL + ".sha512"

    def __init__(self, body, headers=None):
        super().__init__(body)
        self.headers = headers or {}


@pytest.mark.parametrize("headers", [{}, {"Content-Length": "5000"}])
def test_fetch_enforces_metadata_size_cap(monkeypatch, headers):
    class Opener:
        def open(self, request, timeout):
            return Response(b"x" * 5000, headers)

    monkeypatch.setattr(review.urllib.request, "build_opener", lambda *a: Opener())
    monkeypatch.setattr(review.time, "sleep", lambda seconds: None)
    record, body = review.fetch_small(URL + ".sha512")
    assert record["http_status"] is None
    assert "limite" in record["error"]
    assert len(body) <= review.CHECKSUM_LIMIT + 1


def test_network_retries_are_bounded_and_keep_each_attempt(monkeypatch):
    calls = []

    class Opener:
        def open(self, request, timeout):
            calls.append(timeout)
            raise urllib.error.URLError("synthetic timeout")

    monkeypatch.setattr(review.urllib.request, "build_opener", lambda *a: Opener())
    monkeypatch.setattr(review.time, "sleep", lambda seconds: None)
    record, _ = review.fetch_small(URL + ".sha512", timeout=7)
    assert calls == [7, 7]
    assert len(record["attempts"]) == 2


def test_collector_preserves_manifest_and_reports_incomplete_evidence(source, tmp_path):
    item, root = source
    manifest = tmp_path / "manifest.json"
    raw = json.dumps(
        {"release_id": "synthetic", "sources": {"source_root": str(root), "files": [item]}}
    ).encode()
    manifest.write_bytes(raw)

    def fetch(url, **kw):
        if "package_show" in url:
            return {"http_status": 200}, json.dumps(
                {"success": True, "result": {"resources": [resource()]}}
            ).encode()
        return {"http_status": 404}, b"not found"

    # Two packages can duplicate entries; same-URL aliases are preserved explicitly.
    report = review.collect(manifest, fetch=fetch)
    assert report["summary"]["no_usable_reference"] == 1
    assert report["summary"]["new_operator_declarations"] == 0
    assert report["release_files_changed"] is report["operator_trust_changed"] is False
    assert manifest.read_bytes() == raw
    with pytest.raises(review.ImportFailure):
        review.collect(manifest, workers=5, fetch=fetch)

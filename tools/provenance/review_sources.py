"""Collect small official references without opening ZIPs or changing trust/release state."""

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "pipelines"))
from tse_importer.domain import ImportFailure  # noqa: E402
from tse_importer.integrity import checksum_line, fingerprint  # noqa: E402

HOSTS = {"dadosabertos.tse.jus.br", "cdn.tse.jus.br"}
PACKAGES = ("resultados-2026", "resultados-2026-boletim-de-urna")
CHECKSUM_LIMIT = 4096
CATALOG_LIMIT = 2 * 1024 * 1024


def now():
    return datetime.now(UTC).isoformat()


def safe_url(url):
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in HOSTS
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
        or urllib.parse.unquote(parsed.path).lower().endswith(".zip")
    ):
        raise ImportFailure("Somente metadados/checksums HTTPS oficiais; ZIPs não são baixados")
    return url


class OfficialRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        safe_url(newurl)
        return super().redirect_request(request, fp, code, message, headers, newurl)


def fetch_small(url, *, limit=CHECKSUM_LIMIT, timeout=15, cache_dir=None):
    safe_url(url)
    attempts = []
    body = b""
    result = {"requested_url": url, "tls_verification": "platform_default_trust_store"}
    for attempt in range(2):
        body = b""
        item = {"started_at": now()}
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "VotoAberto-Provenance-Review/1 (small metadata only)",
                    "Accept": "application/json,text/plain,*/*;q=0.1",
                },
            )
            with urllib.request.build_opener(OfficialRedirects()).open(
                request, timeout=timeout
            ) as response:
                length = response.headers.get("Content-Length")
                if length is not None and int(length) > limit:
                    raise ImportFailure("Resposta maior que o limite de metadados")
                body = response.read(limit + 1)
                if len(body) > limit:
                    raise ImportFailure("Resposta maior que o limite de metadados")
                item.update(
                    http_status=response.status,
                    final_url=response.url,
                    headers={
                        key: response.headers[key]
                        for key in (
                            "Date",
                            "Last-Modified",
                            "ETag",
                            "Content-Type",
                            "Content-Length",
                        )
                        if key in response.headers
                    },
                )
        except urllib.error.HTTPError as error:
            item.update(http_status=error.code, final_url=error.url, error=str(error))
            body = error.read(min(limit, 4096))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, ImportFailure) as error:
            item.update(http_status=None, error=str(error))
        item["finished_at"] = now()
        attempts.append(item)
        status = item["http_status"]
        if status is not None and status != 429 and status < 500:
            break
        if attempt == 0:
            time.sleep(0.5)
    result.update(
        attempts=attempts,
        **attempts[-1],
        body_bytes=len(body),
        body_sha256=hashlib.sha256(body).hexdigest(),
    )
    if cache_dir:
        cache_dir = Path(cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        # Content-addressed metadata snapshots, never the electoral archives.
        target = cache_dir / (result["body_sha256"] + ".response")
        if not target.exists():
            target.write_bytes(body)
    return result, body


def get_catalog(package, fetch=fetch_small):
    url = "https://dadosabertos.tse.jus.br/api/3/action/package_show?id=" + package
    request, body = fetch(url, limit=CATALOG_LIMIT)
    if request.get("http_status") != 200:
        raise ImportFailure("Catálogo oficial indisponível: " + url)
    payload = json.loads(body)
    if payload.get("success") is not True:
        raise ImportFailure("Resposta CKAN sem sucesso")
    data = payload["result"]
    summary = {
        "package": package,
        "request": request,
        "catalog_url": "https://dadosabertos.tse.jus.br/dataset/" + package,
        "title": data.get("title"),
        "organization": data.get("organization", {}).get("title"),
        "license_id": data.get("license_id"),
        "license_title": data.get("license_title"),
        "license_url": data.get("license_url"),
        "notes": data.get("notes"),
        "metadata_modified": data.get("metadata_modified"),
        "resource_count": len(data["resources"]),
    }
    return summary, data["resources"]


def resource_for(resources, name):
    matching = [
        item
        for item in resources
        if urllib.parse.unquote(urllib.parse.urlsplit(item.get("url", "")).path).split("/")[-1]
        == name
    ]
    if len({item["url"] for item in matching}) > 1:
        raise ImportFailure("Recurso duplicado/ambíguo no catálogo: " + name)
    if not matching:
        return None
    item = matching[0]
    result = {
        key: item.get(key)
        for key in (
            "id",
            "name",
            "url",
            "hash",
            "format",
            "last_modified",
            "created",
            "description",
        )
    }
    if len(matching) > 1:
        result["catalog_aliases"] = [
            {key: entry.get(key) for key in ("id", "name", "url", "format")} for entry in matching
        ]
    return result


def review_source(item, resources, source_root, fetch=fetch_small):
    resource = resource_for(resources, item["name"])
    expected_fingerprint = item.get("fingerprint")
    local = Path(source_root) / item["path"]
    try:
        stat = list(fingerprint(local))
        unchanged = stat == expected_fingerprint
    except OSError:
        stat, unchanged = None, False
    prior = item.get("verification", {})
    result = {
        "path": item["path"],
        "name": item["name"],
        "bytes": item["bytes"],
        "retained_hashes": item["hashes"],
        "original_hash_calculation": item.get("hash_calculation"),
        "local_byte_hash_recomputed": False,
        "local_fingerprint_matches_manifest": unchanged,
        "current_fingerprint": stat,
        "prior_verification": prior,
        "resource": resource,
        "official_reference_in_catalog": False,
        "reference_requests": [],
        "digest_comparison": "not_compared",
        "operator_confirmation": "pending",
        "previous_operator_trust": prior.get("reference", {}).get("trusted") is True,
        "origin_authentication": "not_performed",
        "signature_verification": "not_performed",
    }
    checksum_resource = resource_for(resources, item["name"] + ".sha512")
    if not resource and not checksum_resource:
        result["reference_state"] = "source_resource_not_found_in_current_catalog"
        return result
    # Some catalogs mistakenly point the ZIP entry at its checksum. Preserve the
    # missing ZIP binding and both aliases; the checksum still names the exact file.
    source_url = resource["url"] if resource else checksum_resource["url"].removesuffix(".sha512")
    result["source_url"] = source_url
    result["source_url_evidence"] = (
        "catalog_resource" if resource else "inferred_from_catalog_checksum_url_not_zip_fetch"
    )
    for algorithm in ("sha512", "sha256"):
        reference = resource_for(resources, item["name"] + "." + algorithm)
        url = reference["url"] if reference else source_url + "." + algorithm
        # An HTTP link in CKAN is explicitly upgraded to HTTPS, never downgraded.
        url = urllib.parse.urlsplit(url)._replace(scheme="https").geturl()
        request, body = fetch(url)
        request["algorithm"] = algorithm
        request["catalog_resource"] = reference
        result["reference_requests"].append(request)
        if request.get("http_status") != 200:
            continue
        try:
            digest = checksum_line(
                body.decode("ascii").replace("\r\n", "\n"), item["name"], algorithm
            )
        except (ImportFailure, UnicodeError) as error:
            request["parse_error"] = str(error)
            continue
        request["checksum_text"] = body.decode("ascii")
        result.update(
            reference_state="fetched_official_https_reference",
            official_reference_in_catalog=reference is not None,
            digest_comparison="match" if item["hashes"][algorithm] == digest else "mismatch",
            # A proposal is never an operator declaration. The evaluator stays unchanged.
            proposed_reference={
                "algorithm": algorithm,
                "digest": digest,
                "origin": url,
                "trusted": False,
            },
            confidence_proposal=(
                "official_https_reference_matches_retained_digest_pending_operator_and_byte_refresh"
                if unchanged and item["hashes"][algorithm] == digest
                else "blocked_local_file_changed_or_digest_mismatch"
            ),
        )
        return result
    result["reference_state"] = "no_usable_reference_at_tested_endpoints"
    return result


def collect(manifest_path, *, workers=3, fetch=fetch_small):
    if not 1 <= workers <= 4:
        raise ImportFailure("Paralelismo permitido: 1 a 4")
    manifest_path = Path(manifest_path)
    manifest_bytes = manifest_path.read_bytes()
    manifest = json.loads(manifest_bytes)
    catalogs, resources = [], []
    for package in PACKAGES:
        catalog, entries = get_catalog(package, fetch)
        catalogs.append(catalog)
        resources.extend(entries)
    sources = [item for item in manifest["sources"]["files"] if item["name"].endswith(".zip")]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        records = list(
            pool.map(
                lambda item: review_source(
                    item, resources, manifest["sources"]["source_root"], fetch
                ),
                sources,
            )
        )
    return {
        "review_version": 1,
        "captured_at": now(),
        "national_release_id": manifest["release_id"],
        "national_manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "method": "Fresh official HTTPS reference compared with retained local digest; ZIP bytes not reread",
        "operator_trust_changed": False,
        "release_files_changed": False,
        "catalogs": catalogs,
        "sources": records,
        "summary": {
            "source_count": len(records),
            "zip_bytes": sum(item["bytes"] for item in sources),
            "fresh_reference_matches": sum(r["digest_comparison"] == "match" for r in records),
            "digest_mismatches": sum(r["digest_comparison"] == "mismatch" for r in records),
            "no_usable_reference": sum(r["digest_comparison"] == "not_compared" for r in records),
            "local_fingerprints_unchanged": sum(
                r["local_fingerprint_matches_manifest"] for r in records
            ),
            "previous_operator_trusted": sum(r["previous_operator_trust"] for r in records),
            "new_operator_declarations": 0,
            "zip_downloads": 0,
            "zip_byte_hashes_recomputed": 0,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--http-cache", type=Path)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args(argv)
    if args.report.exists():
        parser.error("O relatório já existe; escolha um novo caminho para preservar evidências")
    try:
        result = collect(
            args.manifest,
            workers=args.workers,
            fetch=lambda url, **kw: fetch_small(url, cache_dir=args.http_cache, **kw),
        )
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
        )
        print(json.dumps(result["summary"], ensure_ascii=False))
        return 1 if result["summary"]["digest_mismatches"] else 0
    except (ImportFailure, OSError, KeyError, ValueError) as error:
        print("Revisão interrompida: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

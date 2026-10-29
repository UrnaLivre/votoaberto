"""Hashes are byte comparisons, never digital signatures."""

import hashlib
import re
from pathlib import Path

from .domain import ImportFailure


def fingerprint(path: Path) -> tuple[int, int, int, int]:
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns, stat.st_dev, stat.st_ino


def hashes(path: Path) -> dict[str, str]:
    before = fingerprint(path)
    digests = {name: hashlib.new(name) for name in ("sha256", "sha512")}
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            for digest in digests.values():
                digest.update(chunk)
    if fingerprint(path) != before:
        raise ImportFailure(f"Arquivo alterado durante cálculo de hash: {path.name}")
    return {name: digest.hexdigest() for name, digest in digests.items()}


def checksum_line(text: str, filename: str, algorithm: str) -> str:
    if algorithm not in ("sha256", "sha512"):
        raise ImportFailure("Algoritmo de referência não suportado")
    length = hashlib.new(algorithm).digest_size * 2
    match = re.fullmatch(rf"([0-9a-fA-F]{{{length}}}) [ *](.+)\n?", text)
    if not match or match[2] != filename:
        raise ImportFailure("Checksum não suportado ou nome de arquivo divergente (formato GNU)")
    return match[1].lower()


def verify(path: Path, calculated: dict, reference: dict | None = None) -> dict:
    result = _verify(path, calculated, reference)
    result.update(
        digest_comparison="match"
        if result.get("matches") is True
        else "mismatch"
        if result.get("matches") is False
        else "not_compared",
        reference_trust="operator_declared"
        if result.get("reference", {}).get("trusted") is True
        else "not_assigned",
        origin_authentication="not_performed",
        signature_verification="not_performed",
        status_scope="digest_comparison_under_operator_assigned_trust",
    )
    return result


def _verify(path: Path, calculated: dict, reference: dict | None = None) -> dict:
    if reference:
        required = {"algorithm", "digest", "origin", "trusted"}
        if set(reference) != required or reference.get("algorithm") not in calculated:
            return {"status": "unsupported", "reference": reference}
        algorithm = reference["algorithm"]
        expected = reference["digest"]
        if (
            not isinstance(expected, str)
            or not re.fullmatch(rf"[a-fA-F0-9]{{{len(calculated[algorithm])}}}", expected)
            or not isinstance(reference["origin"], str)
            or type(reference["trusted"]) is not bool
        ):
            raise ImportFailure("Referência inválida: digest, origin ou trusted")
        matches = calculated[algorithm] == expected.lower()
        return {
            "status": ("verified" if reference["trusted"] else "unverified")
            if matches
            else "mismatch",
            "matches": matches,
            "reference": reference,
        }
    sidecar = Path(str(path) + ".sha512")
    if sidecar.exists():
        if sidecar.stat().st_size > 4096:
            return {"status": "unsupported", "reason": "Checksum maior que 4096 bytes"}
        try:
            expected = checksum_line(sidecar.read_text(encoding="ascii"), path.name, "sha512")
        except (ImportFailure, UnicodeError) as exc:
            return {"status": "unsupported", "reason": str(exc)}
        matches = expected == calculated["sha512"]
        return {
            "status": "unverified" if matches else "mismatch",
            "matches": matches,
            "reference": {
                "algorithm": "sha512",
                "digest": expected,
                "origin": sidecar.name,
                "trusted": False,
            },
            "reason": "Auxiliar local; confiança na origem não configurada",
        }
    return {"status": "unverified", "reason": "Sem referência suficiente"}

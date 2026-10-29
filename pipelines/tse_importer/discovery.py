"""Inventory and bounded ZIP streams; never extracts filesystem members."""

import io
import re
import stat
import struct
import zipfile
from collections import Counter
from contextlib import contextmanager
from pathlib import Path, PurePosixPath

from .domain import ImportFailure, Limits
from .integrity import fingerprint, hashes, verify


def member_issues(info: zipfile.ZipInfo, limits: Limits) -> list[str]:
    name = info.filename.replace("\\", "/")
    issues = []
    if (
        name.startswith("/")
        or re.match(r"^[a-zA-Z]:", name)
        or ".." in PurePosixPath(name).parts
        or ":" in name
    ):
        issues.append("unsafe_path")
    if stat.S_ISLNK(info.external_attr >> 16):
        issues.append("symlink")
    if info.flag_bits & 1:
        issues.append("encrypted")
    if info.file_size > limits.max_member_bytes:
        issues.append("member_size_limit")
    if info.file_size / max(1, info.compress_size) > limits.max_ratio:
        issues.append("compression_ratio_limit")
    suffix = PurePosixPath(name).suffix.lower()
    if suffix in (".zip", ".7z", ".gz", ".tar", ".rar"):
        issues.append("nested_archive")
    return issues


def preflight_index(path: Path, limits: Limits) -> None:
    """Bound central-directory allocation before ZipFile reads it, including ZIP64."""
    with path.open("rb") as stream:
        size = path.stat().st_size
        stream.seek(max(0, size - 65557))
        tail = stream.read(65557)
        offset = tail.rfind(b"PK\x05\x06")
        if offset < 0 or len(tail) - offset < 22:
            raise ImportFailure("ZIP sem índice final válido")
        _, disk, central_disk, disk_count, count, index_bytes, _, comment = struct.unpack_from(
            "<4s4H2LH", tail, offset
        )
        if disk or central_disk or disk_count != count or offset + 22 + comment != len(tail):
            raise ImportFailure("ZIP multipartes/trailer não suportado")
        if count == 65535 or index_bytes == 0xFFFFFFFF:
            eocd_offset = size - len(tail) + offset
            stream.seek(max(0, eocd_offset - 20))
            locator = stream.read(20)
            if len(locator) != 20:
                raise ImportFailure("Localizador ZIP64 inválido")
            magic, disk, record_offset, disks = struct.unpack("<4sLQL", locator)
            if magic != b"PK\x06\x07" or disk or disks != 1 or record_offset > size - 56:
                raise ImportFailure("ZIP64 multipartes/inválido")
            stream.seek(record_offset)
            record = stream.read(56)
            if len(record) != 56:
                raise ImportFailure("Registro ZIP64 incompleto")
            magic, record_size, _, _, disk, central_disk, disk_count, count, index_bytes, _ = (
                struct.unpack("<4sQ2H2L4Q", record)
            )
            if (
                magic != b"PK\x06\x06"
                or record_size < 44
                or disk
                or central_disk
                or disk_count != count
            ):
                raise ImportFailure("Índice ZIP64 inválido")
        if count > limits.max_members or index_bytes > limits.max_index_bytes:
            raise ImportFailure("Índice ZIP excede limites de membros/bytes")


def zip_index(path: Path, limits: Limits) -> dict:
    preflight_index(path, limits)
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        if len(entries) > limits.max_members:
            raise ImportFailure(f"ZIP excede {limits.max_members} membros")
        names = Counter(m.filename for m in entries)
        members = []
        for info in entries:
            issues = member_issues(info, limits)
            if names[info.filename] > 1:
                issues.append("duplicate_member")
            members.append(
                {
                    "name": info.filename,
                    "bytes": info.file_size,
                    "compressed_bytes": info.compress_size,
                    "crc32": f"{info.CRC:08x}",
                    "directory": info.is_dir(),
                    "issues": issues,
                    "extension": PurePosixPath(info.filename).suffix.lower(),
                }
            )
        total = sum(m.file_size for m in entries)
        return {
            "members": members,
            "member_count": len(entries),
            "declared_bytes": total,
            "compressed_bytes": sum(m.compress_size for m in entries),
            "issues": ["total_size_limit"] if total > limits.max_total_bytes else [],
        }


def inventory(root: Path, limits: Limits = Limits(), references: dict | None = None) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise ImportFailure(f"Diretório de entrada inexistente: {root}")
    files = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in (".zip", ".sha256", ".sha512"):
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ImportFailure("Links para fontes não são aceitos")
        relative = path.relative_to(root).as_posix()
        item = {"path": relative, "name": path.name, "bytes": path.stat().st_size}
        before = fingerprint(path)
        try:
            item["hashes"] = hashes(path)
            if path.suffix.lower() == ".zip":
                item.update(zip_index(path, limits))
                item["verification"] = verify(
                    path, item["hashes"], (references or {}).get(relative)
                )
                item["status"] = (
                    "unsafe"
                    if item["issues"] or any(m["issues"] for m in item["members"])
                    else "ok"
                )
            else:
                item["status"] = "auxiliary"
            if fingerprint(path) != before:
                raise ImportFailure("Fonte mudou durante inventário")
        except (OSError, ValueError, zipfile.BadZipFile, NotImplementedError) as exc:
            item.update(status="error", error=str(exc))
        files.append(item)
    unknown = set(references or {}) - {
        item["path"] for item in files if item["name"].lower().endswith(".zip")
    }
    if unknown:
        raise ImportFailure(f"Referências sem fonte correspondente: {sorted(unknown)}")
    return {"inventory_version": 1, "files": files}


class BoundedReader(io.RawIOBase):
    def __init__(self, stream, limit: int):
        self.stream, self.limit, self.count = stream, limit, 0

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        chunk = self.stream.read(min(len(buffer), max(1, self.limit - self.count + 1)))
        self.count += len(chunk)
        if self.count > self.limit:
            raise ImportFailure("Limite real de bytes descompactados excedido")
        buffer[: len(chunk)] = chunk
        return len(chunk)


@contextmanager
def member_stream(path: Path, member: str, limits: Limits):
    index = zip_index(path, limits)
    if index["issues"] or any(m["issues"] for m in index["members"]):
        raise ImportFailure(f"ZIP inseguro: {path.name}")
    with zipfile.ZipFile(path) as archive, archive.open(member) as raw:
        with io.BufferedReader(BoundedReader(raw, limits.max_member_bytes)) as stream:
            yield stream


def drain(stream, limits: Limits) -> int:
    """Read to EOF, forcing ZIP CRC checking even for unparsed members."""
    count = 0
    while chunk := stream.read(1024 * 1024):
        count += len(chunk)
        if count > limits.max_member_bytes:
            raise ImportFailure("Limite de bytes excedido")
    return count

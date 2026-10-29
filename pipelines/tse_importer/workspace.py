"""Process-local disk accounting and conservative cleanup of owned run files.

This is a sampled guard with growth reservations, not an operating-system quota.
Unknown/replaced files are counted but never removed. No source path is accepted here.
"""

import json
import os
import shutil
import stat
import threading
import time
import uuid
from contextvars import ContextVar
from dataclasses import asdict
from pathlib import Path

from .domain import ImportFailure, StoragePolicy

ACTIVE_WORK = ContextVar("tse_active_workspace", default=None)
TEMP_LOCK = threading.Lock()


def no_links(path: Path) -> None:
    for item in (path, *path.parents):
        if item.exists() or item.is_symlink():
            info = item.lstat()
            if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
                raise ImportFailure(f"Link/reparse point recusado na área de trabalho: {item}")


def entry_info(path):
    """During a read-only scan, ancestors were checked when entering the area."""
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
        raise ImportFailure(f"Link/reparse point recusado na área de trabalho: {path}")
    return info


class WorkRun:
    def __init__(self, output: Path, policy: StoragePolicy):
        no_links(output)
        self.output, self.policy = output.resolve(), policy
        self.run_id = uuid.uuid4().hex
        self.root = self.output / policy.work_directory / self.run_id
        self.ledger = self.output / ".runs" / (self.run_id + ".json")
        self.owned = {}
        self.completed_checkpoints = set()
        self.companions = set()
        self.removed = []
        self.refused = []
        self.connections = []
        self.failure = None
        self.stop = threading.Event()
        self.mutex = threading.RLock()
        self.start_free = shutil.disk_usage(self.output).free
        self.minimum_free = self.start_free
        self.peak_bytes = self.peak_work_bytes = self.peak_journal_bytes = 0
        self.peak_visible_bytes = 0
        self.file_peaks = {}
        self.safety_margin = min(64 * 1024**2, policy.max_work_disk_bytes // 32)
        self.checkpoint_key = None
        self.start = time.perf_counter()
        self.promoted = None
        self.published = False
        self.last_check = 0.0
        self.check()
        self.check(policy.projected_peak_bytes)
        for directory in (self.root, self.ledger.parent, self.root / "tmp"):
            no_links(directory)
            directory.mkdir(parents=True, exist_ok=True)
        self.file(self.ledger)
        self.save("running")

    def file(self, path: Path) -> Path:
        """Reserve a new exact file with exclusive creation, recording its identity."""
        if not path.is_absolute():
            path = self.root / path
        self.allowed(path)
        no_links(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb"):
            pass
        info = path.stat()
        self.owned[str(path)] = (info.st_dev, info.st_ino)
        self.check()
        if path != self.ledger:
            self.save("running")
        return path

    def allowed(self, path):
        # The only outside files permitted are this run's ledger and promoted release.
        if not (
            path.is_relative_to(self.root)
            or path == self.ledger
            or (self.promoted and path.is_relative_to(self.promoted))
        ):
            raise ImportFailure("Artefato fora da área pertencente à execução")

    def database(self, path, db):
        self.allowed(path)
        for suffix in ("-journal", "-wal", "-shm"):
            companion = Path(str(path) + suffix)
            if companion.exists():
                raise ImportFailure("Journal preexistente inesperado")
            self.companions.add(str(companion))
        self.connections.append(db)
        db.set_progress_handler(self.sql_progress, 20000)

    def sql_progress(self):
        try:
            self.check()
        except ImportFailure as exc:
            self.failure = exc
        return int(self.failure is not None)

    def scan(self):
        total = work = journals = 0
        areas = [self.root] + ([self.promoted] if self.promoted else [])
        for area in areas:
            if not area.exists():
                continue
            no_links(area)
            for parent, dirs, files in os.walk(area, followlinks=False):
                for name in dirs:
                    entry_info(Path(parent) / name)
                for name in files:
                    path = Path(parent) / name
                    try:
                        info = entry_info(path)
                    except FileNotFoundError:  # SQLite deletes journals between samples.
                        continue
                    total += info.st_size
                    self.file_peaks[str(path)] = max(
                        self.file_peaks.get(str(path), 0), info.st_size
                    )
                    if path.is_relative_to(self.root):
                        work += info.st_size
                    if str(path) in self.companions:
                        journals += info.st_size
                        self.owned.setdefault(str(path), (info.st_dev, info.st_ino))
        if self.ledger.exists():
            total += self.ledger.stat().st_size
        return total, work, journals

    def check(self, reserve=0):
        with self.mutex:
            if self.failure:
                raise self.failure
            now = time.monotonic()
            if not reserve and now - self.last_check < 0.08:
                return
            total, work, journals = self.scan()
            free = shutil.disk_usage(self.output).free
            # Conservatively include unlinked SQLite temps and unexplained volume loss.
            accounted = max(total, self.start_free - free)
            self.minimum_free = min(self.minimum_free, free)
            self.peak_bytes = max(self.peak_bytes, accounted)
            self.peak_visible_bytes = max(self.peak_visible_bytes, total)
            self.peak_work_bytes = max(self.peak_work_bytes, work)
            self.peak_journal_bytes = max(self.peak_journal_bytes, journals)
            self.last_check = now
            if accounted + reserve + self.safety_margin > self.policy.max_work_disk_bytes:
                raise ImportFailure(
                    "Orçamento max_work_disk_bytes insuficiente; carga interrompida"
                )
            if free - reserve - self.safety_margin < self.policy.min_free_disk_bytes:
                raise ImportFailure("Reserva min_free_disk_bytes seria violada; carga interrompida")

    def reserve_batch(self):
        self.check(min(4 * 1024**2, self.policy.max_work_disk_bytes // 16))

    def monitor(self):
        while not self.stop.wait(0.1):
            try:
                self.check()
            except (ImportFailure, OSError) as exc:
                self.failure = ImportFailure(str(exc))
                # SQLite progress handlers interrupt long queries at their next callback.
                return

    def metrics(self):
        accounting_error = None
        try:
            total, work, _ = self.scan()
        except (ImportFailure, OSError) as exc:
            total = work = None
            accounting_error = str(exc)
        return {
            "run_id": self.run_id,
            "policy": asdict(self.policy),
            "free_before_bytes": self.start_free,
            "minimum_free_bytes": self.minimum_free,
            "peak_accounted_bytes": self.peak_bytes,
            "peak_visible_file_bytes": self.peak_visible_bytes,
            "growth_safety_margin_bytes": self.safety_margin,
            "peak_work_bytes": self.peak_work_bytes,
            "peak_journal_bytes": self.peak_journal_bytes,
            "remaining_owned_bytes": total,
            "remaining_work_bytes": work,
            "removed_files": len(self.removed),
            "recovered_logical_bytes": sum(x["bytes"] for x in self.removed),
            "cleanup_refused": self.refused,
            "accounting_error": accounting_error,
            "file_high_water_bytes": dict(self.file_peaks),
            "sqlite_temporary_files_observed": sum(
                Path(name).parent == self.root / "tmp" and Path(name).name.startswith("etilqs_")
                for name in self.file_peaks
            ),
            "sqlite_temporaries_no_longer_present": sum(
                Path(name).parent == self.root / "tmp"
                and Path(name).name.startswith("etilqs_")
                and not Path(name).exists()
                for name in self.file_peaks
            ),
            "measurement": "logical file lengths + conservative volume free-space delta; 100ms sampling and SQL/batch checks; not an OS quota",
        }

    def save(self, status, error=None):
        no_links(self.ledger)
        info = self.ledger.stat()
        if self.owned.get(str(self.ledger)) != (info.st_dev, info.st_ino):
            raise ImportFailure("Registro de propriedade foi substituído; escrita recusada")
        data = {
            "ownership_version": 1,
            "run_id": self.run_id,
            "status": status,
            "checkpoint_key": self.checkpoint_key,
            "error": error,
            "root": str(self.root),
            "metrics": self.metrics(),
            "created": [{"path": p, "identity": list(i)} for p, i in self.owned.items()],
            "removed": self.removed,
            "completed_checkpoints": sorted(self.completed_checkpoints),
        }
        self.ledger.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf8"
        )

    def remove(self, path):
        with self.mutex:
            self.allowed(path)
            key = str(path)
            if not path.exists() and not path.is_symlink():
                return
            try:
                no_links(path)
                info = path.stat()
                if self.owned.get(key) != (info.st_dev, info.st_ino):
                    raise ImportFailure("Identidade/propriedade não confirmada")
                path.unlink()
                self.removed.append({"path": key, "bytes": info.st_size})
                self.owned.pop(key, None)
            except (ImportFailure, OSError) as exc:
                self.refused.append({"path": key, "reason": str(exc)})

    def promoted_to(self, stage, release):
        with self.mutex:
            self.promoted = release
            for old in list(self.owned):
                path = Path(old)
                if path.is_relative_to(stage):
                    new = release / path.relative_to(stage)
                    self.owned[str(new)] = self.owned.pop(old)

    def demoted_to(self, release, stage):
        with self.mutex:
            for old in list(self.owned):
                path = Path(old)
                if path.is_relative_to(release):
                    self.owned[str(stage / path.relative_to(release))] = self.owned.pop(old)
            self.promoted = None

    def __enter__(self):
        TEMP_LOCK.acquire()
        self.previous_env = {key: os.environ.get(key) for key in ("TMP", "TEMP", "SQLITE_TMPDIR")}
        for key in self.previous_env:
            os.environ[key] = str(self.root / "tmp")
        self.token = ACTIVE_WORK.set(self)
        self.thread = threading.Thread(target=self.monitor, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, kind, error, traceback):
        self.stop.set()
        self.thread.join()
        ACTIVE_WORK.reset(self.token)
        for key, value in self.previous_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        TEMP_LOCK.release()
        # All SQLite connections are closed by their owning scopes before cleanup.
        if self.policy.cleanup_policy == "owned":
            for name in list(self.owned):
                path = Path(name)
                if path == self.ledger or (
                    self.published and self.promoted and path.is_relative_to(self.promoted)
                ):
                    continue
                if self.policy.retain_checkpoints and str(path) in self.completed_checkpoints:
                    continue
                if (
                    kind
                    and self.policy.retain_failed_diagnostics
                    and path.suffix in (".json", ".jsonl")
                    and not path.is_relative_to(self.root / "checkpoints")
                ):
                    continue
                self.remove(path)
            # Empty known run directories only; rmdir never recursively deletes files.
            try:
                no_links(self.root)
                walk = os.walk(self.root, topdown=False, followlinks=False)
            except ImportFailure as exc:
                self.refused.append({"path": str(self.root), "reason": str(exc)})
                walk = ()
            for parent, dirs, _files in walk:
                for name in dirs:
                    path = Path(parent) / name
                    try:
                        no_links(path)
                        path.rmdir()
                    except (OSError, ImportFailure):
                        pass
            try:
                self.root.rmdir()
            except OSError:
                pass
        self.save(
            "cancelled" if kind is KeyboardInterrupt else "failed" if kind else "succeeded",
            str(error)[:4096] if error else None,
        )
        return False

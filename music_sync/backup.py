from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import shutil

MANIFEST_NAME = ".music-sync-backup.json"


class BackupVerificationError(RuntimeError):
    """Raised when a backup does not exactly match the source snapshot."""


@dataclass(frozen=True, slots=True)
class BackupInfo:
    path: Path
    backup_id: str
    file_count: int
    size_bytes: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _manifest_for(root: Path) -> dict[str, dict[str, int | str]]:
    manifest: dict[str, dict[str, int | str]] = {}
    for path in root.rglob("*"):
        if not path.is_file() or path.name == MANIFEST_NAME:
            continue
        stat = path.stat()
        relative = str(path.relative_to(root))
        manifest[relative] = {
            "size": stat.st_size,
            "modified_ns": stat.st_mtime_ns,
            "sha256": _sha256(path),
        }
    return manifest


def _write_manifest(root: Path, backup_id: str, entries: dict[str, dict[str, int | str]]) -> None:
    payload = {
        "format": 1,
        "backup_id": backup_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "files": entries,
    }
    (root / MANIFEST_NAME).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def verify_backup(source: Path, backup: Path) -> BackupInfo:
    """Verify a backup against the source using file sets, sizes, mtimes, and SHA-256."""
    source = source.resolve()
    backup = backup.resolve()
    manifest_path = backup / MANIFEST_NAME
    if not manifest_path.is_file():
        raise BackupVerificationError(f"Backup manifest is missing: {manifest_path}")

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries = payload["files"]
        backup_id = str(payload["backup_id"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise BackupVerificationError(f"Backup manifest is invalid: {manifest_path}") from exc

    source_entries = _manifest_for(source)
    backup_entries = _manifest_for(backup)
    if set(source_entries) != set(entries) or set(source_entries) != set(backup_entries):
        raise BackupVerificationError("Backup file set does not match the source snapshot.")

    for relative, expected in source_entries.items():
        actual = backup_entries[relative]
        if actual != expected or entries[relative] != expected:
            raise BackupVerificationError(f"Backup verification failed for {relative}.")

    return BackupInfo(backup, backup_id, len(source_entries), sum(int(item["size"]) for item in source_entries.values()))


def create_verified_backup(source: Path, backup_root: Path) -> BackupInfo:
    """Copy a library and verify the resulting backup before returning it."""
    source = source.resolve()
    backup_root = backup_root.resolve()
    if not source.is_dir():
        raise FileNotFoundError(f"Library not found: {source}")
    if source == backup_root or source.is_relative_to(backup_root) or backup_root.is_relative_to(source):
        raise ValueError("Backup location must be outside the source library.")

    backup_root.mkdir(parents=True, exist_ok=True)
    backup_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    destination = backup_root / f"music_backup_{backup_id}"
    shutil.copytree(source, destination)
    entries = _manifest_for(source)
    _write_manifest(destination, backup_id, entries)
    try:
        return verify_backup(source, destination)
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise

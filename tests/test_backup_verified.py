from pathlib import Path

import pytest

from harmelune.backup import BackupVerificationError, create_verified_backup, verify_backup
from harmelune.direction import MasterLibrary, SyncDirection
from harmelune.models import SyncPlan, Track
from harmelune.scanner import current_fingerprint
from harmelune.sync import execute_safe


def test_verified_backup_success_with_unicode_and_nested_files(tmp_path: Path):
    source = tmp_path / "Library – 夜"
    backup_root = tmp_path / "Backups"
    nested = source / "Artist" / "Album"
    nested.mkdir(parents=True)
    (nested / "Jóga.mp3").write_bytes(b"audio")
    (nested / "cover.bin").write_bytes(b"art")

    info = create_verified_backup(source, backup_root)

    assert info.file_count == 2
    assert info.size_bytes == len(b"audio") + len(b"art")
    assert info.backup_id
    assert verify_backup(source, info.path) == info


def test_empty_library_backup_is_verified(tmp_path: Path):
    source = tmp_path / "Empty"
    source.mkdir()
    info = create_verified_backup(source, tmp_path / "Backups")
    assert info.file_count == 0
    assert verify_backup(source, info.path) == info


def test_changed_backup_file_fails_verification(tmp_path: Path):
    source = tmp_path / "Library"
    source.mkdir()
    (source / "song.mp3").write_bytes(b"source")
    info = create_verified_backup(source, tmp_path / "Backups")
    (info.path / "song.mp3").write_bytes(b"changed")

    with pytest.raises(BackupVerificationError):
        verify_backup(source, info.path)


def test_missing_backup_file_fails_verification(tmp_path: Path):
    source = tmp_path / "Library"
    source.mkdir()
    (source / "song.mp3").write_bytes(b"source")
    info = create_verified_backup(source, tmp_path / "Backups")
    (info.path / "song.mp3").unlink()

    with pytest.raises(BackupVerificationError):
        verify_backup(source, info.path)


def test_extra_backup_file_fails_verification(tmp_path: Path):
    source = tmp_path / "Library"
    source.mkdir()
    (source / "song.mp3").write_bytes(b"source")
    info = create_verified_backup(source, tmp_path / "Backups")
    (info.path / "extra.tmp").write_bytes(b"extra")

    with pytest.raises(BackupVerificationError):
        verify_backup(source, info.path)


def test_backup_verification_failure_blocks_safe_execution(tmp_path: Path, monkeypatch):
    source = tmp_path / "A"
    destination = tmp_path / "B"
    backup_root = tmp_path / "Backups"
    source.mkdir()
    destination.mkdir()
    track = source / "new.mp3"
    track.write_bytes(b"new")

    plan = SyncPlan(
        library_a_only=[Track(track, "a")],
        library_a_root=source,
        library_b_root=destination,
        fingerprint_a=current_fingerprint(source),
        fingerprint_b=current_fingerprint(destination),
    )

    def fail_backup(*args, **kwargs):
        raise BackupVerificationError("simulated verification failure")

    monkeypatch.setattr("harmelune.sync.create_verified_backup", fail_backup)
    with pytest.raises(BackupVerificationError):
        execute_safe(plan, SyncDirection(source, destination, MasterLibrary.LIBRARY_A), backup_root)

    assert not (destination / "new.mp3").exists()

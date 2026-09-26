from pathlib import Path

import pytest

from harmelune.backup import (
    RestoreConfirmationError,
    create_verified_backup,
    restore_verified_backup,
)


def test_restore_requires_exact_confirmation(tmp_path: Path):
    source = tmp_path / "Source"
    source.mkdir()
    (source / "song.mp3").write_bytes(b"song")
    backup = create_verified_backup(source, tmp_path / "Backups").path
    target = tmp_path / "Target"
    target.mkdir()

    with pytest.raises(RestoreConfirmationError, match="RESTORE"):
        restore_verified_backup(backup, target, tmp_path / "Safety", "yes")
    assert not any(target.iterdir())


def test_successful_restore_is_verified_and_unicode_safe(tmp_path: Path):
    source = tmp_path / "Source"
    source.mkdir()
    (source / "Artist – 夜" / "曲.mp3").parent.mkdir(parents=True)
    (source / "Artist – 夜" / "曲.mp3").write_bytes(b"source")
    backup = create_verified_backup(source, tmp_path / "Backups").path
    target = tmp_path / "Target"
    target.mkdir()
    (target / "old.mp3").write_bytes(b"old")

    result = restore_verified_backup(backup, target, tmp_path / "Safety", "RESTORE")

    assert result.restored is True
    assert result.recovered is True
    assert (target / "Artist – 夜" / "曲.mp3").read_bytes() == b"source"
    assert not (target / "old.mp3").exists()
    assert result.safety_backup is not None and result.safety_backup.is_dir()


def test_corrupt_backup_is_rejected_before_target_change(tmp_path: Path):
    source = tmp_path / "Source"
    source.mkdir()
    (source / "song.mp3").write_bytes(b"song")
    backup = create_verified_backup(source, tmp_path / "Backups").path
    (backup / "song.mp3").write_bytes(b"corrupt")
    target = tmp_path / "Target"
    target.mkdir()
    (target / "keep.mp3").write_bytes(b"keep")

    with pytest.raises(Exception):
        restore_verified_backup(backup, target, tmp_path / "Safety", "RESTORE")
    assert (target / "keep.mp3").read_bytes() == b"keep"
    assert not (tmp_path / "Safety").exists()


def test_restore_failure_recovers_current_library(tmp_path: Path, monkeypatch):
    source = tmp_path / "Source"
    source.mkdir()
    (source / "new.mp3").write_bytes(b"new")
    backup = create_verified_backup(source, tmp_path / "Backups").path
    target = tmp_path / "Target"
    target.mkdir()
    (target / "current.mp3").write_bytes(b"current")

    import harmelune.backup as backup_module
    original_restore = backup_module._restore_directory
    calls = {"count": 0}

    def fail_first_restore(target_path, backup_path):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("simulated restore failure")
        return original_restore(target_path, backup_path)

    monkeypatch.setattr(backup_module, "_restore_directory", fail_first_restore)
    result = restore_verified_backup(backup, target, tmp_path / "Safety", "RESTORE")

    assert result.restored is False
    assert result.recovered is True
    assert (target / "current.mp3").read_bytes() == b"current"
    assert not (target / "new.mp3").exists()


def test_restore_recovery_failure_is_reported(tmp_path: Path, monkeypatch):
    source = tmp_path / "Source"
    source.mkdir()
    (source / "new.mp3").write_bytes(b"new")
    backup = create_verified_backup(source, tmp_path / "Backups").path
    target = tmp_path / "Target"
    target.mkdir()
    (target / "current.mp3").write_bytes(b"current")

    monkeypatch.setattr("harmelune.backup._restore_directory", lambda *_: (_ for _ in ()).throw(OSError("restore failed")))
    result = restore_verified_backup(backup, target, tmp_path / "Safety", "RESTORE")

    assert result.restored is False
    assert result.recovered is False
    assert result.error and "recovery failed" in result.error

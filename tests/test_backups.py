from pathlib import Path

from music_sync.backups import list_backups, restore_backup


def test_list_backups_reads_timestamped_directories(tmp_path: Path):
    root = tmp_path / "backups"
    root.mkdir()
    first = root / "music_backup_20260829_120000"
    second = root / "music_backup_20260830_120000"
    first.mkdir()
    second.mkdir()
    (second / "song.mp3").write_bytes(b"audio")
    backups = list_backups(root)
    assert [item.path for item in backups] == [second, first]
    assert backups[0].file_count == 1


def test_restore_protects_current_library(tmp_path: Path):
    root = tmp_path / "backups"
    root.mkdir()
    backup = root / "music_backup_20260830_120000"
    backup.mkdir()
    (backup / "restored.mp3").write_bytes(b"new")
    target = tmp_path / "library"
    target.mkdir()
    (target / "old.mp3").write_bytes(b"old")
    protection = restore_backup(backup, target, root)
    assert (target / "restored.mp3").read_bytes() == b"new"
    assert not (target / "old.mp3").exists()
    assert protection.is_dir()

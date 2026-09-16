from pathlib import Path

import pytest

from music_sync.first_run import FirstRunState, is_first_run
from music_sync.models import SyncMode
from music_sync.settings import Settings


def test_empty_settings_are_first_run():
    assert is_first_run(Settings()) is True


def test_configured_settings_are_not_first_run(tmp_path: Path):
    settings = Settings(
        library_a=str(tmp_path / "A"),
        library_b=str(tmp_path / "B"),
        master="library_b",
        sync_mode=SyncMode.RECONCILE,
        backup_location=str(tmp_path / "backup"),
    )
    assert is_first_run(settings) is False


def test_first_run_state_preserves_existing_preferences(tmp_path: Path):
    a = tmp_path / "音乐 A"
    b = tmp_path / "Library B with spaces"
    backup = tmp_path / "backup"
    a.mkdir()
    b.mkdir()
    existing = Settings(
        fuzzy_threshold=0.93,
        conflict_defaults={"artwork": "skip"},
        appearance="dark",
    )
    state = FirstRunState(
        library_a=str(a),
        library_b=str(b),
        master="library_b",
        sync_mode=SyncMode.MIRROR,
        backup_location=str(backup),
    )
    result = state.to_settings(existing)
    assert result.library_a == str(a)
    assert result.library_b == str(b)
    assert result.master == "library_b"
    assert result.sync_mode == SyncMode.MIRROR
    assert result.backup_location == str(backup)
    assert result.fuzzy_threshold == 0.93
    assert result.conflict_defaults == {"artwork": "skip"}
    assert result.appearance == "dark"
    assert not backup.exists()


def test_first_run_rejects_identical_libraries(tmp_path: Path):
    library = tmp_path / "Library"
    library.mkdir()
    state = FirstRunState(library_a=str(library), library_b=str(library), backup_location=str(tmp_path / "backup"))
    with pytest.raises(ValueError, match="different directories"):
        state.validate()


def test_first_run_rejects_nested_libraries(tmp_path: Path):
    parent = tmp_path / "Parent"
    child = parent / "Child"
    child.mkdir(parents=True)
    state = FirstRunState(library_a=str(parent), library_b=str(child), backup_location=str(tmp_path / "backup"))
    with pytest.raises(ValueError, match="contain one another"):
        state.validate()


def test_first_run_rejects_backup_inside_library(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    a.mkdir()
    b.mkdir()
    state = FirstRunState(library_a=str(a), library_b=str(b), backup_location=str(a / "backups"))
    with pytest.raises(ValueError, match="overlaps library"):
        state.validate()


def test_first_run_rejects_missing_library(tmp_path: Path):
    a = tmp_path / "missing"
    b = tmp_path / "B"
    b.mkdir()
    state = FirstRunState(library_a=str(a), library_b=str(b), backup_location=str(tmp_path / "backup"))
    with pytest.raises(FileNotFoundError):
        state.validate()


def test_first_run_rejects_invalid_mode_and_master(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    a.mkdir()
    b.mkdir()
    invalid_mode = FirstRunState(library_a=str(a), library_b=str(b), sync_mode="unknown", backup_location=str(tmp_path / "backup"))
    with pytest.raises(ValueError, match="valid sync mode"):
        invalid_mode.validate()
    invalid_master = FirstRunState(library_a=str(a), library_b=str(b), master="unknown", backup_location=str(tmp_path / "backup"))
    with pytest.raises(ValueError, match="valid master"):
        invalid_master.validate()


def test_app_integrates_first_run_without_developer_defaults():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "FirstRunWizard" in source
    assert "is_first_run" in source
    assert "self.after_idle(self._run_first_run)" in source
    assert "E:\\Ava files" not in source
    assert "DEFAULT_LAPTOP" not in source
    assert "DEFAULT_PHONE_COPY" not in source

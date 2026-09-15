from pathlib import Path

from music_sync.settings import Settings, SettingsStore


def test_defaults_contain_no_library_paths():
    settings = Settings()
    assert settings.library_a == ""
    assert settings.library_b == ""
    assert settings.backup_location == ""


def test_round_trip_preserves_all_settings(tmp_path: Path):
    store = SettingsStore(tmp_path / "config")
    settings = Settings(
        library_a="C:/Music A/夜",
        library_b="D:/Music B",
        master="library_b",
        sync_mode="reconcile",
        backup_location="E:/Backups",
        fuzzy_threshold=0.91,
        conflict_defaults={"artwork": "skip"},
        appearance="dark",
    )

    path = store.save(settings)
    loaded = store.load()

    assert path == tmp_path / "config" / "settings.json"
    assert loaded == settings


def test_corrupt_json_returns_defaults(tmp_path: Path):
    store = SettingsStore(tmp_path / "config")
    store.config_dir.mkdir()
    store.path.write_text("{not valid json", encoding="utf-8")

    assert store.load() == Settings()


def test_invalid_values_are_rejected_on_save(tmp_path: Path):
    store = SettingsStore(tmp_path / "config")
    invalid = Settings(fuzzy_threshold=2.0)

    try:
        store.save(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("Invalid settings should be rejected")
    assert not store.path.exists()


def test_atomic_save_does_not_leave_temporary_file(tmp_path: Path):
    store = SettingsStore(tmp_path / "config")
    store.save(Settings(appearance="dark"))

    assert store.path.is_file()
    assert not store.path.with_suffix(".json.tmp").exists()

from pathlib import Path

from music_sync.settings import PORTABLE_MARKER, Settings, SettingsStore, application_directory, is_portable_mode, portable_config_dir


def test_application_directory_uses_executable_parent(tmp_path: Path):
    executable = tmp_path / "USB Drive" / "music-sync.exe"
    assert application_directory(executable) == executable.parent.resolve()


def test_portable_marker_selects_config_beside_executable(tmp_path: Path):
    executable = tmp_path / "music-sync" / "music-sync.exe"
    executable.parent.mkdir()
    marker = executable.parent / PORTABLE_MARKER
    marker.write_text("", encoding="utf-8")

    assert is_portable_mode(executable) is True
    assert portable_config_dir(executable) == executable.parent / "config"


def test_missing_portable_marker_does_not_enable_portable_mode(tmp_path: Path):
    executable = tmp_path / "music-sync" / "music-sync.exe"
    executable.parent.mkdir()

    assert is_portable_mode(executable) is False


def test_portable_settings_store_never_writes_to_music_library(tmp_path: Path):
    application = tmp_path / "Removable" / "music-sync.exe"
    application.parent.mkdir()
    (application.parent / PORTABLE_MARKER).write_text("", encoding="utf-8")
    library = tmp_path / "Music"
    library.mkdir()

    store = SettingsStore(portable_config_dir(application))
    settings = Settings(library_a=str(library), library_b=str(tmp_path / "Other"))
    path = store.save(settings)

    assert path == application.parent / "config" / "settings.json"
    assert path.is_file()
    assert not (library / "settings.json").exists()

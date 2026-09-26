from pathlib import Path

from harmelune.settings import PORTABLE_MARKER, Settings, SettingsStore, application_directory, is_portable_mode, portable_config_dir


def test_application_directory_uses_executable_parent(tmp_path: Path):
    executable = tmp_path / "USB Drive" / "harmelune.exe"
    assert application_directory(executable) == executable.parent.resolve()


def test_portable_marker_selects_config_beside_executable(tmp_path: Path):
    executable = tmp_path / "harmelune" / "harmelune.exe"
    executable.parent.mkdir()
    marker = executable.parent / PORTABLE_MARKER
    marker.write_text("", encoding="utf-8")

    assert is_portable_mode(executable) is True
    assert portable_config_dir(executable) == executable.parent / "config"


def test_missing_portable_marker_does_not_enable_portable_mode(tmp_path: Path):
    executable = tmp_path / "harmelune" / "harmelune.exe"
    executable.parent.mkdir()

    assert is_portable_mode(executable) is False


def test_portable_settings_store_never_writes_to_music_library(tmp_path: Path):
    application = tmp_path / "Removable" / "harmelune.exe"
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

def test_legacy_portable_marker_still_enables_portable_mode(tmp_path: Path):
    from harmelune.settings import LEGACY_PORTABLE_MARKER

    executable = tmp_path / "legacy" / "music-sync.exe"
    executable.parent.mkdir()
    (executable.parent / LEGACY_PORTABLE_MARKER).write_text("", encoding="utf-8")

    assert is_portable_mode(executable) is True


def test_new_portable_marker_name_is_harmelune():
    from harmelune.settings import PORTABLE_MARKER

    assert PORTABLE_MARKER == ".harmelune-portable"


def test_default_config_uses_harmelune(monkeypatch, tmp_path: Path):
    import harmelune.settings as settings_module

    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))

    assert settings_module.default_config_dir() == tmp_path / "AppData" / "Harmelune"


def test_legacy_settings_are_loaded_from_old_config(monkeypatch, tmp_path: Path):
    import harmelune.settings as settings_module

    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))

    legacy = tmp_path / "AppData" / "music-sync"
    legacy.mkdir(parents=True)
    (legacy / "settings.json").write_text(
        '{"library_a":"C:/Old Music","appearance":"dark"}',
        encoding="utf-8",
    )

    store = settings_module.SettingsStore()
    loaded = store.load()

    assert loaded.library_a == "C:/Old Music"
    assert loaded.appearance == "dark"
    assert store.path == tmp_path / "AppData" / "Harmelune" / "settings.json"


def test_new_settings_take_precedence_over_legacy(monkeypatch, tmp_path: Path):
    import harmelune.settings as settings_module

    monkeypatch.setenv("APPDATA", str(tmp_path / "AppData"))

    legacy = tmp_path / "AppData" / "music-sync"
    legacy.mkdir(parents=True)
    (legacy / "settings.json").write_text(
        '{"library_a":"C:/Old Music"}',
        encoding="utf-8",
    )

    current = tmp_path / "AppData" / "Harmelune"
    current.mkdir(parents=True)
    (current / "settings.json").write_text(
        '{"library_a":"D:/New Music"}',
        encoding="utf-8",
    )

    loaded = settings_module.SettingsStore().load()

    assert loaded.library_a == "D:/New Music"

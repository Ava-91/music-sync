from pathlib import Path


def test_app_has_no_developer_music_paths():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "E:\\Ava files" not in source
    assert "DEFAULT_LAPTOP" not in source
    assert "DEFAULT_PHONE_COPY" not in source
    assert "Ava Music Sync" not in source


def test_app_uses_generic_v1_components():
    source = Path("app.py").read_text(encoding="utf-8")
    for required in (
        "SettingsStore",
        "MasterLibrary",
        "SyncMode",
        "build_health_report",
        "execute_safe",
        "execute_reconcile",
        "execute_mirror",
        "dry_run_safe",
        "dry_run_reconcile",
        "dry_run_mirror",
        "report_from_safe",
        "report_from_reconcile",
        "report_from_mirror",
    ):
        assert required in source


def test_app_module_imports_without_constructing_a_window():
    import app

    assert hasattr(app, "HarmeluneApp")

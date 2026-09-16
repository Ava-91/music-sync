from pathlib import Path


def test_main_gui_exposes_backup_manager_actions_without_personal_defaults():
    source = Path("app.py").read_text(encoding="utf-8")
    assert "open_backup_manager" in source
    assert "Backups A" in source
    assert "Backups B" in source
    assert "self.plan = None" in source
    assert "scan again before applying changes" in source
    assert "E:\\Ava files" not in source


def test_backup_dialog_reports_success_to_the_caller():
    source = Path("music_sync/backup_ui.py").read_text(encoding="utf-8")
    assert "self.restored = False" in source
    assert "self.restored = True" in source
    assert "return dialog" in source

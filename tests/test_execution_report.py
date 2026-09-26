from pathlib import Path

from harmelune.execution_report import (
    ReportStatus,
    report_from_mirror,
    report_from_reconcile,
    report_from_safe,
    report_from_transaction,
)
from harmelune.mirror import MirrorResult
from harmelune.reconcile import ReconcileResult
from harmelune.sync import SafeExecutionResult
from harmelune.transaction import FileOperation, OperationKind, TransactionResult


def test_safe_report_records_actual_copy_and_backup():
    result = SafeExecutionResult(
        copied=[(Path("A/夜.mp3"), Path("B/夜.mp3"))],
        backup=Path("Backups/music_backup_1"),
    )
    report = report_from_safe(result)
    assert report.final_status is ReportStatus.SUCCESS
    assert report.succeeded == 1
    assert report.copied == ["A/夜.mp3 -> B/夜.mp3"]
    assert report.backups == ["Backups/music_backup_1"]


def test_reconcile_report_distinguishes_copy_replace_and_block():
    result = ReconcileResult(
        copied=[(Path("A/new.mp3"), Path("B/new.mp3"))],
        replaced=[(Path("A/song.mp3"), Path("B/song.mp3"))],
        blocked=["match:A/uncertain.mp3"],
        backups={"library_b": Path("Backups/b")},
    )
    report = report_from_reconcile(result)
    assert report.final_status is ReportStatus.PARTIAL
    assert report.succeeded == 2
    assert report.copied == ["A/new.mp3 -> B/new.mp3"]
    assert report.replaced == ["A/song.mp3 -> B/song.mp3"]
    assert report.conflicts == ["match:A/uncertain.mp3"]


def test_mirror_report_records_deletion_and_rollback_failure():
    result = MirrorResult(
        deleted=[Path("B/old.mp3")],
        backup=Path("Backups/b"),
        failures=["copy failed"],
        rollback_failures=["rollback failed"],
    )
    report = report_from_mirror(result)
    assert report.final_status is ReportStatus.PARTIAL
    assert report.deleted == ["B/old.mp3"]
    assert report.rollback_failures == ["rollback failed"]


def test_transaction_report_records_operation_types():
    result = TransactionResult(
        attempted=3,
        succeeded=[
            FileOperation(OperationKind.COPY, Path("A/a.mp3"), Path("B/a.mp3")),
            FileOperation(OperationKind.REPLACE, Path("A/b.mp3"), Path("B/b.mp3")),
            FileOperation(OperationKind.DELETE, None, Path("B/c.mp3")),
        ],
    )
    report = report_from_transaction(result)
    assert report.final_status is ReportStatus.SUCCESS
    assert report.copied == ["A/a.mp3 -> B/a.mp3"]
    assert report.replaced == ["A/b.mp3 -> B/b.mp3"]
    assert report.deleted == ["B/c.mp3"]


def test_json_export_preserves_unicode(tmp_path: Path):
    result = SafeExecutionResult(copied=[(Path("Library A – 夜/曲.mp3"), Path("Library B/曲.mp3"))])
    report = report_from_safe(result)
    path = report.save_json(tmp_path / "report.json")
    text = path.read_text(encoding="utf-8")
    assert "Library A – 夜" in text
    assert "曲.mp3" in text
    assert '"final_status": "SUCCESS"' in text

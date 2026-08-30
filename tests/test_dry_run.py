from pathlib import Path

from music_sync.dry_run import summarize
from music_sync.models import Match, SyncPlan, Track


def test_dry_run_is_read_only_and_counts_changes():
    left = Track(path=Path("a.mp3"), side="laptop")
    right = Track(path=Path("b.mp3"), side="phone")
    plan = SyncPlan(
        phone_only=[right],
        matches=[Match(left, right, 1.0, metadata_conflict=True, artwork_conflict=True)],
    )
    summary = summarize(plan, scan_errors=2)
    assert summary.add == 1
    assert summary.matched == 1
    assert summary.fuzzy == 0
    assert summary.metadata_conflicts == 1
    assert summary.artwork_conflicts == 1
    assert summary.scan_errors == 2
    assert summary.changes == 3

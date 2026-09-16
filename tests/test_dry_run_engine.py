from pathlib import Path

import pytest

from music_sync.direction import MasterLibrary, SyncDirection
from music_sync.dry_run import dry_run_mirror, dry_run_reconcile, dry_run_safe
from music_sync.freshness import StalePlanError
from music_sync.mirror import MirrorAction
from music_sync.models import Match, SyncPlan, Track
from music_sync.reconcile import ReconcileDecision
from music_sync.scanner import current_fingerprint


def fresh_plan(a: Path, b: Path, **kwargs) -> SyncPlan:
    return SyncPlan(
        library_a_root=a,
        library_b_root=b,
        fingerprint_a=current_fingerprint(a),
        fingerprint_b=current_fingerprint(b),
        **kwargs,
    )


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def test_safe_dry_run_is_read_only(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    a.mkdir()
    b.mkdir()
    track = a / "new.mp3"
    track.write_bytes(b"new")
    before_a = snapshot(a)
    before_b = snapshot(b)
    plan = fresh_plan(a, b, library_a_only=[Track(track, "a")])

    result = dry_run_safe(plan, SyncDirection(a, b, MasterLibrary.LIBRARY_A))

    assert result.status == "SUCCESS"
    assert result.operations[0].destination == b / "new.mp3"
    assert snapshot(a) == before_a
    assert snapshot(b) == before_b
    assert not (tmp_path / "Backups").exists()


def test_reconcile_dry_run_is_read_only(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    a.mkdir()
    b.mkdir()
    left = a / "song.mp3"
    right = b / "song.mp3"
    left.write_bytes(b"a")
    right.write_bytes(b"b")
    match = Match(Track(left, "a", file_hash="a"), Track(right, "b", file_hash="b"), 1.0, metadata_conflict=True)
    assert match.metadata_conflict is True
    plan = fresh_plan(a, b, matches=[match])
    before_a = snapshot(a)
    before_b = snapshot(b)

    result = dry_run_reconcile(plan, {f"match:{left}": ReconcileDecision.KEEP_A}, tmp_path / "Backups")

    assert result.status == "SUCCESS"
    assert result.operations[0].kind.value == "replace"
    assert snapshot(a) == before_a
    assert snapshot(b) == before_b
    assert not (tmp_path / "Backups").exists()


def test_mirror_dry_run_is_read_only_and_lists_deletion(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    a.mkdir()
    b.mkdir()
    new = a / "new.mp3"
    old = b / "old.mp3"
    new.write_bytes(b"new")
    old.write_bytes(b"old")
    plan = fresh_plan(a, b, library_a_only=[Track(new, "a")], library_b_only=[Track(old, "b")])
    before_a = snapshot(a)
    before_b = snapshot(b)

    result = dry_run_mirror(plan, SyncDirection(a, b, MasterLibrary.LIBRARY_A))

    assert result.status == "SUCCESS"
    assert {operation.kind for operation in result.operations} == {MirrorAction.COPY.value, MirrorAction.DELETE.value}
    assert snapshot(a) == before_a
    assert snapshot(b) == before_b


def test_dry_run_blocks_stale_plan(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    a.mkdir()
    b.mkdir()
    track = a / "song.mp3"
    track.write_bytes(b"old")
    plan = fresh_plan(a, b, library_a_only=[Track(track, "a")])
    track.write_bytes(b"changed")

    with pytest.raises(StalePlanError):
        dry_run_safe(plan, SyncDirection(a, b, MasterLibrary.LIBRARY_A))

from pathlib import Path

import pytest

from music_sync.direction import MasterLibrary
from music_sync.models import Match, SyncPlan, Track
from music_sync.reconcile import ReconcileDecision, execute_reconcile
from music_sync.scanner import current_fingerprint


def fresh_plan(a: Path, b: Path, **kwargs) -> SyncPlan:
    return SyncPlan(
        library_a_root=a,
        library_b_root=b,
        fingerprint_a=current_fingerprint(a),
        fingerprint_b=current_fingerprint(b),
        **kwargs,
    )


def test_a_only_requires_explicit_copy_decision(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    backups = tmp_path / "Backups"
    a.mkdir()
    b.mkdir()
    track = a / "new.mp3"
    track.write_bytes(b"a")
    plan = fresh_plan(a, b, library_a_only=[Track(track, "a")])

    blocked = execute_reconcile(plan, {}, backups)
    assert blocked.status == "BLOCKED"
    assert not (b / "new.mp3").exists()

    # The filesystem changed only by the test's deliberate source creation, so rescan.
    plan = fresh_plan(a, b, library_a_only=[Track(track, "a")])
    result = execute_reconcile(plan, {f"a-only:{track}": ReconcileDecision.COPY_A_TO_B}, backups)
    assert result.status == "SUCCESS"
    assert (b / "new.mp3").read_bytes() == b"a"
    assert result.backups["library_b"].is_dir()


def test_b_only_can_copy_back_to_a(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    backups = tmp_path / "Backups"
    a.mkdir()
    b.mkdir()
    track = b / "new.mp3"
    track.write_bytes(b"b")
    plan = fresh_plan(a, b, library_b_only=[Track(track, "b")])

    result = execute_reconcile(plan, {f"b-only:{track}": ReconcileDecision.COPY_B_TO_A}, backups)
    assert result.status == "SUCCESS"
    assert (a / "new.mp3").read_bytes() == b"b"
    assert result.backups["library_a"].is_dir()


def test_conflict_keep_a_keep_b_and_skip_are_explicit(tmp_path: Path):
    for decision, expected in [
        (ReconcileDecision.KEEP_A, b"a"),
        (ReconcileDecision.KEEP_B, b"b"),
        (ReconcileDecision.SKIP, b"b"),
    ]:
        root = tmp_path / decision.value
        a = root / "A"
        b = root / "B"
        backups = root / "Backups"
        a.mkdir(parents=True)
        b.mkdir()
        a_track = a / "song.mp3"
        b_track = b / "song.mp3"
        a_track.write_bytes(b"a")
        b_track.write_bytes(b"b")
        match = Match(Track(a_track, "a", artwork_hash="a"), Track(b_track, "b", artwork_hash="b"), 0.9, artwork_conflict=True)
        plan = fresh_plan(a, b, matches=[match])

        result = execute_reconcile(plan, {f"match:{a_track}": decision}, backups)
        assert result.status == "SUCCESS"
        assert a_track.read_bytes() == expected if decision is not ReconcileDecision.KEEP_B else b"a"
        assert b_track.read_bytes() == expected


def test_unresolved_fuzzy_match_blocks_without_decision(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    backups = tmp_path / "Backups"
    a.mkdir()
    b.mkdir()
    a_track = a / "maybe.mp3"
    b_track = b / "maybe-copy.mp3"
    a_track.write_bytes(b"a")
    b_track.write_bytes(b"b")
    match = Match(Track(a_track, "a"), Track(b_track, "b"), 0.91, confirmed=False)
    plan = fresh_plan(a, b, matches=[match])

    result = execute_reconcile(plan, {}, backups)

    assert result.status == "BLOCKED"
    assert a_track.read_bytes() == b"a"
    assert b_track.read_bytes() == b"b"
    assert result.backups == {}


def test_reconcile_never_deletes_files(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    backups = tmp_path / "Backups"
    a.mkdir()
    b.mkdir()
    a_track = a / "keep-a.mp3"
    b_track = b / "keep-b.mp3"
    a_track.write_bytes(b"a")
    b_track.write_bytes(b"b")
    plan = fresh_plan(a, b)

    result = execute_reconcile(plan, {}, backups)

    assert result.status == "SUCCESS"
    assert a_track.exists()
    assert b_track.exists()

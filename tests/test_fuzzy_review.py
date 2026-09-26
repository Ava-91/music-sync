from pathlib import Path

import pytest

from harmelune.direction import MasterLibrary, SyncDirection
from harmelune.fuzzy_ui import apply_fuzzy_decisions
from harmelune.mirror import MirrorAction, build_mirror_preview, execute_mirror
from harmelune.models import Match, SyncPlan, Track
from harmelune.scanner import current_fingerprint


def make_track(name: str, side: str, root: Path | None = None) -> Track:
    path = (root / name) if root is not None else Path(name)
    return Track(path=path, side=side, title=name, artist="Artist", album="Album", file_hash=f"hash-{name}")


def fresh_plan(a_root: Path, b_root: Path, **kwargs) -> SyncPlan:
    return SyncPlan(
        library_a_root=a_root,
        library_b_root=b_root,
        fingerprint_a=current_fingerprint(a_root),
        fingerprint_b=current_fingerprint(b_root),
        **kwargs,
    )


def test_confirmed_fuzzy_match_becomes_safe_match():
    a_track = make_track("a.mp3", "a")
    b_track = make_track("b.mp3", "b")
    match = Match(a_track, b_track, 0.91, confirmed=False)
    plan = apply_fuzzy_decisions(SyncPlan(matches=[match]), {str(a_track.path): True})
    assert len(plan.matches) == 1
    assert plan.matches[0].confirmed is True
    assert plan.library_a_only == []
    assert plan.library_b_only == []


def test_rejected_fuzzy_match_becomes_both_only():
    """Rejecting a fuzzy match must keep BOTH tracks as independent library-only entries."""
    a_track = make_track("a-only-after-reject.mp3", "a")
    b_track = make_track("b-only-after-reject.mp3", "b")
    match = Match(a_track, b_track, 0.91, confirmed=False)
    plan = apply_fuzzy_decisions(SyncPlan(matches=[match]), {str(a_track.path): False})
    assert plan.matches == []
    assert plan.library_a_only == [a_track]
    assert plan.library_b_only == [b_track]


def test_unreviewed_fuzzy_match_remains_unconfirmed():
    a_track = make_track("a.mp3", "a")
    b_track = make_track("b.mp3", "b")
    match = Match(a_track, b_track, 0.91, confirmed=False)
    plan = apply_fuzzy_decisions(SyncPlan(matches=[match]), {})
    assert plan.matches == [match]
    assert plan.matches[0].confirmed is False
    assert plan.library_a_only == []
    assert plan.library_b_only == []


def test_unreviewed_fuzzy_match_does_not_drop_existing_matches():
    fuzzy_left = make_track("fuzzy.mp3", "a")
    fuzzy_right = make_track("fuzzy-copy.mp3", "b")
    trusted_left = make_track("trusted.mp3", "a")
    trusted_right = make_track("trusted-copy.mp3", "b")
    fuzzy = Match(fuzzy_left, fuzzy_right, 0.91, confirmed=False)
    trusted = Match(trusted_left, trusted_right, 1.0, confirmed=True)

    plan = apply_fuzzy_decisions(SyncPlan(matches=[trusted, fuzzy]), {})

    assert plan.matches == [trusted, fuzzy]
    assert plan.matches[1].confirmed is False


def test_rejected_fuzzy_preserves_existing_only_lists():
    existing_a = make_track("existing-a.mp3", "a")
    existing_b = make_track("existing-b.mp3", "b")
    a_track = make_track("reject-a.mp3", "a")
    b_track = make_track("reject-b.mp3", "b")
    match = Match(a_track, b_track, 0.91, confirmed=False)
    plan = apply_fuzzy_decisions(
        SyncPlan(library_a_only=[existing_a], library_b_only=[existing_b], matches=[match]),
        {str(a_track.path): False},
    )
    assert plan.library_a_only == [existing_a, a_track]
    assert plan.library_b_only == [existing_b, b_track]
    assert plan.matches == []


def test_rejected_fuzzy_mirror_a_to_b_preview_and_execution(tmp_path: Path):
    """
    Full interaction regression for rejected fuzzy + Mirror A → B:

    1. Fuzzy candidate presented
    2. User rejects → both tracks become independent A-only and B-only
    3. Mirror A → B preview lists COPY of A track and DELETE of B track
       (correct Mirror semantics: make B look like A)
    4. Execution succeeds; A is never mutated; B receives A track and loses B-only track
    5. Report/status remains SUCCESS
    """
    a = tmp_path / "A"
    b = tmp_path / "B"
    backups = tmp_path / "Backups"
    a.mkdir()
    b.mkdir()
    a_file = a / "song-x.mp3"
    b_file = b / "song-y.mp3"
    a_file.write_bytes(b"content-x")
    b_file.write_bytes(b"content-y")

    a_track = Track(a_file, "a", title="Song X", artist="Artist", album="Album", file_hash="hash-x")
    b_track = Track(b_file, "b", title="Song Y", artist="Artist", album="Album", file_hash="hash-y")
    match = Match(a_track, b_track, 0.91, confirmed=False)

    plan = fresh_plan(a, b, matches=[match])
    assert plan.library_a_only == []
    assert plan.library_b_only == []

    plan = apply_fuzzy_decisions(plan, {str(a_track.path): False})

    assert plan.matches == []
    assert len(plan.library_a_only) == 1 and plan.library_a_only[0].path == a_file
    assert len(plan.library_b_only) == 1 and plan.library_b_only[0].path == b_file

    direction = SyncDirection(a, b, MasterLibrary.LIBRARY_A)
    preview = build_mirror_preview(plan, direction)
    assert not preview.blocked
    actions = {op.action for op in preview.operations}
    assert MirrorAction.COPY in actions
    assert MirrorAction.DELETE in actions
    assert any(op.destination == b_file for op in preview.deletions)
    assert any(op.source == a_file for op in preview.copies)

    assert a_file.read_bytes() == b"content-x"
    assert b_file.read_bytes() == b"content-y"

    result = execute_mirror(plan, direction, backups, "MIRROR")
    assert result.status == "SUCCESS"
    assert (b / "song-x.mp3").exists()
    assert (b / "song-x.mp3").read_bytes() == b"content-x"
    assert not b_file.exists()
    assert a_file.exists()


def test_rejected_fuzzy_mirror_b_to_a_preview_and_execution(tmp_path: Path):
    """Mirror B → A after rejection: deletes A-only, copies B-only (correct Mirror semantics)."""
    a = tmp_path / "A"
    b = tmp_path / "B"
    backups = tmp_path / "Backups"
    a.mkdir()
    b.mkdir()
    a_file = a / "song-x.mp3"
    b_file = b / "song-y.mp3"
    a_file.write_bytes(b"content-x")
    b_file.write_bytes(b"content-y")

    a_track = Track(a_file, "a", title="Song X", file_hash="hash-x")
    b_track = Track(b_file, "b", title="Song Y", file_hash="hash-y")
    match = Match(a_track, b_track, 0.91, confirmed=False)
    plan = apply_fuzzy_decisions(fresh_plan(a, b, matches=[match]), {str(a_track.path): False})

    direction = SyncDirection(a, b, MasterLibrary.LIBRARY_B)
    preview = build_mirror_preview(plan, direction)
    assert not preview.blocked
    assert any(op.destination == a_file for op in preview.deletions)

    result = execute_mirror(plan, direction, backups, "MIRROR")
    assert result.status == "SUCCESS"
    assert not a_file.exists()
    assert (a / "song-y.mp3").exists()
    assert b_file.exists()

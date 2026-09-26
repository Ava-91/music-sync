from pathlib import Path

import pytest

from harmelune.direction import MasterLibrary, SyncDirection
from harmelune.mirror import MirrorAction, MirrorConfirmationError, build_mirror_preview, execute_mirror
from harmelune.models import Match, SyncPlan, Track
from harmelune.scanner import current_fingerprint


def fresh_plan(a: Path, b: Path, **kwargs) -> SyncPlan:
    return SyncPlan(
        library_a_root=a,
        library_b_root=b,
        fingerprint_a=current_fingerprint(a),
        fingerprint_b=current_fingerprint(b),
        **kwargs,
    )


def test_mirror_preview_lists_copy_replace_delete_without_modifying_files(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    backups = tmp_path / "Backups"
    a.mkdir()
    b.mkdir()
    copy_source = a / "new.mp3"
    delete_target = b / "old.mp3"
    replace_source = a / "song.mp3"
    replace_target = b / "song.mp3"
    copy_source.write_bytes(b"new")
    delete_target.write_bytes(b"delete me")
    replace_source.write_bytes(b"source")
    replace_target.write_bytes(b"old")
    (b / "keep.txt").write_text("not music")

    match = Match(
        Track(replace_source, "a", file_hash="hash-a"),
        Track(replace_target, "b", file_hash="hash-b"),
        1.0,
    )
    plan = fresh_plan(
        a,
        b,
        library_a_only=[Track(copy_source, "a")],
        library_b_only=[Track(delete_target, "b")],
        matches=[match],
    )
    preview = build_mirror_preview(plan, SyncDirection(a, b, MasterLibrary.LIBRARY_A))

    assert not preview.blocked
    assert [operation.action for operation in preview.operations] == [
        MirrorAction.COPY,
        MirrorAction.DELETE,
        MirrorAction.REPLACE,
    ]
    assert not (b / "new.mp3").exists()
    assert delete_target.exists()
    assert replace_target.read_bytes() == b"old"
    assert (b / "keep.txt").exists()


def test_mirror_requires_exact_confirmation(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    a.mkdir()
    b.mkdir()
    source = a / "new.mp3"
    source.write_bytes(b"new")
    plan = fresh_plan(a, b, library_a_only=[Track(source, "a")])

    with pytest.raises(MirrorConfirmationError, match="MIRROR"):
        execute_mirror(plan, SyncDirection(a, b, MasterLibrary.LIBRARY_A), tmp_path / "Backups", "yes")
    assert not (b / "new.mp3").exists()


def test_mirror_applies_explicit_confirmation_and_backup(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    backups = tmp_path / "Backups"
    a.mkdir()
    b.mkdir()
    source = a / "new.mp3"
    old = b / "old.mp3"
    source.write_bytes(b"new")
    old.write_bytes(b"old")
    plan = fresh_plan(a, b, library_a_only=[Track(source, "a")], library_b_only=[Track(old, "b")])

    result = execute_mirror(plan, SyncDirection(a, b, MasterLibrary.LIBRARY_A), backups, "MIRROR")

    assert result.status == "SUCCESS"
    assert (b / "new.mp3").read_bytes() == b"new"
    assert not old.exists()
    assert result.backup is not None and result.backup.is_dir()


def test_mirror_blocks_unresolved_fuzzy_matches(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    a.mkdir()
    b.mkdir()
    left = a / "maybe.mp3"
    right = b / "maybe-copy.mp3"
    left.write_bytes(b"a")
    right.write_bytes(b"b")
    match = Match(Track(left, "a"), Track(right, "b"), 0.91, confirmed=False)
    plan = fresh_plan(a, b, matches=[match])

    with pytest.raises(MirrorConfirmationError, match="fuzzy"):
        execute_mirror(plan, SyncDirection(a, b, MasterLibrary.LIBRARY_A), tmp_path / "Backups", "MIRROR")

    assert left.read_bytes() == b"a"
    assert right.read_bytes() == b"b"

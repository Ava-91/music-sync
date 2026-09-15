from pathlib import Path

from music_sync.direction import MasterLibrary, SyncDirection
from music_sync.models import Match, SyncPlan, Track
from music_sync.scanner import current_fingerprint
from music_sync.sync import execute_safe


def make_direction(source: Path, destination: Path, master: MasterLibrary) -> SyncDirection:
    return SyncDirection(source=source, destination=destination, master=master)


def with_fingerprints(plan: SyncPlan) -> SyncPlan:
    return SyncPlan(
        library_a_only=plan.library_a_only,
        library_b_only=plan.library_b_only,
        matches=plan.matches,
        library_a_root=plan.library_a_root,
        library_b_root=plan.library_b_root,
        fingerprint_a=current_fingerprint(plan.library_a_root),
        fingerprint_b=current_fingerprint(plan.library_b_root),
    )


def test_safe_sync_copies_missing_without_deleting_or_overwriting(tmp_path: Path):
    source = tmp_path / "Library A"
    destination = tmp_path / "Library B"
    backup_root = tmp_path / "Backups"
    source.mkdir()
    destination.mkdir()
    (source / "new.mp3").write_bytes(b"new")
    (destination / "existing.mp3").write_bytes(b"keep")

    plan = with_fingerprints(SyncPlan(
        library_a_only=[Track(source / "new.mp3", "a")],
        library_a_root=source,
        library_b_root=destination,
    ))
    result = execute_safe(plan, make_direction(source, destination, MasterLibrary.LIBRARY_A), backup_root)

    assert result.status == "SUCCESS"
    assert (destination / "new.mp3").read_bytes() == b"new"
    assert (destination / "existing.mp3").read_bytes() == b"keep"
    assert result.backup is not None and result.backup.is_dir()


def test_safe_sync_skips_existing_collision(tmp_path: Path):
    source = tmp_path / "A"
    destination = tmp_path / "B"
    backup_root = tmp_path / "Backups"
    source.mkdir()
    destination.mkdir()
    (source / "same.mp3").write_bytes(b"source")
    (destination / "same.mp3").write_bytes(b"destination")

    plan = with_fingerprints(SyncPlan(
        library_a_only=[Track(source / "same.mp3", "a")],
        library_a_root=source,
        library_b_root=destination,
    ))
    result = execute_safe(plan, make_direction(source, destination, MasterLibrary.LIBRARY_A), backup_root)

    assert result.status == "SUCCESS"
    assert result.skipped == [destination / "same.mp3"]
    assert (destination / "same.mp3").read_bytes() == b"destination"
    assert result.backup is None


def test_safe_sync_does_not_apply_unresolved_fuzzy_matches(tmp_path: Path):
    source = tmp_path / "A"
    destination = tmp_path / "B"
    backup_root = tmp_path / "Backups"
    source.mkdir()
    destination.mkdir()
    fuzzy_source = source / "uncertain.mp3"
    fuzzy_source.write_bytes(b"uncertain")
    fuzzy_destination = destination / "other.mp3"
    fuzzy_destination.write_bytes(b"other")

    match = Match(Track(fuzzy_source, "a"), Track(fuzzy_destination, "b"), 0.91, confirmed=False)
    plan = with_fingerprints(SyncPlan(matches=[match], library_a_root=source, library_b_root=destination))
    result = execute_safe(plan, make_direction(source, destination, MasterLibrary.LIBRARY_A), backup_root)

    assert result.copied == []
    assert not (destination / "uncertain.mp3").exists()
    assert result.backup is None


def test_safe_sync_blocks_tracks_outside_source_root(tmp_path: Path):
    source = tmp_path / "A"
    destination = tmp_path / "B"
    outside = tmp_path / "outside.mp3"
    backup_root = tmp_path / "Backups"
    source.mkdir()
    destination.mkdir()
    outside.write_bytes(b"outside")

    plan = with_fingerprints(SyncPlan(
        library_a_only=[Track(outside, "a")],
        library_a_root=source,
        library_b_root=destination,
    ))
    result = execute_safe(plan, make_direction(source, destination, MasterLibrary.LIBRARY_A), backup_root)

    assert result.status == "BLOCKED"
    assert result.blocked
    assert result.backup is None
    assert not any(destination.iterdir())

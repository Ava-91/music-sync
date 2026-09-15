from pathlib import Path
import os
import shutil

import pytest

from music_sync.freshness import StalePlanError, validate_plan_freshness
from music_sync.models import SyncPlan
from music_sync.scanner import current_fingerprint


def make_plan(a: Path, b: Path) -> SyncPlan:
    return SyncPlan(
        library_a_root=a,
        library_b_root=b,
        fingerprint_a=current_fingerprint(a),
        fingerprint_b=current_fingerprint(b),
    )


def make_libraries(tmp_path: Path) -> tuple[Path, Path]:
    a = tmp_path / "A"
    b = tmp_path / "B"
    a.mkdir()
    b.mkdir()
    (a / "one.mp3").write_bytes(b"one")
    (b / "two.mp3").write_bytes(b"two")
    return a, b


def test_fresh_plan_is_accepted(tmp_path: Path):
    a, b = make_libraries(tmp_path)
    validate_plan_freshness(make_plan(a, b))


@pytest.mark.parametrize("mutation", ["add", "delete", "size", "mtime"])
def test_filesystem_change_invalidates_plan(tmp_path: Path, mutation: str):
    a, b = make_libraries(tmp_path)
    plan = make_plan(a, b)
    target = a / "one.mp3"

    if mutation == "add":
        (a / "new.mp3").write_bytes(b"new")
    elif mutation == "delete":
        target.unlink()
    elif mutation == "size":
        target.write_bytes(b"one plus more")
    else:
        stat = target.stat()
        os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))

    with pytest.raises(StalePlanError, match="Scan both libraries again"):
        validate_plan_freshness(plan)


def test_missing_library_blocks_execution(tmp_path: Path):
    a, b = make_libraries(tmp_path)
    plan = make_plan(a, b)
    shutil.rmtree(b)
    with pytest.raises(StalePlanError, match="unavailable"):
        validate_plan_freshness(plan)


def test_missing_fingerprint_metadata_blocks_execution(tmp_path: Path):
    a, b = make_libraries(tmp_path)
    plan = SyncPlan(library_a_root=a, library_b_root=b)
    with pytest.raises(StalePlanError, match="fingerprints"):
        validate_plan_freshness(plan)

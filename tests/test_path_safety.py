from pathlib import Path

import pytest

from harmelune.path_safety import validate_backup_root, validate_library_pair


def test_valid_unicode_and_space_paths_are_accepted(tmp_path: Path):
    a = tmp_path / "Library A – 夜"
    b = tmp_path / "My Music B"
    a.mkdir()
    b.mkdir()

    resolved_a, resolved_b = validate_library_pair(a, b)

    assert resolved_a == a.resolve()
    assert resolved_b == b.resolve()


def test_identical_paths_are_rejected(tmp_path: Path):
    library = tmp_path / "Library"
    library.mkdir()
    with pytest.raises(ValueError, match="different"):
        validate_library_pair(library, library)


def test_nested_paths_are_rejected(tmp_path: Path):
    outer = tmp_path / "Library"
    inner = outer / "Nested"
    inner.mkdir(parents=True)
    with pytest.raises(ValueError, match="contain one another"):
        validate_library_pair(outer, inner)
    with pytest.raises(ValueError, match="contain one another"):
        validate_library_pair(inner, outer)


def test_missing_library_is_rejected(tmp_path: Path):
    a = tmp_path / "missing"
    b = tmp_path / "B"
    b.mkdir()
    with pytest.raises(FileNotFoundError):
        validate_library_pair(a, b)


def test_backup_root_cannot_overlap_library(tmp_path: Path):
    library = tmp_path / "Library"
    library.mkdir()
    with pytest.raises(ValueError, match="overlaps"):
        validate_backup_root(library / "Backups", (library,))
    with pytest.raises(ValueError, match="overlaps"):
        validate_backup_root(library.parent, (library,))


def test_backup_root_may_be_created_outside_libraries(tmp_path: Path):
    library = tmp_path / "Library"
    backup = tmp_path / "Backups"
    library.mkdir()
    assert validate_backup_root(backup, (library,)) == backup.resolve()

from pathlib import Path

import pytest

from harmelune.direction import MasterLibrary, select_master


def test_library_a_is_explicit_master():
    direction = select_master(Path("Library A"), Path("Library B"), MasterLibrary.LIBRARY_A)
    assert direction.source == Path("Library A").resolve()
    assert direction.destination == Path("Library B").resolve()
    assert direction.master is MasterLibrary.LIBRARY_A


def test_library_b_is_explicit_master():
    direction = select_master(Path("Library A"), Path("Library B"), MasterLibrary.LIBRARY_B)
    assert direction.source == Path("Library B").resolve()
    assert direction.destination == Path("Library A").resolve()
    assert direction.master is MasterLibrary.LIBRARY_B


@pytest.mark.parametrize("master", [None, "laptop", "phone", "other"])
def test_invalid_master_is_rejected(master):
    with pytest.raises(ValueError):
        select_master(Path("A"), Path("B"), master)


def test_identical_paths_are_rejected():
    path = Path("same-library")
    with pytest.raises(ValueError):
        select_master(path, path, MasterLibrary.LIBRARY_A)

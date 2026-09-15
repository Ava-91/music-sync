from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class MasterLibrary(str, Enum):
    LIBRARY_A = "library_a"
    LIBRARY_B = "library_b"


@dataclass(frozen=True, slots=True)
class SyncDirection:
    """Explicit source/destination selection for a directed sync operation."""

    source: Path
    destination: Path
    master: MasterLibrary


def select_master(
    library_a: Path,
    library_b: Path,
    master: MasterLibrary | str | None,
) -> SyncDirection:
    """Resolve an explicit master choice without touching either library."""
    if master is None:
        raise ValueError("A master library must be selected explicitly.")

    try:
        selected = MasterLibrary(master)
    except ValueError as exc:
        raise ValueError(f"Invalid master library: {master!r}") from exc

    a = library_a.expanduser().resolve(strict=False)
    b = library_b.expanduser().resolve(strict=False)
    if a == b:
        raise ValueError("Library A and Library B must be different directories.")

    if selected is MasterLibrary.LIBRARY_A:
        return SyncDirection(source=a, destination=b, master=selected)
    return SyncDirection(source=b, destination=a, master=selected)

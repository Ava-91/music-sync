from __future__ import annotations

import os
from pathlib import Path


def resolve_user_path(path: str | Path) -> Path:
    """Normalize a user-supplied Windows path without requiring it to exist."""
    return Path(path).expanduser().resolve(strict=False)


def _require_directory(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"{label} does not exist: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"{label} is not a directory: {path}")
    if not os.access(path, os.R_OK | os.X_OK):
        raise PermissionError(f"{label} is not accessible: {path}")


def validate_library_pair(library_a: str | Path, library_b: str | Path) -> tuple[Path, Path]:
    """Validate two independent, accessible library roots before modification."""
    a = resolve_user_path(library_a)
    b = resolve_user_path(library_b)
    _require_directory(a, "Library A")
    _require_directory(b, "Library B")
    if a == b:
        raise ValueError("Library A and Library B must be different directories.")
    if a.is_relative_to(b) or b.is_relative_to(a):
        raise ValueError("Library A and Library B cannot contain one another.")
    return a, b


def validate_backup_root(backup_root: str | Path, libraries: tuple[Path, ...]) -> Path:
    """Validate that a backup root does not overlap any library being modified."""
    backup = resolve_user_path(backup_root)
    for library in libraries:
        root = library.resolve()
        if backup == root or backup.is_relative_to(root) or root.is_relative_to(backup):
            raise ValueError(f"Backup location overlaps library: {library}")
    if backup.exists() and not backup.is_dir():
        raise NotADirectoryError(f"Backup location is not a directory: {backup}")
    return backup

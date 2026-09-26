from __future__ import annotations

from os import PathLike


def display_path(value: str | PathLike[str]) -> str:
    """Render a filesystem path with stable POSIX separators for reports/UI."""
    return str(value).replace("\\", "/")

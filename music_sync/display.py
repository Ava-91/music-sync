from __future__ import annotations

from os import PathLike
from pathlib import Path


def display_path(value: str | PathLike[str]) -> str:
    """Render a filesystem path with stable POSIX separators for reports/UI."""
    return Path(value).as_posix()

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from .models import SyncPlan, Track


def make_backup(root: Path, backup_root: Path) -> Path:
    """Create a timestamped copy of the laptop library before changing it."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = backup_root / f"music_backup_{timestamp}"
    destination.mkdir(parents=True, exist_ok=False)
    shutil.copytree(root, destination, dirs_exist_ok=True)
    return destination


def unique_destination(destination: Path) -> Path:
    """Avoid overwriting an unrelated file with the same filename."""
    if not destination.exists():
        return destination
    stem, suffix = destination.stem, destination.suffix
    number = 2
    while True:
        candidate = destination.with_name(f"{stem} ({number}){suffix}")
        if not candidate.exists():
            return candidate
        number += 1


def merge_phone_only(
    plan: SyncPlan,
    laptop_root: Path,
    backup_root: Path,
) -> tuple[Path, list[tuple[Path, Path]]]:
    """Back up the laptop and copy phone-only tracks into it.

    Existing laptop files are never replaced. Phone-only files keep their
    relative path where possible; a filename collision gets a numbered name.
    """
    backup = make_backup(laptop_root, backup_root)
    copied: list[tuple[Path, Path]] = []

    for track in plan.phone_only:
        try:
            relative = track.path.relative_to(track.path.anchor)
        except ValueError:
            relative = Path(track.path.name)

        # For a copied phone folder, preserving its absolute hierarchy would be
        # undesirable. The scanner's root is not stored on Track, so use the
        # source filename and avoid collisions. A later UI can offer a folder
        # organizer; the safe default is to keep every unique file.
        destination = unique_destination(laptop_root / track.path.name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(track.path, destination)
        copied.append((track.path, destination))

    return backup, copied


def export_merged_library(laptop_root: Path, destination: Path) -> None:
    """Export the complete merged laptop library to a fresh directory."""
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")
    shutil.copytree(laptop_root, destination)

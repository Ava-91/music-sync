from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from .models import SyncPlan
from .review import ConflictChoice


def make_backup(root: Path, backup_root: Path) -> Path:
    """Create a timestamped copy of a library before changing it."""
    root = root.resolve()
    backup_root.mkdir(parents=True, exist_ok=True)
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


def merge_phone_only(plan: SyncPlan, laptop_root: Path, phone_root: Path, backup_root: Path):
    """Back up the laptop and copy phone-only tracks into it."""
    laptop_root = laptop_root.resolve()
    phone_root = phone_root.resolve()
    backup = make_backup(laptop_root, backup_root)
    copied: list[tuple[Path, Path]] = []

    for track in plan.phone_only:
        try:
            relative = track.path.relative_to(phone_root)
        except ValueError:
            relative = Path(track.path.name)
        destination = unique_destination(laptop_root / relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(track.path, destination)
        copied.append((track.path, destination))

    return backup, copied


def merge_with_conflicts(plan: SyncPlan, laptop_root: Path, phone_root: Path, backup_root: Path, choices: dict[str, ConflictChoice]):
    """Merge phone-only tracks and apply explicit conflict choices after one backup."""
    laptop_root = laptop_root.resolve()
    phone_root = phone_root.resolve()
    backup = make_backup(laptop_root, backup_root)
    copied: list[tuple[Path, Path]] = []
    replaced: list[tuple[Path, Path]] = []
    skipped: list[Path] = []

    for track in plan.phone_only:
        relative = track.path.relative_to(phone_root) if track.path.is_relative_to(phone_root) else Path(track.path.name)
        destination = unique_destination(laptop_root / relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(track.path, destination)
        copied.append((track.path, destination))

    for match in plan.matches:
        choice = choices.get(str(match.laptop.path), ConflictChoice.LAPTOP)
        if choice is ConflictChoice.PHONE:
            shutil.copy2(match.phone.path, match.laptop.path)
            replaced.append((match.phone.path, match.laptop.path))
        elif choice is ConflictChoice.SKIP:
            skipped.append(match.laptop.path)

    return backup, copied, replaced, skipped


def export_merged_library(laptop_root: Path, destination: Path) -> None:
    """Export the complete merged laptop library to a fresh directory."""
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")
    shutil.copytree(laptop_root, destination)

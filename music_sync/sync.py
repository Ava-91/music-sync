from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .direction import SyncDirection
from .models import SyncPlan
from .review import ConflictChoice


@dataclass(slots=True)
class SafeExecutionResult:
    """Authoritative result for a non-destructive Safe-mode execution."""

    copied: list[tuple[Path, Path]] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    backup: Path | None = None

    @property
    def status(self) -> str:
        if (self.failures or self.blocked) and self.copied:
            return "PARTIAL"
        if self.failures:
            return "FAILED"
        if self.blocked:
            return "BLOCKED"
        return "SUCCESS"


def make_backup(root: Path, backup_root: Path) -> Path:
    """Create a timestamped copy of a library before changing it."""
    root = root.resolve()
    backup_root = backup_root.resolve()
    if root == backup_root or root.is_relative_to(backup_root) or backup_root.is_relative_to(root):
        raise ValueError("Backup location must be outside the library being backed up.")
    if not root.is_dir():
        raise FileNotFoundError(f"Library not found: {root}")
    backup_root.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
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


def _source_only(plan: SyncPlan, direction: SyncDirection):
    source = direction.source.resolve()
    if plan.library_a_root and source == plan.library_a_root.resolve():
        return list(plan.library_a_only)
    if plan.library_b_root and source == plan.library_b_root.resolve():
        return list(plan.library_b_only)
    raise ValueError("The sync plan does not match the selected Library A/B direction.")


def execute_safe(plan: SyncPlan, direction: SyncDirection, backup_root: Path) -> SafeExecutionResult:
    """Copy only source-only tracks without deleting or overwriting destination files."""
    source = direction.source.resolve()
    destination = direction.destination.resolve()
    if source == destination:
        raise ValueError("Safe sync requires different source and destination directories.")
    if not source.is_dir() or not destination.is_dir():
        raise FileNotFoundError("Safe sync requires existing source and destination directories.")

    result = SafeExecutionResult()
    candidates = _source_only(plan, direction)
    planned: list[tuple[Path, Path]] = []
    for track in candidates:
        track_path = track.path.resolve()
        try:
            relative = track_path.relative_to(source)
        except ValueError:
            result.blocked.append(f"Track is outside the selected source library: {track.path}")
            continue
        target = destination / relative
        if target.exists():
            result.skipped.append(target)
            continue
        planned.append((track_path, target))

    if not planned:
        return result

    result.backup = make_backup(destination, backup_root)
    for source_path, target in planned:
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target)
            result.copied.append((source_path, target))
        except OSError as exc:
            result.failures.append(f"Could not copy {source_path} to {target}: {exc}")

    return result


# Compatibility wrappers retained during the Library A/B migration.
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
    """Export the complete merged library to a fresh directory."""
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")
    shutil.copytree(laptop_root, destination)

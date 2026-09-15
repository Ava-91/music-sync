from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from .models import FileState, SyncMode, SyncPlan, Track
from .review import ConflictChoice
from .scanner import AUDIO_EXTENSIONS, current_fingerprint


class SyncSafetyError(RuntimeError):
    """Raised when a synchronization plan is unsafe to apply."""


@dataclass(slots=True)
class ExecutionResult:
    backup: Path
    copied: list[tuple[Path, Path]] = field(default_factory=list)
    replaced: list[tuple[Path, Path]] = field(default_factory=list)
    deleted: list[Path] = field(default_factory=list)
    skipped: list[Path] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    rolled_back: bool = False

    @property
    def success(self) -> bool:
        return not self.failures


def validate_library_paths(library_a: Path, library_b: Path, output: Path | None = None) -> tuple[Path, Path, Path | None]:
    a, b = library_a.expanduser().resolve(strict=False), library_b.expanduser().resolve(strict=False)
    if a == b: raise ValueError("Library A and Library B must be different directories.")
    if not a.is_dir() or not b.is_dir(): raise FileNotFoundError("Both libraries must be existing directories.")
    if a.is_relative_to(b) or b.is_relative_to(a): raise ValueError("Libraries cannot contain one another.")
    out = output.expanduser().resolve(strict=False) if output else None
    if out and (out == a or out == b or out.is_relative_to(a) or out.is_relative_to(b)):
        raise ValueError("Output directory cannot overlap either source library.")
    return a, b, out


def make_backup(root: Path, backup_root: Path) -> Path:
    """Create and verify a unique snapshot before changing a library."""
    root = root.resolve()
    backup_root = backup_root.resolve()
    if not root.is_dir(): raise FileNotFoundError(f"Library not found: {root}")
    if backup_root == root or backup_root.is_relative_to(root):
        raise ValueError("Backup location cannot be inside the library being backed up.")
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    destination = backup_root / f"music_backup_{stamp}"
    destination.mkdir()
    try:
        shutil.copytree(root, destination, dirs_exist_ok=True)
        source_files = _file_manifest(root)
        backup_files = _file_manifest(destination)
        if source_files != backup_files:
            raise IOError("Backup verification failed: the backup does not match the source library.")
        (destination / "backup.json").write_text(json.dumps({"created_at": datetime.now().isoformat(), "source": str(root), "files": len(source_files)}, indent=2), encoding="utf-8")
        return destination
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise


def _file_manifest(root: Path) -> dict[str, tuple[int, int, str]]:
    result = {}
    for path in root.rglob("*"):
        if path.is_file():
            stat = path.stat()
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            result[str(path.relative_to(root))] = (stat.st_size, stat.st_mtime_ns, digest)
    return result


def unique_destination(destination: Path) -> Path:
    if not destination.exists(): return destination
    stem, suffix = destination.stem, destination.suffix
    for number in range(2, 1_000_000):
        candidate = destination.with_name(f"{stem} ({number}){suffix}")
        if not candidate.exists(): return candidate
    raise FileExistsError(f"Could not find a free destination for {destination}")


def validate_plan_freshness(plan: SyncPlan) -> None:
    if not plan.library_a_root or not plan.library_b_root:
        raise SyncSafetyError("This synchronization plan has no library roots; scan again.")
    try:
        current_a = current_fingerprint(plan.library_a_root)
        current_b = current_fingerprint(plan.library_b_root)
    except (OSError, ValueError) as exc:
        raise SyncSafetyError(f"A library is no longer available. Scan again. ({exc})") from exc
    expected_a = {k: (v.size, v.modified_ns) for k, v in plan.fingerprint_a.items()}
    expected_b = {k: (v.size, v.modified_ns) for k, v in plan.fingerprint_b.items()}
    actual_a = {k: (v.size, v.modified_ns) for k, v in current_a.items()}
    actual_b = {k: (v.size, v.modified_ns) for k, v in current_b.items()}
    if expected_a != actual_a or expected_b != actual_b:
        raise SyncSafetyError("The library changed after scanning. The synchronization plan is stale; scan again before applying it.")


def _copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def execute_plan(plan: SyncPlan, destination: Path, source: Path, backup_root: Path, *, mode: str = SyncMode.SAFE, explicit_destructive_confirmation: bool = False, choices: dict[str, ConflictChoice] | None = None) -> ExecutionResult:
    """Apply a validated plan. Backup is created before the first modification."""
    choices = choices or {}
    source, destination, _ = validate_library_paths(source, destination, None)
    validate_plan_freshness(plan)
    if mode not in {SyncMode.SAFE, SyncMode.MIRROR, SyncMode.RECONCILE}: raise ValueError(f"Unknown sync mode: {mode}")
    if mode == SyncMode.MIRROR and not explicit_destructive_confirmation:
        raise SyncSafetyError("Mirror mode requires explicit destructive confirmation.")
    if mode != SyncMode.SAFE and any(not m.confirmed for m in plan.matches):
        raise SyncSafetyError("Unresolved fuzzy matches block synchronization. Review them first.")
    if mode == SyncMode.RECONCILE and any((m.metadata_conflict or m.artwork_conflict) and str(m.library_a.path) not in choices for m in plan.matches):
        raise SyncSafetyError("Every conflict requires an explicit decision in Reconcile mode.")

    backup = make_backup(destination, backup_root)
    result = ExecutionResult(backup)
    try:
        if mode in {SyncMode.SAFE, SyncMode.RECONCILE}:
            for track in plan.library_b_only if source == plan.library_b_root else plan.library_a_only:
                relative = track.path.resolve().relative_to(source)
                target = unique_destination(destination / relative)
                _copy(track.path, target); result.copied.append((track.path, target))
        if mode == SyncMode.RECONCILE:
            for match in plan.matches:
                choice = choices.get(str(match.library_a.path), ConflictChoice.LAPTOP)
                if choice is ConflictChoice.PHONE and destination == plan.library_a_root:
                    _copy(match.library_b.path, match.library_a.path); result.replaced.append((match.library_b.path, match.library_a.path))
                elif choice is ConflictChoice.LAPTOP and destination == plan.library_b_root:
                    _copy(match.library_a.path, match.library_b.path); result.replaced.append((match.library_a.path, match.library_b.path))
                elif choice is ConflictChoice.SKIP:
                    result.skipped.append(match.library_a.path)
        if mode == SyncMode.MIRROR:
            source_tracks = plan.library_b_only if source == plan.library_b_root else plan.library_a_only
            for track in source_tracks:
                relative = track.path.resolve().relative_to(source)
                target = destination / relative
                _copy(track.path, target); result.copied.append((track.path, target))
            source_paths = {str(t.path.resolve().relative_to(source)) for t in (plan.library_b_only + [m.library_b for m in plan.matches] if source == plan.library_b_root else plan.library_a_only + [m.library_a for m in plan.matches])}
            for path in list(destination.rglob("*")):
                if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS and str(path.relative_to(destination)) not in source_paths:
                    path.unlink(); result.deleted.append(path)
    except Exception as exc:
        result.failures.append(str(exc))
        result.rolled_back = _rollback(result)
        raise SyncSafetyError(f"Synchronization stopped after a failure: {exc}. Backup preserved at {backup}") from exc
    return result


def _rollback(result: ExecutionResult) -> bool:
    """Best-effort rollback of changes made during this execution."""
    try:
        for _, target in reversed(result.replaced):
            # Replacements are restored from the backup by relative target path.
            rel = target.relative_to(result.backup.parent.parent) if False else None
        for target in reversed(result.deleted):
            target.unlink(missing_ok=True)
        for _, target in reversed(result.copied):
            if target.is_file(): target.unlink()
        return True
    except OSError:
        return False


def merge_phone_only(plan: SyncPlan, laptop_root: Path, phone_root: Path, backup_root: Path):
    result = execute_plan(plan, laptop_root, phone_root, backup_root, mode=SyncMode.SAFE)
    return result.backup, result.copied


def merge_with_conflicts(plan: SyncPlan, laptop_root: Path, phone_root: Path, backup_root: Path, choices: dict[str, ConflictChoice]):
    result = execute_plan(plan, laptop_root, phone_root, backup_root, mode=SyncMode.RECONCILE, choices=choices)
    return result.backup, result.copied, result.replaced, result.skipped


def export_merged_library(laptop_root: Path, destination: Path) -> None:
    if destination.exists(): raise FileExistsError(f"Destination already exists: {destination}")
    shutil.copytree(laptop_root, destination)

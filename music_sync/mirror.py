from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .backup import create_verified_backup
from .direction import MasterLibrary, SyncDirection
from .freshness import validate_plan_freshness
from .models import Match, SyncPlan, Track
from .path_safety import validate_backup_root, validate_library_pair
from .transaction import FileOperation, OperationKind, execute_transaction


class MirrorAction(str, Enum):
    COPY = "copy"
    REPLACE = "replace"
    DELETE = "delete"


class MirrorConfirmationError(RuntimeError):
    """Raised when Mirror execution is not explicitly confirmed."""


@dataclass(frozen=True, slots=True)
class MirrorOperation:
    action: MirrorAction
    source: Path | None
    destination: Path


@dataclass(slots=True)
class MirrorPreview:
    operations: list[MirrorOperation] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)

    @property
    def deletions(self) -> list[MirrorOperation]:
        return [operation for operation in self.operations if operation.action is MirrorAction.DELETE]

    @property
    def replacements(self) -> list[MirrorOperation]:
        return [operation for operation in self.operations if operation.action is MirrorAction.REPLACE]

    @property
    def copies(self) -> list[MirrorOperation]:
        return [operation for operation in self.operations if operation.action is MirrorAction.COPY]


@dataclass(slots=True)
class MirrorResult:
    copied: list[tuple[Path, Path]] = field(default_factory=list)
    replaced: list[tuple[Path, Path]] = field(default_factory=list)
    deleted: list[Path] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    backup: Path | None = None
    rolled_back: bool = False
    rollback_failures: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.rollback_failures:
            return "PARTIAL"
        if self.failures:
            return "FAILED"
        return "SUCCESS"


def _track_relative(track: Track, root: Path) -> Path:
    return track.path.resolve().relative_to(root.resolve())


def _pair_needs_replacement(match: Match) -> bool:
    if not match.library_a.file_hash or not match.library_b.file_hash:
        return True
    return match.library_a.file_hash != match.library_b.file_hash


def build_mirror_preview(plan: SyncPlan, direction: SyncDirection) -> MirrorPreview:
    """Build a read-only Mirror preview after path and freshness validation."""
    library_a, library_b = validate_library_pair(direction.source, direction.destination)
    validate_plan_freshness(plan)
    preview = MirrorPreview()

    source_is_a = direction.master is MasterLibrary.LIBRARY_A
    source_root = library_a if source_is_a else library_b
    destination_root = library_b if source_is_a else library_a
    source_only = plan.library_a_only if source_is_a else plan.library_b_only
    destination_only = plan.library_b_only if source_is_a else plan.library_a_only

    for track in source_only:
        preview.operations.append(
            MirrorOperation(MirrorAction.COPY, track.path.resolve(), destination_root / _track_relative(track, source_root))
        )

    for track in destination_only:
        preview.operations.append(MirrorOperation(MirrorAction.DELETE, None, track.path.resolve()))

    for match in plan.matches:
        source_track = match.library_a if source_is_a else match.library_b
        destination_track = match.library_b if source_is_a else match.library_a
        if not match.confirmed:
            preview.blocked.append(f"Unresolved fuzzy match requires review: {source_track.path}")
            continue
        if _pair_needs_replacement(match):
            preview.operations.append(
                MirrorOperation(MirrorAction.REPLACE, source_track.path.resolve(), destination_track.path.resolve())
            )

    return preview


def execute_mirror(
    plan: SyncPlan,
    direction: SyncDirection,
    backup_root: Path,
    confirmation: str,
) -> MirrorResult:
    """Apply a destructive Mirror plan only after explicit `MIRROR` confirmation."""
    if confirmation != "MIRROR":
        raise MirrorConfirmationError("Mirror execution requires exact confirmation text: MIRROR")

    library_a, library_b = validate_library_pair(direction.source, direction.destination)
    validate_backup_root(backup_root, (direction.destination,))
    validate_plan_freshness(plan)
    preview = build_mirror_preview(plan, direction)
    if preview.blocked:
        raise MirrorConfirmationError("Mirror is blocked until all fuzzy matches are explicitly resolved.")

    destination = library_b if direction.master is MasterLibrary.LIBRARY_A else library_a
    backup = create_verified_backup(destination, backup_root).path
    result = MirrorResult(backup=backup)
    operations = []
    for operation in preview.operations:
        kind = {
            MirrorAction.COPY: OperationKind.COPY,
            MirrorAction.REPLACE: OperationKind.REPLACE,
            MirrorAction.DELETE: OperationKind.DELETE,
        }[operation.action]
        operations.append(FileOperation(kind, operation.source, operation.destination))

    transaction = execute_transaction(operations, {destination: backup})
    for operation in transaction.succeeded:
        if operation.kind is OperationKind.COPY:
            result.copied.append((operation.source, operation.destination))
        elif operation.kind is OperationKind.REPLACE:
            result.replaced.append((operation.source, operation.destination))
        elif operation.kind is OperationKind.DELETE:
            result.deleted.append(operation.destination)
    result.failures.extend(transaction.failures)
    result.rolled_back = transaction.rolled_back
    result.rollback_failures.extend(transaction.rollback_failures)
    return result

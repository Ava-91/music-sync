from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .direction import SyncDirection
from .freshness import validate_plan_freshness
from .models import SyncPlan
from .mirror import MirrorAction, build_mirror_preview
from .path_safety import validate_backup_root, validate_library_pair
from .reconcile import ReconcileDecision, _plan_operations
from .sync import _source_only
from .transaction import FileOperation, OperationKind


@dataclass(frozen=True, slots=True)
class DryRunSummary:
    """A read-only description of what applying a plan would do."""

    add: int
    matched: int
    fuzzy: int
    metadata_conflicts: int
    artwork_conflicts: int
    scan_errors: int = 0

    @property
    def changes(self) -> int:
        return self.add + self.metadata_conflicts + self.artwork_conflicts


@dataclass(slots=True)
class DryRunResult:
    mode: str
    operations: list[FileOperation] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.blocked:
            return "BLOCKED"
        return "SUCCESS"


def summarize(plan: SyncPlan, scan_errors: int = 0) -> DryRunSummary:
    """Build a summary without touching either library."""
    return DryRunSummary(
        add=len(plan.phone_only),
        matched=len(plan.matches),
        fuzzy=sum(not match.confirmed for match in plan.matches),
        metadata_conflicts=sum(match.metadata_conflict for match in plan.matches),
        artwork_conflicts=sum(match.artwork_conflict for match in plan.matches),
        scan_errors=scan_errors,
    )


def dry_run_safe(plan: SyncPlan, direction: SyncDirection) -> DryRunResult:
    """Preview Safe-mode copies without creating backups or modifying files."""
    source, destination = validate_library_pair(direction.source, direction.destination)
    validate_plan_freshness(plan)
    operations: list[FileOperation] = []
    skipped: list[str] = []
    blocked: list[str] = []

    for track in _source_only(plan, SyncDirection(source, destination, direction.master)):
        try:
            relative = track.path.resolve().relative_to(source)
        except ValueError:
            blocked.append(f"Track is outside the selected source library: {track.path}")
            continue
        target = destination / relative
        if target.exists():
            skipped.append(str(target))
        else:
            operations.append(FileOperation(OperationKind.COPY, track.path.resolve(), target))

    return DryRunResult("safe", operations, skipped, blocked)


def dry_run_reconcile(
    plan: SyncPlan,
    decisions: dict[str, ReconcileDecision],
    backup_root: Path,
) -> DryRunResult:
    """Preview Reconcile operations without creating backups or modifying files."""
    library_a, library_b = validate_library_pair(plan.library_a_root, plan.library_b_root)
    validate_backup_root(backup_root, (library_a, library_b))
    validate_plan_freshness(plan)
    operations, blocked, skipped = _plan_operations(plan, decisions)
    return DryRunResult("reconcile", operations, skipped, blocked)


def dry_run_mirror(plan: SyncPlan, direction: SyncDirection) -> DryRunResult:
    """Preview Mirror operations without confirmation, backup, or modification."""
    preview = build_mirror_preview(plan, direction)
    operations = [
        FileOperation(
            {
                MirrorAction.COPY: OperationKind.COPY,
                MirrorAction.REPLACE: OperationKind.REPLACE,
                MirrorAction.DELETE: OperationKind.DELETE,
            }[operation.action],
            operation.source,
            operation.destination,
        )
        for operation in preview.operations
    ]
    return DryRunResult("mirror", operations, blocked=preview.blocked)

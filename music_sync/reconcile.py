from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .backup import create_verified_backup
from .freshness import validate_plan_freshness
from .models import SyncPlan
from .path_safety import validate_backup_root, validate_library_pair
from .transaction import FileOperation, OperationKind, execute_transaction


class ReconcileDecision(str, Enum):
    COPY_A_TO_B = "copy_a_to_b"
    COPY_B_TO_A = "copy_b_to_a"
    KEEP_A = "keep_a"
    KEEP_B = "keep_b"
    SKIP = "skip"


@dataclass(slots=True)
class ReconcileResult:
    copied: list[tuple[Path, Path]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    blocked: list[str] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)
    backups: dict[str, Path] = field(default_factory=dict)
    rolled_back: bool = False
    rollback_failures: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.rollback_failures:
            return "PARTIAL"
        if self.failures:
            return "FAILED"
        if self.blocked and not self.copied:
            return "BLOCKED"
        if self.blocked:
            return "PARTIAL"
        return "SUCCESS"


def _relative(path: Path, root: Path) -> Path:
    try:
        return path.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"Track path is outside its library: {path}") from exc


def _key(prefix: str, path: Path) -> str:
    return f"{prefix}:{path}"


def _plan_operations(plan: SyncPlan, decisions: dict[str, ReconcileDecision]):
    operations: list[FileOperation] = []
    blocked: list[str] = []
    skipped: list[str] = []

    for track in plan.library_a_only:
        key = _key("a-only", track.path)
        decision = decisions.get(key)
        if decision is ReconcileDecision.COPY_A_TO_B:
            relative = _relative(track.path, plan.library_a_root)
            operations.append(FileOperation(OperationKind.COPY, track.path.resolve(), plan.library_b_root.resolve() / relative))
        elif decision is ReconcileDecision.SKIP:
            skipped.append(key)
        else:
            blocked.append(f"No explicit decision for {key}")

    for track in plan.library_b_only:
        key = _key("b-only", track.path)
        decision = decisions.get(key)
        if decision is ReconcileDecision.COPY_B_TO_A:
            relative = _relative(track.path, plan.library_b_root)
            operations.append(FileOperation(OperationKind.COPY, track.path.resolve(), plan.library_a_root.resolve() / relative))
        elif decision is ReconcileDecision.SKIP:
            skipped.append(key)
        else:
            blocked.append(f"No explicit decision for {key}")

    for match in plan.matches:
        key = _key("match", match.library_a.path)
        requires_decision = not match.confirmed or match.metadata_conflict or match.artwork_conflict
        if not requires_decision:
            continue
        decision = decisions.get(key)
        if decision is ReconcileDecision.KEEP_A:
            _relative(match.library_a.path, plan.library_a_root)
            _relative(match.library_b.path, plan.library_b_root)
            operations.append(FileOperation(OperationKind.REPLACE, match.library_a.path.resolve(), match.library_b.path.resolve()))
        elif decision is ReconcileDecision.KEEP_B:
            _relative(match.library_b.path, plan.library_b_root)
            _relative(match.library_a.path, plan.library_a_root)
            operations.append(FileOperation(OperationKind.REPLACE, match.library_b.path.resolve(), match.library_a.path.resolve()))
        elif decision is ReconcileDecision.SKIP:
            skipped.append(key)
        else:
            blocked.append(f"No explicit decision for {key}")

    return operations, blocked, skipped


def execute_reconcile(plan: SyncPlan, decisions: dict[str, ReconcileDecision], backup_root: Path) -> ReconcileResult:
    """Apply only explicit Reconcile decisions; never delete files."""
    library_a, library_b = validate_library_pair(plan.library_a_root, plan.library_b_root)
    validate_backup_root(backup_root, (library_a, library_b))
    validate_plan_freshness(plan)

    operations, blocked, skipped = _plan_operations(plan, decisions)
    result = ReconcileResult(blocked=blocked, skipped=skipped)
    if blocked or not operations:
        return result

    destinations = [operation.destination.resolve() for operation in operations]
    if any(destination.is_relative_to(library_a) for destination in destinations):
        result.backups["library_a"] = create_verified_backup(library_a, backup_root).path
    if any(destination.is_relative_to(library_b) for destination in destinations):
        result.backups["library_b"] = create_verified_backup(library_b, backup_root).path

    backup_map = {}
    if "library_a" in result.backups:
        backup_map[library_a] = result.backups["library_a"]
    if "library_b" in result.backups:
        backup_map[library_b] = result.backups["library_b"]
    transaction = execute_transaction(operations, backup_map)
    result.copied = [(operation.source, operation.destination) for operation in transaction.succeeded if operation.source]
    result.failures.extend(transaction.failures)
    result.rolled_back = transaction.rolled_back
    result.rollback_failures.extend(transaction.rollback_failures)
    return result

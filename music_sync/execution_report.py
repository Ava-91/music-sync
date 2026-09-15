from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ReportStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    BLOCKED = "BLOCKED"


@dataclass(slots=True)
class ExecutionReport:
    mode: str
    final_status: ReportStatus
    planned: int = 0
    attempted: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    copied: list[str] = field(default_factory=list)
    replaced: list[str] = field(default_factory=list)
    deleted: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    backups: list[str] = field(default_factory=list)
    rolled_back: bool = False
    rollback_failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["final_status"] = self.final_status.value
        return data

    def save_json(self, destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.to_dict(), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return destination


def report_from_safe(result) -> ExecutionReport:
    return ExecutionReport(
        mode="safe",
        final_status=ReportStatus(result.status),
        planned=len(result.copied) + len(result.skipped) + len(result.blocked) + len(result.failures),
        attempted=len(result.copied) + len(result.failures),
        succeeded=len(result.copied),
        failed=len(result.failures),
        skipped=len(result.skipped),
        copied=[f"{source} -> {destination}" for source, destination in result.copied],
        conflicts=list(result.blocked),
        errors=list(result.failures) + list(result.rollback_failures),
        backups=[str(result.backup)] if result.backup else [],
        rolled_back=result.rolled_back,
        rollback_failures=list(result.rollback_failures),
    )


def report_from_reconcile(result) -> ExecutionReport:
    blocked = list(result.blocked)
    return ExecutionReport(
        mode="reconcile",
        final_status=ReportStatus(result.status),
        planned=len(result.copied) + len(result.replaced) + len(result.skipped) + len(blocked) + len(result.failures),
        attempted=len(result.copied) + len(result.replaced) + len(result.failures),
        succeeded=len(result.copied) + len(result.replaced),
        failed=len(result.failures),
        skipped=len(result.skipped),
        copied=[f"{source} -> {destination}" for source, destination in result.copied],
        replaced=[f"{source} -> {destination}" for source, destination in result.replaced],
        conflicts=blocked,
        errors=list(result.failures) + list(result.rollback_failures),
        backups=[str(path) for path in result.backups.values()],
        rolled_back=result.rolled_back,
        rollback_failures=list(result.rollback_failures),
    )


def report_from_mirror(result) -> ExecutionReport:
    return ExecutionReport(
        mode="mirror",
        final_status=ReportStatus(result.status),
        planned=len(result.copied) + len(result.replaced) + len(result.deleted) + len(result.failures),
        attempted=len(result.copied) + len(result.replaced) + len(result.deleted) + len(result.failures),
        succeeded=len(result.copied) + len(result.replaced) + len(result.deleted),
        failed=len(result.failures),
        copied=[f"{source} -> {destination}" for source, destination in result.copied],
        replaced=[f"{source} -> {destination}" for source, destination in result.replaced],
        deleted=[str(path) for path in result.deleted],
        errors=list(result.failures) + list(result.rollback_failures),
        backups=[str(result.backup)] if result.backup else [],
        rolled_back=result.rolled_back,
        rollback_failures=list(result.rollback_failures),
    )


def report_from_transaction(result, mode: str = "transaction") -> ExecutionReport:
    copied = [f"{operation.source} -> {operation.destination}" for operation in result.succeeded if operation.source and operation.kind.value == "copy"]
    replaced = [f"{operation.source} -> {operation.destination}" for operation in result.succeeded if operation.source and operation.kind.value == "replace"]
    deleted = [str(operation.destination) for operation in result.succeeded if operation.kind.value == "delete"]
    return ExecutionReport(
        mode=mode,
        final_status=ReportStatus(result.status),
        planned=result.attempted,
        attempted=result.attempted,
        succeeded=len(result.succeeded),
        failed=len(result.failures),
        copied=copied,
        replaced=replaced,
        deleted=deleted,
        errors=list(result.failures) + list(result.rollback_failures),
        rolled_back=result.rolled_back,
        rollback_failures=list(result.rollback_failures),
    )

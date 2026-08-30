from __future__ import annotations

from dataclasses import dataclass

from .models import SyncPlan


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

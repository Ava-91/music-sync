from __future__ import annotations

from .models import FileState, SyncPlan
from .scanner import current_fingerprint


class StalePlanError(RuntimeError):
    """Raised when a synchronization plan no longer describes the libraries."""


def _lightweight_fingerprint(fingerprint: dict[str, FileState]) -> dict[str, tuple[int, int]]:
    return {path: (state.size, state.modified_ns) for path, state in fingerprint.items()}


def validate_plan_freshness(plan: SyncPlan) -> None:
    """Block execution unless both scanned libraries still match their plan fingerprints."""
    if not plan.library_a_root or not plan.library_b_root:
        raise StalePlanError("The synchronization plan has no library roots. Scan both libraries again.")
    if plan.fingerprint_a is None or plan.fingerprint_b is None:
        raise StalePlanError("The synchronization plan has no filesystem fingerprints. Scan both libraries again.")

    try:
        current_a = current_fingerprint(plan.library_a_root)
        current_b = current_fingerprint(plan.library_b_root)
    except (OSError, ValueError) as exc:
        raise StalePlanError(f"A library is unavailable. Scan both libraries again. ({exc})") from exc

    if _lightweight_fingerprint(plan.fingerprint_a) != _lightweight_fingerprint(current_a):
        raise StalePlanError("Library A changed after scanning. Scan both libraries again before applying the plan.")
    if _lightweight_fingerprint(plan.fingerprint_b) != _lightweight_fingerprint(current_b):
        raise StalePlanError("Library B changed after scanning. Scan both libraries again before applying the plan.")

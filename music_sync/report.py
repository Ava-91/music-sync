from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class SyncReport:
    """Serializable record of a scan/merge operation."""

    created_at: str
    library_a: str
    library_b: str
    added: int
    replaced: int
    skipped: int
    matched: int
    fuzzy: int
    metadata_conflicts: int
    artwork_conflicts: int
    scan_errors: int

    def to_dict(self) -> dict:
        return asdict(self)


def make_report(*, library_a: Path, library_b: Path, added: int, replaced: int, skipped: int,
                matched: int, fuzzy: int, metadata_conflicts: int, artwork_conflicts: int,
                scan_errors: int) -> SyncReport:
    return SyncReport(
        created_at=datetime.now().isoformat(timespec="seconds"),
        library_a=str(library_a),
        library_b=str(library_b),
        added=added,
        replaced=replaced,
        skipped=skipped,
        matched=matched,
        fuzzy=fuzzy,
        metadata_conflicts=metadata_conflicts,
        artwork_conflicts=artwork_conflicts,
        scan_errors=scan_errors,
    )


def save_json(report: SyncReport, destination: Path) -> Path:
    """Write an indented UTF-8 JSON report and return its path."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return destination

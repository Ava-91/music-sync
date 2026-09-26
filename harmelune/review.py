from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import Match


class ConflictChoice(str, Enum):
    LAPTOP = "laptop"
    PHONE = "phone"
    SKIP = "skip"


@dataclass(slots=True)
class ConflictDecision:
    match: Match
    choice: ConflictChoice = ConflictChoice.LAPTOP


def conflict_matches(matches: list[Match]) -> list[Match]:
    """Return matches that have metadata or artwork differences."""
    return [m for m in matches if m.metadata_conflict or m.artwork_conflict]


def apply_choices(matches: list[Match], choices: dict[str, ConflictChoice]) -> dict[str, ConflictChoice]:
    """Normalize user choices keyed by the laptop path string."""
    return {str(match.laptop.path): choices.get(str(match.laptop.path), ConflictChoice.LAPTOP) for match in matches}

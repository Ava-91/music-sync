from __future__ import annotations

from dataclasses import dataclass

from .matcher import _artwork_values, _match_reasons, normalize
from .models import Match


@dataclass(frozen=True, slots=True)
class MatchExplanation:
    """Human-readable evidence behind a track match."""

    confidence: float
    identity: str
    reasons: tuple[str, ...]
    conflicts: tuple[str, ...]


def _identity(match: Match) -> str:
    if not match.confirmed:
        return "Fuzzy match — review required"
    if match.match_kind == "hash":
        return "Exact match"
    if match.match_kind == "metadata":
        return "Confirmed metadata match"
    if match.match_kind == "filename":
        return "Confirmed filename match"
    if match.match_kind == "fuzzy":
        return "Confirmed fuzzy match"
    return "Exact match" if match.confidence >= 1.0 else "Confirmed match"


def explain_match(match: Match) -> MatchExplanation:
    left, right = match.library_a, match.library_b
    reasons = tuple(match.reasons) or _match_reasons(left, right, match.match_kind, match.confidence)
    conflicts: list[str] = []

    for label, a, b in (("Title", left.title, right.title), ("Artist", left.artist, right.artist), ("Album", left.album, right.album)):
        if a and b and normalize(a) != normalize(b):
            conflicts.append(f"{label} differs")

    left_art, right_art = _artwork_values(left), _artwork_values(right)
    if left_art != right_art:
        if left_art and right_art:
            conflicts.append("Embedded artwork differs")
        elif left_art:
            conflicts.append("Library B is missing embedded artwork")
        else:
            conflicts.append("Library A is missing embedded artwork")

    return MatchExplanation(match.confidence, _identity(match), reasons, tuple(conflicts))

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher

from .matcher import normalize
from .models import Match, Track


@dataclass(frozen=True, slots=True)
class MatchExplanation:
    """Human-readable evidence behind a track match."""

    confidence: float
    identity: str
    reasons: tuple[str, ...]
    conflicts: tuple[str, ...]


def explain_match(match: Match) -> MatchExplanation:
    left, right = match.laptop, match.phone
    reasons: list[str] = []
    conflicts: list[str] = []

    if left.file_hash and right.file_hash and left.file_hash == right.file_hash:
        reasons.append("Byte-identical SHA-256")
    else:
        title_score = SequenceMatcher(None, normalize(left.display_title), normalize(right.display_title)).ratio()
        artist_score = SequenceMatcher(None, normalize(left.artist), normalize(right.artist)).ratio() if left.artist or right.artist else 1.0
        reasons.append(f"Title similarity: {title_score:.0%}")
        reasons.append(f"Artist similarity: {artist_score:.0%}")
        if left.duration is not None and right.duration is not None:
            delta = abs(left.duration - right.duration)
            reasons.append(f"Duration difference: {delta:.2f}s")

    for label, a, b in (("Title", left.title, right.title), ("Artist", left.artist, right.artist), ("Album", left.album, right.album)):
        if a and b and normalize(a) != normalize(b):
            conflicts.append(f"{label} differs")
    if left.artwork_hashes != right.artwork_hashes:
        if left.artwork_hashes and right.artwork_hashes:
            conflicts.append("Embedded artwork differs")
        elif left.artwork_hashes:
            conflicts.append("Phone is missing embedded artwork")
        else:
            conflicts.append("Laptop is missing embedded artwork")

    identity = "Exact match" if match.confirmed and match.confidence >= 1.0 else "Confirmed match" if match.confirmed else "Fuzzy match — review required"
    return MatchExplanation(match.confidence, identity, tuple(reasons), tuple(conflicts))

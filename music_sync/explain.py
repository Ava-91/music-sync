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


def _artwork_values(track: Track) -> tuple[str, ...]:
    """Same representation the matcher uses for artwork comparison."""
    return track.artwork_hashes or ((track.artwork_hash,) if track.artwork_hash else ())


def explain_match(match: Match) -> MatchExplanation:
    left, right = match.library_a, match.library_b
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
        name_score = SequenceMatcher(None, normalize(left.path.stem), normalize(right.path.stem)).ratio()
        if name_score >= 0.8:
            reasons.append(f"Filename similarity: {name_score:.0%}")

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

    identity = "Exact match" if match.confirmed and match.confidence >= 1.0 else "Confirmed match" if match.confirmed else "Fuzzy match — review required"
    return MatchExplanation(match.confidence, identity, tuple(reasons), tuple(conflicts))

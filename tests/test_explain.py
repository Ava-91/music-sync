from pathlib import Path

from music_sync.explain import explain_match
from music_sync.models import Match, Track


def test_exact_hash_is_explained():
    left = Track(path=Path("a.mp3"), side="a", title="Song", file_hash="abc")
    right = Track(path=Path("b.mp3"), side="b", title="Song", file_hash="abc")
    explanation = explain_match(Match(left, right, 1.0, confirmed=True))
    assert explanation.identity == "Exact match"
    assert "Byte-identical SHA-256" in explanation.reasons


def test_metadata_and_artwork_conflicts_are_explained():
    left = Track(path=Path("a.mp3"), side="a", title="New", artist="Artist", artwork_hashes=("a",))
    right = Track(path=Path("b.mp3"), side="b", title="Old", artist="Artist", artwork_hashes=("b",))
    explanation = explain_match(Match(left, right, 0.9, confirmed=True))
    assert "Title differs" in explanation.conflicts
    assert "Embedded artwork differs" in explanation.conflicts


def test_missing_artwork_uses_library_a_b_labels():
    left = Track(path=Path("a.mp3"), side="a", title="Song", artwork_hashes=("hash1",))
    right = Track(path=Path("b.mp3"), side="b", title="Song")
    explanation = explain_match(Match(left, right, 0.9, confirmed=True))
    assert "Library B is missing embedded artwork" in explanation.conflicts
    assert "Laptop" not in " ".join(explanation.conflicts)
    assert "Phone" not in " ".join(explanation.conflicts)

    left2 = Track(path=Path("a2.mp3"), side="a", title="Song")
    right2 = Track(path=Path("b2.mp3"), side="b", title="Song", artwork_hashes=("hash2",))
    explanation2 = explain_match(Match(left2, right2, 0.9, confirmed=True))
    assert "Library A is missing embedded artwork" in explanation2.conflicts


def test_artwork_hash_fallback_matches_matcher_representation():
    """explain must use the same artwork_hash fallback the matcher uses."""
    left = Track(path=Path("a.mp3"), side="a", title="Song", artwork_hash="legacy-hash")
    right = Track(path=Path("b.mp3"), side="b", title="Song", artwork_hash="other-hash")
    explanation = explain_match(Match(left, right, 0.9, confirmed=True))
    assert "Embedded artwork differs" in explanation.conflicts

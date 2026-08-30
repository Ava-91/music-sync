from pathlib import Path

from music_sync.explain import explain_match
from music_sync.models import Match, Track


def test_exact_hash_is_explained():
    left = Track(path=Path("a.mp3"), side="laptop", title="Song", file_hash="abc")
    right = Track(path=Path("b.mp3"), side="phone", title="Song", file_hash="abc")
    explanation = explain_match(Match(left, right, 1.0, confirmed=True))
    assert explanation.identity == "Exact match"
    assert "Byte-identical SHA-256" in explanation.reasons


def test_metadata_and_artwork_conflicts_are_explained():
    left = Track(path=Path("a.mp3"), side="laptop", title="New", artist="Artist", artwork_hashes=("a",))
    right = Track(path=Path("b.mp3"), side="phone", title="Old", artist="Artist", artwork_hashes=("b",))
    explanation = explain_match(Match(left, right, 0.9, confirmed=True))
    assert "Title differs" in explanation.conflicts
    assert "Embedded artwork differs" in explanation.conflicts

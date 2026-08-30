from pathlib import Path

from music_sync.models import Match, Track
from music_sync.review import ConflictChoice, apply_choices, conflict_matches


def track(path: str, side: str, *, title: str = "Song", artwork: str | None = None) -> Track:
    return Track(path=Path(path), side=side, title=title, artist="Artist", album="Album", artwork_hash=artwork)


def test_conflict_matches_filters_clean_matches():
    clean = Match(track("a.mp3", "laptop"), track("b.mp3", "phone"), 1.0)
    conflict = Match(track("c.mp3", "laptop", artwork="one"), track("d.mp3", "phone", artwork="two"), 1.0, artwork_conflict=True)
    assert conflict_matches([clean, conflict]) == [conflict]


def test_apply_choices_defaults_to_laptop():
    match = Match(track("a.mp3", "laptop"), track("b.mp3", "phone"), 1.0, metadata_conflict=True)
    result = apply_choices([match], {})
    assert result[str(match.laptop.path)] is ConflictChoice.LAPTOP


def test_apply_choices_keeps_explicit_choice():
    match = Match(track("a.mp3", "laptop"), track("b.mp3", "phone"), 1.0, artwork_conflict=True)
    result = apply_choices([match], {str(match.laptop.path): ConflictChoice.PHONE})
    assert result[str(match.laptop.path)] is ConflictChoice.PHONE

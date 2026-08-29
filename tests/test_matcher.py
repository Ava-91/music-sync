from pathlib import Path

from music_sync.matcher import build_plan
from music_sync.models import ScanResult, Track


def track(side: str, name: str, title: str, artist: str = "Billie Eilish", album: str = "Album") -> Track:
    return Track(
        path=Path(name),
        side=side,
        title=title,
        artist=artist,
        album=album,
        duration=200.0,
        artwork_hash=f"art-{side}-{name}",
    )


def test_phone_only_track_is_detected() -> None:
    laptop = ScanResult("laptop", Path("laptop"), [track("laptop", "one.mp3", "One")])
    phone = ScanResult("phone", Path("phone"), [track("phone", "one.mp3", "One"), track("phone", "two.mp3", "Two")])

    plan = build_plan(laptop, phone)

    assert len(plan.matches) == 1
    assert [item.path.name for item in plan.phone_only] == ["two.mp3"]


def test_laptop_wins_artwork_conflict() -> None:
    laptop = ScanResult("laptop", Path("laptop"), [track("laptop", "one.mp3", "One")])
    phone = ScanResult("phone", Path("phone"), [track("phone", "one.mp3", "One")])

    plan = build_plan(laptop, phone)

    assert plan.matches[0].artwork_conflict is True
    assert not plan.phone_only


def test_renamed_metadata_with_same_filename_is_matched() -> None:
    laptop = ScanResult("laptop", Path("laptop"), [track("laptop", "one.mp3", "My Custom Title")])
    phone = ScanResult("phone", Path("phone"), [track("phone", "one.mp3", "Original Title")])

    plan = build_plan(laptop, phone)

    assert len(plan.matches) == 1
    assert not plan.phone_only
    assert plan.matches[0].metadata_conflict is True

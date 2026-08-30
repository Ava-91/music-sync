from pathlib import Path

from music_sync.fuzzy_ui import apply_fuzzy_decisions
from music_sync.models import Match, SyncPlan, Track


def make_track(name: str, side: str) -> Track:
    return Track(path=Path(name), side=side, title=name, artist="Artist", album="Album")


def test_confirmed_fuzzy_match_becomes_safe_match():
    laptop = make_track("laptop.mp3", "laptop")
    phone = make_track("phone.mp3", "phone")
    match = Match(laptop, phone, 0.91, confirmed=False)
    plan = apply_fuzzy_decisions(SyncPlan(matches=[match]), {str(laptop.path): True})
    assert len(plan.matches) == 1
    assert plan.matches[0].confirmed is True
    assert plan.phone_only == []


def test_rejected_fuzzy_match_becomes_phone_only():
    laptop = make_track("laptop.mp3", "laptop")
    phone = make_track("phone.mp3", "phone")
    match = Match(laptop, phone, 0.91, confirmed=False)
    plan = apply_fuzzy_decisions(SyncPlan(matches=[match]), {str(laptop.path): False})
    assert plan.matches == []
    assert plan.phone_only == [phone]


def test_unreviewed_fuzzy_match_remains_unconfirmed():
    laptop = make_track("laptop.mp3", "laptop")
    phone = make_track("phone.mp3", "phone")
    match = Match(laptop, phone, 0.91, confirmed=False)
    plan = apply_fuzzy_decisions(SyncPlan(matches=[match]), {})
    assert plan.matches == [match]
    assert plan.matches[0].confirmed is False

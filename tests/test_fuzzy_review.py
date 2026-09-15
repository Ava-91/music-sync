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


def test_unreviewed_fuzzy_match_does_not_drop_existing_matches():
    fuzzy_left = make_track("fuzzy.mp3", "laptop")
    fuzzy_right = make_track("fuzzy-copy.mp3", "phone")
    trusted_left = make_track("trusted.mp3", "laptop")
    trusted_right = make_track("trusted-copy.mp3", "phone")
    fuzzy = Match(fuzzy_left, fuzzy_right, 0.91, confirmed=False)
    trusted = Match(trusted_left, trusted_right, 1.0, confirmed=True)

    plan = apply_fuzzy_decisions(SyncPlan(matches=[trusted, fuzzy]), {})

    assert plan.matches == [trusted, fuzzy]
    assert plan.matches[1].confirmed is False

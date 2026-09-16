from pathlib import Path

from music_sync.models import FileState, Match, SyncPlan, Track


def _match() -> Match:
    return Match(Track(Path("a.mp3"), "a"), Track(Path("b.mp3"), "b"), 1.0)


def test_syncplan_accepts_explicit_none_fingerprints():
    plan = SyncPlan(matches=[_match()], fingerprint_a=None, fingerprint_b=None)
    assert plan.fingerprint_a is None
    assert plan.fingerprint_b is None


def test_syncplan_preserves_fingerprint_mappings():
    fingerprint = {"song.mp3": FileState("song.mp3", 1, 2, "hash")}
    plan = SyncPlan(matches=[_match()], fingerprint_a=fingerprint, fingerprint_b=dict(fingerprint))
    assert plan.fingerprint_a == fingerprint
    assert plan.fingerprint_b == fingerprint
    assert plan.fingerprint_a is not fingerprint

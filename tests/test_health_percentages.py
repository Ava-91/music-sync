from pathlib import Path

from harmelune.health import build_health_report
from harmelune.models import ScanResult, Track


def test_health_percentage_uses_stable_integer_first_arithmetic():
    tracks = [
        Track(Path("one.mp3"), "a", title="One", artist="Artist", album="Album", artwork_hash="cover"),
        Track(Path("two.mp3"), "a", title="Two", artist="Artist", album="Album"),
        Track(Path("three.mp3"), "a", title="", artist="Artist", album="Album", artwork_hash="cover2"),
    ]
    report = build_health_report(ScanResult("a", Path("a"), tracks=tracks), ScanResult("b", Path("b")))
    assert report.library_a.metadata_completeness_pct == 200 / 3
    assert report.library_a.artwork_coverage_pct == 200 / 3

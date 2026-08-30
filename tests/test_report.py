from pathlib import Path

from music_sync.report import make_report, save_json


def test_report_round_trips_to_json(tmp_path: Path):
    report = make_report(
        library_a=Path("A"), library_b=Path("B"), added=3, replaced=1,
        skipped=2, matched=10, fuzzy=1, metadata_conflicts=2,
        artwork_conflicts=4, scan_errors=0,
    )
    destination = save_json(report, tmp_path / "report.json")
    text = destination.read_text(encoding="utf-8")
    assert '"added": 3' in text
    assert '"artwork_conflicts": 4' in text
    assert report.to_dict()["matched"] == 10

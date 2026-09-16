from pathlib import Path
import wave

from music_sync.matcher import build_plan, normalize
from music_sync.models import ScanResult, Track
from music_sync.scanner import scan_library


def test_empty_library_scan_has_no_tracks_or_errors(tmp_path: Path):
    result = scan_library(tmp_path, "a")
    assert result.tracks == []
    assert result.errors == []
    assert result.fingerprint == {}


def test_unicode_spaces_and_nested_audio_paths_are_scanned(tmp_path: Path):
    nested = tmp_path / "Music Library" / "Beyoncé" / "夜 album"
    nested.mkdir(parents=True)
    audio = nested / "01 — Café.mp3"
    audio.write_bytes(b"not a real mp3")

    result = scan_library(tmp_path, "a")

    assert result.tracks == []
    assert any("Café.mp3" in error for error in result.errors)
    assert normalize("Beyoncé — Déjà Vu") == "beyonce deja vu"


def test_zero_byte_audio_is_reported_not_raised(tmp_path: Path):
    audio = tmp_path / "empty.mp3"
    audio.touch()

    result = scan_library(tmp_path, "a")

    assert result.tracks == []
    assert len(result.errors) == 1
    assert "empty.mp3" in result.errors[0]


def test_read_only_audio_is_not_modified(tmp_path: Path):
    audio = tmp_path / "readonly.mp3"
    audio.write_bytes(b"invalid")
    audio.chmod(0o444)
    before_mode = audio.stat().st_mode
    try:
        result = scan_library(tmp_path, "a")
        assert result.tracks == []
        assert audio.stat().st_mode == before_mode
    finally:
        audio.chmod(0o644)


def test_scan_reports_file_read_failure_without_stopping_other_files(tmp_path: Path, monkeypatch):
    first = tmp_path / "first.mp3"
    second = tmp_path / "second.wav"
    first.write_bytes(b"one")
    with wave.open(str(second), "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(8000)
        handle.writeframes(b"\x00\x00")

    from music_sync import scanner

    original = scanner.sha256_file

    def fail_one(path):
        if Path(path).name == "first.mp3":
            raise OSError("simulated disappearing file")
        return original(path)

    monkeypatch.setattr(scanner, "sha256_file", fail_one)
    result = scan_library(tmp_path, "a")

    assert any("first.mp3" in error for error in result.errors)
    assert not any(track.path.name == "first.mp3" for track in result.tracks)
    assert any(track.path.name == "second.wav" for track in result.tracks)


def test_same_hash_is_exact_identity_even_with_different_paths(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    a.mkdir()
    b.mkdir()
    left = Track(a / "old name.mp3", "a", title="Song", artist="Artist", album="Album", file_hash="same")
    right = Track(b / "renamed.mp3", "b", title="Different", artist="Other", album="Other", file_hash="same")

    plan = build_plan(ScanResult("a", a, [left]), ScanResult("b", b, [right]))

    assert len(plan.matches) == 1
    assert plan.matches[0].match_kind == "hash"
    assert plan.matches[0].metadata_conflict is True


def test_different_hashes_can_still_match_by_metadata(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    a.mkdir()
    b.mkdir()
    left = Track(a / "song-a.mp3", "a", title="Song", artist="Artist", album="Album", file_hash="one")
    right = Track(b / "song-b.mp3", "b", title="Song", artist="Artist", album="Album", file_hash="two")

    plan = build_plan(ScanResult("a", a, [left]), ScanResult("b", b, [right]))

    assert len(plan.matches) == 1
    assert plan.matches[0].match_kind == "metadata"


def test_duplicate_filename_candidates_remain_unresolved(tmp_path: Path):
    a = tmp_path / "A"
    b = tmp_path / "B"
    a.mkdir()
    b.mkdir()
    left = Track(a / "song.mp3", "a", title="Song", artist="", album="")
    right_one = Track(b / "song.mp3", "b", title="Song", artist="Artist One", album="Album")
    right_two = Track(b / "song.mp3", "b", title="Song", artist="Artist Two", album="Album")

    plan = build_plan(ScanResult("a", a, [left]), ScanResult("b", b, [right_one, right_two]))

    assert plan.matches == []
    assert plan.library_a_only == [left]
    assert len(plan.library_b_only) == 2

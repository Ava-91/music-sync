from pathlib import Path

from music_sync.display import display_path


def test_display_path_uses_stable_posix_separators():
    assert display_path(Path("A") / "music" / "夜.mp3") == "A/music/夜.mp3"


def test_display_path_accepts_string_paths():
    assert display_path("A\\music\\song.mp3") == "A/music/song.mp3"

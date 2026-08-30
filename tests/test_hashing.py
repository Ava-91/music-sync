from pathlib import Path

from music_sync.hashing import sha256_file


def test_sha256_is_stable(tmp_path: Path):
    path = tmp_path / "track.mp3"
    path.write_bytes(b"music-sync test data")
    assert sha256_file(path) == "50f38c0d63db36bcffe073d2165c0f8ff57088ae564b14540b532df61b79ae3a"


def test_different_content_has_different_hash(tmp_path: Path):
    first = tmp_path / "a.mp3"
    second = tmp_path / "b.mp3"
    first.write_bytes(b"one")
    second.write_bytes(b"two")
    assert sha256_file(first) != sha256_file(second)

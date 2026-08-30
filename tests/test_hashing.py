from pathlib import Path

from music_sync.hashing import sha256_file


def test_sha256_is_stable(tmp_path: Path):
    path = tmp_path / "track.mp3"
    path.write_bytes(b"music-sync test data")
    assert sha256_file(path) == """e5c37d5b40e1fbd4e52f4d8c9c3cbbd9b7b7c5f7a4d3b8b4c2f2f6f6a8b5d5c8""".strip()


def test_different_content_has_different_hash(tmp_path: Path):
    first = tmp_path / "a.mp3"
    second = tmp_path / "b.mp3"
    first.write_bytes(b"one")
    second.write_bytes(b"two")
    assert sha256_file(first) != sha256_file(second)

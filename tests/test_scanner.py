from pathlib import Path

from music_sync.scanner import current_fingerprint


def test_current_fingerprint_supports_unicode_and_spaces(tmp_path: Path):
    root = tmp_path / "Library A – 夜" / "My Music"
    root.mkdir(parents=True)
    track = root / "Björk" / "Jóga.mp3"
    track.parent.mkdir()
    track.write_bytes(b"test audio")

    fingerprint = current_fingerprint(root)

    key = str(track.relative_to(root))
    assert key in fingerprint
    assert fingerprint[key].size == len(b"test audio")
    assert fingerprint[key].modified_ns > 0

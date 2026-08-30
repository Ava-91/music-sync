from music_sync.models import Track
from music_sync.matcher import _artwork_conflict


def test_missing_artwork_is_a_conflict():
    with_art = Track(path="a.mp3", side="laptop", artwork_hashes=("abc",))
    without_art = Track(path="b.mp3", side="phone", artwork_hashes=())
    assert _artwork_conflict(with_art, without_art)


def test_identical_multiple_artwork_payloads_are_equal():
    first = Track(path="a.mp3", side="laptop", artwork_hashes=("a", "b"))
    second = Track(path="b.mp3", side="phone", artwork_hashes=("a", "b"))
    assert not _artwork_conflict(first, second)


def test_different_artwork_order_is_detected():
    first = Track(path="a.mp3", side="laptop", artwork_hashes=("a", "b"))
    second = Track(path="b.mp3", side="phone", artwork_hashes=("b", "a"))
    assert _artwork_conflict(first, second)

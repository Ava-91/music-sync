from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

from .models import Match, ScanResult, SyncPlan, Track


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).casefold()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def track_key(track: Track) -> tuple[str, str, str]:
    return normalize(track.artist), normalize(track.title or track.path.stem), normalize(track.album)


def similarity(a: Track, b: Track) -> float:
    """Return a conservative 0..1 similarity score based on metadata."""
    title_a = normalize(a.title or a.path.stem)
    title_b = normalize(b.title or b.path.stem)
    artist_a = normalize(a.artist)
    artist_b = normalize(b.artist)
    album_a = normalize(a.album)
    album_b = normalize(b.album)

    title_score = SequenceMatcher(None, title_a, title_b).ratio()
    artist_score = SequenceMatcher(None, artist_a, artist_b).ratio() if artist_a or artist_b else 1.0
    album_score = SequenceMatcher(None, album_a, album_b).ratio() if album_a or album_b else 1.0

    duration_score = 1.0
    if a.duration is not None and b.duration is not None:
        delta = abs(a.duration - b.duration)
        duration_score = max(0.0, 1.0 - delta / 10.0)

    return 0.55 * title_score + 0.25 * artist_score + 0.10 * album_score + 0.10 * duration_score


def _metadata_conflict(a: Track, b: Track) -> bool:
    fields = ((a.title, b.title), (a.artist, b.artist), (a.album, b.album))
    return any(x and y and normalize(x) != normalize(y) for x, y in fields)


def build_plan(laptop: ScanResult, phone: ScanResult, threshold: float = 0.90) -> SyncPlan:
    """Build a non-destructive merge plan. The laptop version wins conflicts."""
    plan = SyncPlan()
    used_phone: set[int] = set()

    # Exact metadata matches first.
    phone_by_key: dict[tuple[str, str, str], list[tuple[int, Track]]] = {}
    for index, track in enumerate(phone.tracks):
        phone_by_key.setdefault(track_key(track), []).append((index, track))

    for laptop_track in laptop.tracks:
        candidates = phone_by_key.get(track_key(laptop_track), [])
        candidate = next(((i, t) for i, t in candidates if i not in used_phone), None)
        if candidate is not None:
            index, phone_track = candidate
            used_phone.add(index)
            plan.matches.append(Match(
                laptop=laptop_track,
                phone=phone_track,
                confidence=1.0,
                metadata_conflict=_metadata_conflict(laptop_track, phone_track),
            ))

    # Then cautiously match remaining tracks using fuzzy metadata + duration.
    remaining_phone = [
        (i, t) for i, t in enumerate(phone.tracks) if i not in used_phone
    ]
    for laptop_track in laptop.tracks:
        if any(m.laptop.path == laptop_track.path for m in plan.matches):
            continue
        best: tuple[float, int, Track] | None = None
        for index, phone_track in remaining_phone:
            score = similarity(laptop_track, phone_track)
            if score >= threshold and (best is None or score > best[0]):
                best = (score, index, phone_track)
        if best is not None:
            score, index, phone_track = best
            used_phone.add(index)
            remaining_phone = [(i, t) for i, t in remaining_phone if i != index]
            plan.matches.append(Match(
                laptop=laptop_track,
                phone=phone_track,
                confidence=score,
                metadata_conflict=_metadata_conflict(laptop_track, phone_track),
            ))
        else:
            plan.laptop_only.append(laptop_track)

    plan.phone_only = [t for i, t in enumerate(phone.tracks) if i not in used_phone]
    return plan

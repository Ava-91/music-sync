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
    """Return a conservative 0..1 similarity score based on metadata and filename."""
    title_a = normalize(a.title or a.path.stem)
    title_b = normalize(b.title or b.path.stem)
    name_a = normalize(a.path.stem)
    name_b = normalize(b.path.stem)
    artist_a = normalize(a.artist)
    artist_b = normalize(b.artist)
    album_a = normalize(a.album)
    album_b = normalize(b.album)

    title_score = SequenceMatcher(None, title_a, title_b).ratio()
    name_score = SequenceMatcher(None, name_a, name_b).ratio()
    artist_score = SequenceMatcher(None, artist_a, artist_b).ratio() if artist_a or artist_b else 1.0
    album_score = SequenceMatcher(None, album_a, album_b).ratio() if album_a or album_b else 1.0
    duration_score = 1.0
    if a.duration is not None and b.duration is not None:
        duration_score = max(0.0, 1.0 - abs(a.duration - b.duration) / 10.0)

    return 0.45 * title_score + 0.15 * name_score + 0.20 * artist_score + 0.10 * album_score + 0.10 * duration_score


def _metadata_conflict(a: Track, b: Track) -> bool:
    fields = ((a.title, b.title), (a.artist, b.artist), (a.album, b.album))
    return any(x and y and normalize(x) != normalize(y) for x, y in fields)


def _artwork_conflict(a: Track, b: Track) -> bool:
    return (
        a.artwork_hash is not None
        and b.artwork_hash is not None
        and a.artwork_hash != b.artwork_hash
    )


def build_plan(laptop: ScanResult, phone: ScanResult, threshold: float = 0.88) -> SyncPlan:
    """Build a non-destructive merge plan. The laptop version wins conflicts."""
    plan = SyncPlan()
    used_phone: set[int] = set()
    matched_laptop: set[object] = set()

    phone_by_key: dict[tuple[str, str, str], list[tuple[int, Track]]] = {}
    for index, track in enumerate(phone.tracks):
        phone_by_key.setdefault(track_key(track), []).append((index, track))

    for laptop_track in laptop.tracks:
        candidate = next(
            ((i, t) for i, t in phone_by_key.get(track_key(laptop_track), []) if i not in used_phone),
            None,
        )
        if candidate is None:
            continue
        index, phone_track = candidate
        used_phone.add(index)
        matched_laptop.add(laptop_track.path)
        plan.matches.append(Match(
            laptop=laptop_track,
            phone=phone_track,
            confidence=1.0,
            metadata_conflict=_metadata_conflict(laptop_track, phone_track),
            artwork_conflict=_artwork_conflict(laptop_track, phone_track),
        ))

    remaining_phone = [(i, t) for i, t in enumerate(phone.tracks) if i not in used_phone]
    for laptop_track in laptop.tracks:
        if laptop_track.path in matched_laptop:
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
            matched_laptop.add(laptop_track.path)
            plan.matches.append(Match(
                laptop=laptop_track,
                phone=phone_track,
                confidence=score,
                metadata_conflict=_metadata_conflict(laptop_track, phone_track),
                artwork_conflict=_artwork_conflict(laptop_track, phone_track),
            ))
        else:
            plan.laptop_only.append(laptop_track)

    plan.phone_only = [t for i, t in enumerate(phone.tracks) if i not in used_phone]
    return plan

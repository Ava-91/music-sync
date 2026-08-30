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


def _same_duration(a: Track, b: Track, tolerance: float = 2.0) -> bool:
    return a.duration is not None and b.duration is not None and abs(a.duration - b.duration) <= tolerance


def _artwork_conflict(a: Track, b: Track) -> bool:
    return a.artwork_hash is not None and b.artwork_hash is not None and a.artwork_hash != b.artwork_hash


def _metadata_conflict(a: Track, b: Track) -> bool:
    fields = ((a.title, b.title), (a.artist, b.artist), (a.album, b.album))
    return any(x and y and normalize(x) != normalize(y) for x, y in fields)


def similarity(a: Track, b: Track) -> float:
    """Return a 0..1 similarity score for review-only fuzzy matching."""
    title_score = SequenceMatcher(None, normalize(a.title or a.path.stem), normalize(b.title or b.path.stem)).ratio()
    name_score = SequenceMatcher(None, normalize(a.path.stem), normalize(b.path.stem)).ratio()
    artist_score = SequenceMatcher(None, normalize(a.artist), normalize(b.artist)).ratio() if a.artist or b.artist else 1.0
    album_score = SequenceMatcher(None, normalize(a.album), normalize(b.album)).ratio() if a.album or b.album else 1.0
    duration_score = 1.0 if _same_duration(a, b) else 0.0
    return 0.45 * title_score + 0.15 * name_score + 0.20 * artist_score + 0.10 * album_score + 0.10 * duration_score


def _make_match(laptop: Track, phone: Track, confidence: float, confirmed: bool) -> Match:
    return Match(
        laptop=laptop,
        phone=phone,
        confidence=confidence,
        metadata_conflict=_metadata_conflict(laptop, phone),
        artwork_conflict=_artwork_conflict(laptop, phone),
        confirmed=confirmed,
    )


def build_plan(laptop: ScanResult, phone: ScanResult, threshold: float = 0.88) -> SyncPlan:
    """Build a non-destructive merge plan using content identity first."""
    plan = SyncPlan()
    used_phone: set[int] = set()
    matched_laptop: set[object] = set()

    # Byte-identical files are the strongest possible match and take priority
    # over metadata, filenames, or fuzzy similarity.
    phone_by_hash: dict[str, list[tuple[int, Track]]] = {}
    for index, track in enumerate(phone.tracks):
        if track.file_hash:
            phone_by_hash.setdefault(track.file_hash, []).append((index, track))

    for laptop_track in laptop.tracks:
        if not laptop_track.file_hash:
            continue
        candidate = next((item for item in phone_by_hash.get(laptop_track.file_hash, []) if item[0] not in used_phone), None)
        if candidate is None:
            continue
        index, phone_track = candidate
        used_phone.add(index)
        matched_laptop.add(laptop_track.path)
        plan.matches.append(_make_match(laptop_track, phone_track, 1.0, True))

    phone_by_key: dict[tuple[str, str, str], list[tuple[int, Track]]] = {}
    for index, track in enumerate(phone.tracks):
        if index not in used_phone:
            phone_by_key.setdefault(track_key(track), []).append((index, track))

    for laptop_track in laptop.tracks:
        if laptop_track.path in matched_laptop:
            continue
        candidate = next(((i, t) for i, t in phone_by_key.get(track_key(laptop_track), []) if i not in used_phone), None)
        if candidate is None:
            continue
        index, phone_track = candidate
        used_phone.add(index)
        matched_laptop.add(laptop_track.path)
        plan.matches.append(_make_match(laptop_track, phone_track, 1.0, True))

    phone_by_name: dict[str, list[tuple[int, Track]]] = {}
    for index, track in enumerate(phone.tracks):
        if index not in used_phone:
            phone_by_name.setdefault(normalize(track.path.stem), []).append((index, track))

    for laptop_track in laptop.tracks:
        if laptop_track.path in matched_laptop:
            continue
        candidates = [
            (i, t) for i, t in phone_by_name.get(normalize(laptop_track.path.stem), [])
            if i not in used_phone and (_same_duration(laptop_track, t) or normalize(laptop_track.artist) == normalize(t.artist))
        ]
        if len(candidates) == 1:
            index, phone_track = candidates[0]
            used_phone.add(index)
            matched_laptop.add(laptop_track.path)
            plan.matches.append(_make_match(laptop_track, phone_track, 0.98, True))

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
            plan.matches.append(_make_match(laptop_track, phone_track, score, False))
        else:
            plan.laptop_only.append(laptop_track)

    plan.phone_only = [t for i, t in enumerate(phone.tracks) if i not in used_phone]
    return plan

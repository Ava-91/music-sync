from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

from .models import FileState, Match, ScanResult, SyncPlan, Track


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).casefold()
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    value = re.sub(r"[^\w]+", " ", value, flags=re.UNICODE)
    return " ".join(value.split())


def track_key(track: Track) -> tuple[str, str, str]:
    return normalize(track.artist), normalize(track.title or track.path.stem), normalize(track.album)


def _same_duration(a: Track, b: Track, tolerance: float = 2.0) -> bool:
    return a.duration is not None and b.duration is not None and abs(a.duration - b.duration) <= tolerance


def _artwork_conflict(a: Track, b: Track) -> bool:
    return a.artwork_hashes != b.artwork_hashes and bool(a.artwork_hashes or b.artwork_hashes)


def _metadata_conflict(a: Track, b: Track) -> bool:
    fields = ((a.title, b.title), (a.artist, b.artist), (a.album, b.album))
    return any(x and y and normalize(x) != normalize(y) for x, y in fields)


def similarity(a: Track, b: Track) -> float:
    title_score = SequenceMatcher(None, normalize(a.display_title), normalize(b.display_title)).ratio()
    name_score = SequenceMatcher(None, normalize(a.path.stem), normalize(b.path.stem)).ratio()
    artist_score = SequenceMatcher(None, normalize(a.artist), normalize(b.artist)).ratio() if a.artist or b.artist else 1.0
    album_score = SequenceMatcher(None, normalize(a.album), normalize(b.album)).ratio() if a.album or b.album else 1.0
    duration_score = 1.0 if _same_duration(a, b) else 0.0
    return 0.45 * title_score + 0.15 * name_score + 0.20 * artist_score + 0.10 * album_score + 0.10 * duration_score


def _make_match(a: Track, b: Track, confidence: float, confirmed: bool, kind: str) -> Match:
    return Match(a, b, confidence, _metadata_conflict(a, b), _artwork_conflict(a, b), confirmed, kind)


def _fingerprint(result: ScanResult) -> dict[str, FileState]:
    data: dict[str, FileState] = {}
    for track in result.tracks:
        try:
            relative = str(track.path.resolve().relative_to(result.root.resolve()))
        except ValueError:
            relative = str(track.path.resolve())
        data[relative] = FileState(relative, track.size, track.modified_ns, track.file_hash)
    return data


def build_plan(a: ScanResult, b: ScanResult, threshold: float = 0.88) -> SyncPlan:
    """Build a conservative, library-agnostic reconciliation plan."""
    plan = SyncPlan(library_a_root=a.root.resolve(), library_b_root=b.root.resolve(), fingerprint_a=_fingerprint(a), fingerprint_b=_fingerprint(b))
    used_b: set[int] = set()
    matched_a: set[object] = set()

    by_hash: dict[str, list[tuple[int, Track]]] = {}
    for i, track in enumerate(b.tracks):
        if track.file_hash:
            by_hash.setdefault(track.file_hash, []).append((i, track))
    for a_track in a.tracks:
        candidates = [x for x in by_hash.get(a_track.file_hash or "", []) if x[0] not in used_b]
        if a_track.file_hash and len(candidates) == 1:
            i, b_track = candidates[0]
            used_b.add(i); matched_a.add(a_track.path)
            plan.matches.append(_make_match(a_track, b_track, 1.0, True, "hash"))

    by_key: dict[tuple[str, str, str], list[tuple[int, Track]]] = {}
    for i, track in enumerate(b.tracks):
        if i not in used_b:
            by_key.setdefault(track_key(track), []).append((i, track))
    for a_track in a.tracks:
        if a_track.path in matched_a: continue
        candidates = [x for x in by_key.get(track_key(a_track), []) if x[0] not in used_b]
        if len(candidates) == 1:
            i, b_track = candidates[0]
            used_b.add(i); matched_a.add(a_track.path)
            plan.matches.append(_make_match(a_track, b_track, 1.0, True, "metadata"))

    by_name: dict[str, list[tuple[int, Track]]] = {}
    for i, track in enumerate(b.tracks):
        if i not in used_b:
            by_name.setdefault(normalize(track.path.stem), []).append((i, track))
    for a_track in a.tracks:
        if a_track.path in matched_a: continue
        candidates = [x for x in by_name.get(normalize(a_track.path.stem), []) if x[0] not in used_b and (_same_duration(a_track, x[1]) or normalize(a_track.artist) == normalize(x[1].artist))]
        if len(candidates) == 1:
            i, b_track = candidates[0]
            used_b.add(i); matched_a.add(a_track.path)
            plan.matches.append(_make_match(a_track, b_track, 0.98, True, "filename"))

    remaining = [(i, t) for i, t in enumerate(b.tracks) if i not in used_b]
    for a_track in a.tracks:
        if a_track.path in matched_a: continue
        ranked = sorted(((similarity(a_track, t), i, t) for i, t in remaining), reverse=True, key=lambda x: x[0])
        if ranked and ranked[0][0] >= threshold and (len(ranked) == 1 or ranked[0][0] - ranked[1][0] >= 0.03):
            score, i, b_track = ranked[0]
            used_b.add(i); matched_a.add(a_track.path)
            remaining = [(j, t) for j, t in remaining if j != i]
            plan.matches.append(_make_match(a_track, b_track, score, False, "fuzzy"))
        else:
            plan.library_a_only.append(a_track)
    plan.library_b_only = [t for i, t in enumerate(b.tracks) if i not in used_b]
    return plan

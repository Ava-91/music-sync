from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from mutagen import File


@dataclass(frozen=True, slots=True)
class ArtworkInfo:
    """Normalized information about embedded artwork in an audio file."""

    count: int
    hashes: tuple[str, ...]

    @property
    def primary_hash(self) -> str | None:
        return self.hashes[0] if self.hashes else None


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def extract_artwork_info(path: Path) -> ArtworkInfo:
    """Return deterministic hashes for every embedded artwork payload."""
    audio = File(path, easy=False)
    if not audio:
        return ArtworkInfo(0, ())

    payloads: list[bytes] = []
    for key, value in (audio.tags or {}).items():
        key_text = str(key).upper()
        if key_text.startswith("APIC"):
            data = getattr(value, "data", None)
            if data:
                payloads.append(bytes(data))
        elif key_text == "COVR":
            try:
                payloads.extend(bytes(item) for item in value)
            except (TypeError, ValueError):
                pass

    for picture in getattr(audio, "pictures", []) or []:
        data = getattr(picture, "data", None)
        if data:
            payloads.append(bytes(data))

    hashes = tuple(_digest(data) for data in payloads)
    return ArtworkInfo(len(hashes), hashes)

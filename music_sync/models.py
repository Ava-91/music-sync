from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


Side = Literal["laptop", "phone"]


@dataclass(slots=True)
class Track:
    """A scanned audio file and the metadata needed for comparison."""

    path: Path
    side: Side
    title: str = ""
    artist: str = ""
    album: str = ""
    duration: float | None = None
    size: int = 0
    modified_ns: int = 0
    file_hash: str | None = None
    artwork_hash: str | None = None
    artwork_hashes: tuple[str, ...] = ()

    @property
    def artwork_count(self) -> int:
        return len(self.artwork_hashes)

    @property
    def display_title(self) -> str:
        return self.title or self.path.stem

    @property
    def display_artist(self) -> str:
        return self.artist or "Unknown artist"

    @property
    def display_album(self) -> str:
        return self.album or "Unknown album"


@dataclass(slots=True)
class Match:
    """A pair of tracks believed to represent the same song."""

    laptop: Track
    phone: Track
    confidence: float
    metadata_conflict: bool = False
    artwork_conflict: bool = False
    confirmed: bool = True


@dataclass(slots=True)
class ScanResult:
    side: Side
    root: Path
    tracks: list[Track] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SyncPlan:
    laptop_only: list[Track] = field(default_factory=list)
    phone_only: list[Track] = field(default_factory=list)
    matches: list[Match] = field(default_factory=list)

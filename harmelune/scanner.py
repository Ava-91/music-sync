from __future__ import annotations

from pathlib import Path
from typing import Callable

from mutagen import File

from .artwork_hash import extract_artwork_info
from .hashing import sha256_file
from .models import FileState, ScanResult, Side, Track

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".m4b", ".flac", ".wav", ".ogg", ".opus", ".aac", ".wma"}


def _first_tag(audio, *names: str) -> str:
    if not audio or not audio.tags:
        return ""
    for name in names:
        value = audio.tags.get(name)
        if value:
            if isinstance(value, (list, tuple)):
                return str(value[0])
            return str(value)
    return ""


def scan_library(root: str | Path, side: Side, progress: Callable[[int], None] | None = None, cancel: Callable[[], bool] | None = None) -> ScanResult:
    """Read-only recursive scan. Files that cannot be read are reported, never modified."""
    root = Path(root).expanduser().resolve(strict=False)
    result = ScanResult(side=side, root=root)
    if not root.exists():
        result.errors.append(f"Directory does not exist: {root}")
        return result
    if not root.is_dir():
        result.errors.append(f"Not a directory: {root}")
        return result
    try:
        paths = list(root.rglob("*"))
    except OSError as exc:
        result.errors.append(f"Could not enumerate {root}: {exc}")
        return result
    audio_paths = [p for p in paths if p.is_file() and p.suffix.lower() in AUDIO_EXTENSIONS]
    for index, path in enumerate(audio_paths, 1):
        if cancel and cancel():
            result.errors.append("Scan cancelled by user")
            break
        try:
            stat = path.stat()
            easy_audio = File(path, easy=True)
            raw_audio = File(path, easy=False)
            duration = float(raw_audio.info.length) if raw_audio and raw_audio.info else None
            artwork = extract_artwork_info(path)
            relative = str(path.relative_to(root))
            result.tracks.append(Track(path, side, _first_tag(easy_audio, "title"), _first_tag(easy_audio, "artist", "albumartist"), _first_tag(easy_audio, "album"), duration, stat.st_size, stat.st_mtime_ns, sha256_file(path), artwork.primary_hash, artwork.hashes))
            result.fingerprint[relative] = FileState(relative, stat.st_size, stat.st_mtime_ns, result.tracks[-1].file_hash)
        except (OSError, ValueError, TypeError) as exc:
            result.errors.append(f"Could not read {path}: {exc}")
        except Exception as exc:
            result.errors.append(f"Could not parse {path}: {exc}")
        if progress:
            progress(index)
    return result


def current_fingerprint(root: str | Path) -> dict[str, FileState]:
    """Return a lightweight filesystem fingerprint for freshness validation."""
    root = Path(root).expanduser().resolve(strict=False)
    if not root.is_dir():
        raise FileNotFoundError(f"Library directory is unavailable: {root}")
    fingerprint: dict[str, FileState] = {}
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in AUDIO_EXTENSIONS:
            stat = path.stat()
            relative = str(path.relative_to(root))
            fingerprint[relative] = FileState(relative, stat.st_size, stat.st_mtime_ns)
    return fingerprint

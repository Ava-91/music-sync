from __future__ import annotations

from pathlib import Path

from mutagen import File

from .artwork_hash import extract_artwork_info
from .hashing import sha256_file
from .models import ScanResult, Side, Track

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


def scan_library(root: str | Path, side: Side) -> ScanResult:
    """Scan an accessible directory without modifying anything."""
    root = Path(root)
    result = ScanResult(side=side, root=root)
    if not root.exists():
        result.errors.append(f"Directory does not exist: {root}")
        return result
    if not root.is_dir():
        result.errors.append(f"Not a directory: {root}")
        return result

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        try:
            easy_audio = File(path, easy=True)
            raw_audio = File(path, easy=False)
            duration = float(raw_audio.info.length) if raw_audio and raw_audio.info else None
            artwork = extract_artwork_info(path)
            stat = path.stat()
            result.tracks.append(Track(
                path=path,
                side=side,
                title=_first_tag(easy_audio, "title"),
                artist=_first_tag(easy_audio, "artist", "albumartist"),
                album=_first_tag(easy_audio, "album"),
                duration=duration,
                size=stat.st_size,
                modified_ns=stat.st_mtime_ns,
                file_hash=sha256_file(path),
                artwork_hash=artwork.primary_hash,
                artwork_hashes=artwork.hashes,
            ))
        except (OSError, ValueError, TypeError) as exc:
            result.errors.append(f"Could not read {path}: {exc}")
        except Exception as exc:
            result.errors.append(f"Could not parse {path}: {exc}")

    return result

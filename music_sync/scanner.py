from __future__ import annotations

from pathlib import Path

from mutagen import File

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

    try:
        paths = root.rglob("*")
    except OSError as exc:
        result.errors.append(f"Could not enumerate {root}: {exc}")
        return result

    for path in paths:
        if not path.is_file() or path.suffix.lower() not in AUDIO_EXTENSIONS:
            continue
        try:
            stat = path.stat()
            audio = File(path, easy=True)
            track = Track(
                path=path,
                side=side,
                title=_first_tag(audio, "title"),
                artist=_first_tag(audio, "artist", "albumartist"),
                album=_first_tag(audio, "album"),
                duration=float(audio.info.length) if audio and audio.info else None,
                size=stat.st_size,
                modified_ns=stat.st_mtime_ns,
            )
            result.tracks.append(track)
        except (OSError, ValueError, TypeError) as exc:
            result.errors.append(f"Could not read {path}: {exc}")
        except Exception as exc:  # Mutagen can raise format-specific exceptions.
            result.errors.append(f"Could not parse {path}: {exc}")

    return result

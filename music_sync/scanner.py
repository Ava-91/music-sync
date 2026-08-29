from __future__ import annotations

import hashlib
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


def _artwork_hash(audio) -> str | None:
    """Hash embedded artwork for common Mutagen-supported formats."""
    if not audio:
        return None
    images: list[bytes] = []

    for key, value in (audio.tags or {}).items():
        key_text = str(key).upper()
        if key_text.startswith("APIC"):
            data = getattr(value, "data", None)
            if data:
                images.append(bytes(data))
        elif key_text == "COVR":
            try:
                images.extend(bytes(item) for item in value)
            except (TypeError, ValueError):
                pass

    for picture in getattr(audio, "pictures", []) or []:
        data = getattr(picture, "data", None)
        if data:
            images.append(bytes(data))

    if not images:
        return None
    digest = hashlib.sha256()
    for image in images:
        digest.update(image)
    return digest.hexdigest()


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
                artwork_hash=_artwork_hash(raw_audio),
            ))
        except (OSError, ValueError, TypeError) as exc:
            result.errors.append(f"Could not read {path}: {exc}")
        except Exception as exc:
            result.errors.append(f"Could not parse {path}: {exc}")

    return result

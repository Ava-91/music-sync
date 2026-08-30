from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image, ImageTk
from mutagen import File


def extract_first_artwork(path: Path) -> bytes | None:
    """Return the first embedded artwork image from an audio file."""
    audio = File(path, easy=False)
    if not audio:
        return None

    for key, value in (audio.tags or {}).items():
        if str(key).upper().startswith("APIC"):
            data = getattr(value, "data", None)
            if data:
                return bytes(data)
        if str(key).upper() == "COVR":
            try:
                return bytes(value[0]) if value else None
            except (TypeError, IndexError):
                return None

    pictures = getattr(audio, "pictures", []) or []
    if pictures:
        data = getattr(pictures[0], "data", None)
        if data:
            return bytes(data)
    return None


def make_preview(path: Path, size: tuple[int, int] = (180, 180)) -> ImageTk.PhotoImage | None:
    """Build a Tk-compatible artwork preview, returning None when unavailable."""
    data = extract_first_artwork(path)
    if not data:
        return None
    try:
        image = Image.open(BytesIO(data)).convert("RGB")
        image.thumbnail(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(image)
    except Exception:
        return None

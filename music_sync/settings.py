from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

from .models import SyncMode


@dataclass(slots=True)
class Settings:
    library_a: str = ""
    library_b: str = ""
    master: str = ""
    sync_mode: str = SyncMode.SAFE
    backup_location: str = ""
    fuzzy_threshold: float = 0.88
    conflict_defaults: dict[str, str] = field(default_factory=dict)
    appearance: str = "system"

    def validate(self) -> None:
        if not 0.0 <= self.fuzzy_threshold <= 1.0:
            raise ValueError("fuzzy_threshold must be between 0 and 1")
        if self.sync_mode not in {SyncMode.SAFE, SyncMode.RECONCILE, SyncMode.MIRROR}:
            raise ValueError(f"Unsupported sync mode: {self.sync_mode}")
        if self.master not in {"", "library_a", "library_b"}:
            raise ValueError(f"Unsupported master: {self.master}")
        if self.appearance not in {"system", "light", "dark"}:
            raise ValueError(f"Unsupported appearance: {self.appearance}")


class SettingsStore:
    """Persist user configuration separately from music libraries."""

    def __init__(self, config_dir: str | Path | None = None) -> None:
        self.config_dir = Path(config_dir) if config_dir is not None else default_config_dir()
        self.path = self.config_dir / "settings.json"

    def load(self) -> Settings:
        if not self.path.is_file():
            return Settings()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            settings = Settings(**payload)
            settings.validate()
            return settings
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return Settings()

    def save(self, settings: Settings) -> Path:
        settings.validate()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(asdict(settings), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)
        return self.path


def default_config_dir() -> Path:
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "music-sync"
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg) / "music-sync"
    return Path.home() / ".config" / "music-sync"

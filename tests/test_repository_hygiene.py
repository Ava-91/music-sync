from __future__ import annotations

import subprocess
from pathlib import Path



def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
        text=False,
    )
    return [item for item in result.stdout.decode("utf-8").split("\0") if item]


def test_no_personal_developer_paths_are_tracked():
    forbidden = ["E:" + chr(92) + "Ava files", "Ava files", "DEFAULT_" + "LAPTOP", "DEFAULT_" + "PHONE_COPY"]
    for path in tracked_files():
        if path.replace("\\", "/").startswith("tests/"):
            continue
        try:
            text = Path(path).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        assert not any(value in text for value in forbidden), path


def test_no_audio_or_build_artifacts_are_tracked():
    forbidden_suffixes = {".mp3", ".wav", ".flac", ".m4a", ".m4b", ".aac", ".ogg", ".opus", ".wma", ".pyc"}
    forbidden_fragments = ("__pycache__/", "dist/", ".pytest_cache/")
    for path in tracked_files():
        normalized = path.replace("\\", "/")
        assert Path(path).suffix.lower() not in forbidden_suffixes, path
        assert not any(fragment in normalized for fragment in forbidden_fragments), path


def test_gitignore_covers_private_audio_and_local_state():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    for required in ("*.mp3", "*.flac", "harmelune-backups/", ".env", "dist/"):
        assert required in gitignore

# 🎵 music-sync

A safe, metadata-aware music library sync tool for Windows.

`music-sync` is designed for the annoying situation where your laptop and phone have different versions of the same music library. Instead of blindly mirroring one folder over the other, it scans both sides, previews changes, backs up before destructive operations, and prefers the laptop copy when the same track exists in both libraries.

## Goals

- 🔎 Scan laptop and Android/MTP music libraries
- 🟢 Find laptop-only tracks
- 🔵 Find phone-only tracks
- 🟡 Detect tracks that exist on both sides
- ⚠️ Flag possible metadata/artwork conflicts
- 💾 Create a backup before destructive sync operations
- 🖼️ Preserve embedded artwork and audio metadata
- 👀 Preview changes before applying them
- 🔄 Sync the merged library back to the phone

## Current status

🚧 Early development — the first milestone is a safe scanner and preview workflow. **No music files are modified by a scan.**

## Requirements

- Windows 10/11
- Python 3.11+
- An Android phone connected over USB with **File Transfer** enabled
- `pywin32` for Windows MTP/Explorer access

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run:

```powershell
python app.py
```

## Important safety rule

Your real music files do **not** belong in this repository. The application works with local paths at runtime and those paths are intentionally not stored in Git.

Always review the proposed changes before running a write/sync operation.

## Planned architecture

```text
music-sync/
├── app.py                 # Tkinter UI
├── music_sync/
│   ├── models.py          # Track/library/change models
│   ├── scanner.py         # Local filesystem scanning
│   ├── mtp.py             # Windows MTP / Explorer integration
│   ├── matcher.py         # Track matching + conflict detection
│   └── sync.py             # Backup + safe copy operations
├── tests/
└── requirements.txt
```

## License

MIT

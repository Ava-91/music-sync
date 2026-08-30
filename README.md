# 🎵 music-sync

A safe, metadata-aware music library merger and synchronizer for Windows.

`music-sync` is built for the situation where a laptop and a phone have different versions of the same music library. Copy the phone's `Music` folder to Windows, let the app compare both libraries, review the plan, and merge the phone-only tracks into the laptop master library.

## What it does

- 🔎 Scans two normal Windows folders recursively
- 🟢 Finds laptop-only and phone-only tracks
- 🟡 Matches tracks using metadata, filename, duration, and conservative fuzzy matching
- 🧠 Separates uncertain fuzzy matches from trusted matches
- 📝 Detects metadata conflicts
- 🖼️ Detects differences in embedded album artwork
- 👀 Reviews metadata/artwork conflicts side-by-side
- 🔍 Reviews every fuzzy match before it can be treated as the same song
- 💾 Creates a timestamped laptop backup before merging
- 🛡️ Never uses an unconfirmed fuzzy match for a merge
- 📱 Leaves the final phone copy step to you, so physical A02s storage is never touched directly

## Your workflow

1. Copy the A02s `Internal storage/Music` folder to a normal Windows folder, for example `E:\Ava files\phone music`.
2. Run `install.bat` once, then use `run.bat` whenever you want to launch the app.
3. Select the laptop and copied phone libraries.
4. Click **Scan & Preview**.
5. Review metadata/artwork conflicts and fuzzy matches.
6. Confirm or reject every fuzzy suggestion.
7. Click **Merge Safely**. The app backs up first, adds phone-only tracks, and applies only reviewed conflict choices.
8. Copy the finished laptop library back to the A02s `Internal storage/Music` folder.

## Matching safety

Exact metadata matches and strong filename/duration matches are trusted. Conservative fuzzy matches are marked **unconfirmed** and must be explicitly accepted as the same song or rejected as different songs. An unresolved fuzzy match blocks the merge operation.

## Requirements

- Windows 10/11
- Python 3.11+
- `mutagen`
- `Pillow` for embedded artwork previews

Manual install:

```powershell
python -m pip install -r requirements.txt
```

Manual run:

```powershell
python app.py
```

Or use the included `install.bat` and `run.bat` launchers.

## Safety

- Scanning is read-only.
- A backup is created before every merge.
- Existing laptop files are never replaced unless the user explicitly chooses **Keep Phone** for a reviewed conflict.
- Unconfirmed fuzzy matches cannot be merged as matches.
- Music files and personal library contents do not belong in this repository.
- Backups are stored outside the music library in `music-sync-backups`.

## Project structure

```text
music-sync/
├── app.py
├── music_sync/
│   ├── __init__.py
│   ├── artwork.py
│   ├── conflict_ui.py
│   ├── fuzzy_ui.py
│   ├── models.py
│   ├── matcher.py
│   ├── review.py
│   └── sync.py
├── tests/
│   ├── test_fuzzy_review.py
│   ├── test_matcher.py
│   └── test_review.py
├── install.bat
├── run.bat
├── requirements.txt
├── .gitignore
└── LICENSE
```

## License

MIT

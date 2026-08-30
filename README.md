# 🎵 music-sync

A safe, metadata-aware music library merger and synchronizer for Windows.

`music-sync` is built for the situation where a laptop and a phone have different versions of the same music library. Copy the phone's `Music` folder to Windows, let the app compare both libraries, review the plan, and merge the phone-only tracks into the laptop master library.

## What it does

- 🔎 Scans two normal Windows folders recursively
- 🟢 Finds laptop-only and phone-only tracks
- 🟡 Matches the same tracks using metadata, filename, duration, and conservative fuzzy matching
- 📝 Detects metadata conflicts
- 🖼️ Detects differences in embedded album artwork
- 👀 Reviews metadata/artwork conflicts side-by-side before applying choices
- 💾 Creates a timestamped laptop backup before merging
- 🛡️ Never overwrites an existing laptop file unless you explicitly choose the phone version for a conflict
- 📱 Leaves the final phone copy step to you, so physical A02s storage is never touched directly

## Your workflow

1. On the Samsung A02s, copy `Internal storage/Music` to a normal Windows folder, for example `E:\Ava files\phone music`.
2. Run `install.bat` once, then use `run.bat` whenever you want to launch the app.
3. Keep the laptop folder as `E:\Ava files\ava music` or choose another folder.
4. Select the copied phone folder.
5. Click **Scan & Preview**.
6. Click **Review Conflicts** when metadata or artwork conflicts are found.
7. Choose **Keep Laptop**, **Keep Phone**, or **Skip** for each conflict.
8. Click **Merge Safely**. The app backs up first, adds phone-only tracks, and applies only the choices you made.
9. Copy the finished laptop library back to the A02s `Internal storage/Music` folder.

## Conflict review

Each metadata/artwork conflict is presented with the laptop and phone track information side by side. Embedded album artwork is shown when it can be decoded. The laptop version remains the default choice, so closing/cancelling review never causes a phone version to replace it.

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
│   ├── models.py
│   ├── matcher.py
│   ├── review.py
│   └── sync.py
├── tests/
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

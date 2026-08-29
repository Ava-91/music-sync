# 🎵 music-sync

A safe, metadata-aware music library merger and synchronizer for Windows.

`music-sync` is built for the situation where a laptop and a phone have different versions of the same music library. Copy the phone's `Music` folder to Windows, let the app compare both libraries, review the plan, and merge the phone-only tracks into the laptop master library.

## What it does

- 🔎 Scans two normal Windows folders recursively
- 🟢 Finds laptop-only and phone-only tracks
- 🟡 Matches the same tracks using metadata, filename, duration, and conservative fuzzy matching
- 📝 Detects metadata conflicts
- 🖼️ Detects differences in embedded album artwork
- 💾 Creates a timestamped laptop backup before merging
- 🛡️ Never overwrites an existing laptop file during the merge
- 👀 Shows a preview before changing anything
- 📱 Leaves the final phone copy step to you, so the physical A02s storage is never touched directly

## Your workflow

1. On the Samsung A02s, copy `Internal storage/Music` to a normal Windows folder, for example:
   `E:\Ava files\phone music`
2. Run `install.bat` once to install the dependency, then use `run.bat` whenever you want to launch the app.
3. Keep the laptop folder as `E:\Ava files\ava music` or choose another folder.
4. Select the copied phone folder.
5. Click **Scan & Preview**.
6. Review the counts and conflicts.
7. Click **Merge Phone-Only Songs** if everything looks right.
8. The app backs up the laptop library and adds phone-only tracks without replacing laptop files.
9. Copy the finished laptop `ava music` folder back to the A02s `Internal storage/Music` folder.

### Conflict rule

When the same track exists on both sides, the **laptop version is the preferred version**. This is intentional because the laptop library is where custom titles, artwork, and other edits are maintained.

The app currently does not rewrite the phone copy directly and does not modify matched laptop files.

## Requirements

- Windows 10/11
- Python 3.11+
- `mutagen`

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
- A backup is created before a merge.
- Existing laptop files are never replaced by phone files.
- Music files and personal library contents do not belong in this repository.
- Backups are stored outside the music library in `music-sync-backups`.

## Project structure

```text
music-sync/
├── app.py
├── music_sync/
│   ├── __init__.py
│   ├── models.py
│   ├── scanner.py
│   ├── matcher.py
│   └── sync.py
├── tests/
│   └── test_matcher.py
├── install.bat
├── run.bat
├── requirements.txt
├── .gitignore
└── LICENSE
```

## License

MIT

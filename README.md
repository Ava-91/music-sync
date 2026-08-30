# 🎵 music-sync

A safe, metadata-aware music library reconciliation and synchronization tool for Windows.

`music-sync` compares two independently maintained music libraries, finds tracks that exist only on one side, detects metadata and embedded-artwork differences, helps review ambiguous matches, creates a backup, and builds a merged master library.

It works with **any two Windows-accessible music folders**. The application does not care where the folders came from.

## ✨ What it does

- 🔎 Scans two normal Windows folders recursively
- 🟢 Finds tracks unique to either library
- 🟡 Matches tracks using metadata, filename, duration, and conservative fuzzy matching
- 🧠 Separates uncertain fuzzy matches from trusted matches
- 📝 Detects metadata conflicts
- 🖼️ Detects differences in embedded album artwork
- 👀 Reviews metadata and artwork conflicts side-by-side
- 🔍 Reviews every fuzzy match before it can be treated as the same song
- 💾 Creates a timestamped backup before merging
- 🛡️ Never uses an unconfirmed fuzzy match for a merge
- 📁 Works with arbitrary local library paths
- 🔒 Operates entirely on the folders you select

## 🗂️ General workflow

1. Make sure both music collections are available as normal Windows folders.
2. Launch `music-sync`.
3. Select **Library A** and **Library B**.
4. Click **Scan & Preview**.
5. Review metadata/artwork conflicts and fuzzy matches.
6. Confirm or reject every fuzzy suggestion.
7. Click **Merge Safely**. The app backs up first, adds unique tracks, and applies only reviewed conflict choices.
8. Use or copy the resulting master library wherever you need it.

The application does not need to identify the original source of either library. A library can come from another computer, removable storage, an exported collection, a backup, or any other source—as long as Windows can access the files.

## 🎧 Why reconciliation instead of simple syncing?

A normal one-way sync assumes that one side is always correct. Real music collections are messier:

- A new track may exist in only one library.
- A title may have been edited in one copy.
- Album artwork may have been replaced in one copy.
- The same track may have different filenames.
- Both libraries may contain different versions of the same file.

`music-sync` treats this as a **reconciliation problem** rather than blindly copying one folder over another.

For example:

```text
Library A:
  Title: Getting Older
  Artwork: custom artwork

Library B:
  Title: Getting Older
  Artwork: old artwork

             ↓

🖼️ Artwork conflict
             ↓

👀 Review
             ↓

💻 Keep Library A artwork
```

## 🧠 Matching safety

The matching engine uses multiple signals rather than trusting filenames alone:

- Artist
- Title
- Album
- Duration
- Filename
- Metadata similarity
- Conservative fuzzy similarity

Strong matches can be trusted automatically. Fuzzy matches are **unconfirmed** and require explicit review before they can affect a merge.

An unresolved fuzzy match blocks the merge operation rather than guessing.

## 💾 Safety

`music-sync` is designed to be conservative with personal music libraries:

- Scanning is read-only.
- A backup is created before every merge.
- Existing master-library files are not silently overwritten.
- Unconfirmed fuzzy matches cannot be merged as matches.
- Unreadable files are never modified.
- Music files and personal library contents do not belong in this repository.
- Backups are kept outside the music library.

## 🛠️ Requirements

- Windows 10/11
- Python 3.11+
- `mutagen`
- `Pillow` for embedded artwork previews

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run manually:

```powershell
python app.py
```

Or use the included `install.bat` and `run.bat` launchers.

## 🗺️ Roadmap

The project is being developed toward a general-purpose local music-library reconciliation tool.

- [x] Library scanning
- [x] Metadata-aware matching
- [x] Artwork conflict detection
- [x] Interactive artwork/metadata conflict review
- [x] Fuzzy-match review
- [ ] File hashing and stronger identity detection
- [ ] Advanced artwork hashing/comparison
- [ ] Explain why each match was chosen
- [ ] Multiple sync modes
- [ ] Configurable master library
- [ ] Backup manager
- [ ] Sync reports and JSON export
- [ ] Dry-run mode
- [ ] Windows `.exe` distribution
- [ ] Portable mode
- [ ] Application settings
- [ ] Library health dashboard
- [ ] Fully library-agnostic reconciliation engine

## 🧱 Project structure

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

## 🤝 Contributing

Issues and pull requests are welcome. The project is especially interested in improvements to matching accuracy, conflict review, metadata handling, artwork preservation, backups, and safe file operations.

## 📄 License

MIT

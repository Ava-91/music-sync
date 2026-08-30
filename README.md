# 🎵 music-sync

A safe, metadata-aware music library reconciliation and synchronization tool for Windows.

`music-sync` is built for the very real problem of maintaining the **same music collection across multiple devices** when each copy has changed independently. It compares two local music libraries, finds songs that exist only on one side, detects metadata and embedded-artwork differences, helps you review ambiguous matches, creates a backup, and builds a merged master library.

> **It is not an A02s-only tool.** The A02s is simply the device this project was originally built and tested around. `music-sync` works with **any phone, tablet, USB drive, SD card, external disk, computer, backup, or other device** whose music folder can be copied to Windows and exposed as a normal local folder.

## ✨ What it does

- 🔎 Scans two normal Windows folders recursively
- 🟢 Finds tracks that exist only in Library A
- 🔵 Finds tracks that exist only in Library B
- 🟡 Matches tracks using metadata, filename, duration, and conservative fuzzy matching
- 🧠 Separates uncertain fuzzy matches from trusted matches
- 📝 Detects metadata conflicts
- 🖼️ Detects differences in embedded album artwork
- 👀 Reviews metadata and artwork conflicts side-by-side
- 🔍 Reviews every fuzzy match before it can be treated as the same song
- 💾 Creates a timestamped backup before merging
- 🛡️ Never uses an unconfirmed fuzzy match for a merge
- 📂 Works with arbitrary local library paths rather than hard-coded phone models
- 🔌 Does not require direct phone/MTP access — copy the device's music folder to Windows first

## 📱 Works with any phone

The app does **not** identify or depend on a particular phone model.

If your device can expose its music folder to Windows so that you can copy it to a normal folder, `music-sync` can work with it. For example:

```text
Android phone  → copy Music folder → Windows folder
iPhone         → copy exported music → Windows folder
Tablet         → copy music folder → Windows folder
USB drive      → use its music folder directly
SD card        → use its music folder directly
Another PC     → copy/export its music library → Windows folder
Backup         → use the backup folder as a library
```

The application only needs two ordinary Windows-accessible directories at comparison time. It does **not** need to know whether the files originally came from a Samsung, Google Pixel, iPhone, Xiaomi, OnePlus, tablet, USB drive, or anything else.

### Example

```text
📱 Any phone
   │
   │ copy Music folder
   ▼
📁 C:\Music\phone-copy
   │
   │
   ├──────────────────────┐
   │                      │
   ▼                      ▼
💻 Laptop library      📱 Phone copy
E:\Music\Master       C:\Music\phone-copy
   │                      │
   └──────────┬───────────┘
              ▼
       🎵 music-sync
              │
              ▼
       🧠 Reconciliation
              │
       ┌──────┼──────┐
       ▼      ▼      ▼
     MATCH  CONFLICT UNIQUE
       │      │      │
       └──────┼──────┘
              ▼
        💾 Backup first
              │
              ▼
       🎵 Merged library
```

## 🎧 Why reconciliation instead of simple syncing?

A normal one-way sync assumes that one side is always correct. Real music collections are messier:

- You may download a new song on your phone.
- You may edit its title on your laptop.
- You may replace an album cover on your laptop.
- You may have different filenames for the same track.
- Both devices may contain different versions of a file.

`music-sync` treats this as a **reconciliation problem** rather than blindly copying one folder over another.

For example:

```text
Laptop:
  Title: Getting Older
  Artwork: custom artwork

Phone:
  Title: Getting Older
  Artwork: old artwork

             ↓

🖼️ Artwork conflict
             ↓

👀 Review
             ↓

💻 Keep Laptop artwork
```

## 🔄 Current workflow

1. Copy your device's `Music` folder to a normal Windows folder.
2. Launch `music-sync`.
3. Select the laptop/master library and the copied device library.
4. Click **Scan & Preview**.
5. Review metadata and artwork conflicts.
6. Review every fuzzy match and confirm whether it is the same song.
7. Click **Merge Safely**.
8. `music-sync` creates a backup before changing the master library.
9. Phone/device-only tracks are added to the master library.
10. Copy the finished master library back to your device when you're ready.

Nothing in the project requires the destination device to be a Samsung A02s.

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
- Existing laptop/master files are not silently overwritten.
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

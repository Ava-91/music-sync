# Harmelune


`Harmelune` is a local music-library reconciliation and synchronization tool. It compares two independently maintained folders as **Library A** and **Library B**, lets you choose which library is authoritative, reviews ambiguous matches and conflicts, previews changes, creates verified backups, and applies a selected synchronization mode.

The product is intentionally generic: Library A and Library B can be ordinary local folders from different computers, removable storage, exports, backups, or other sources accessible to the application. It does not require a laptop/phone pairing.

## What it supports

### Libraries and sync modes

- **Library A / Library B** — two independently maintained music folders.
- **Master selection** — explicitly choose Library A or Library B as the master/source direction.
- **Safe** — synchronize without treating unconfirmed fuzzy matches as trusted identities.
- **Reconcile** — review and apply conflict decisions when both libraries contain different information for the same track.
- **Mirror** — apply the selected master direction as a mirror operation.
- **Dry run** — preview planned changes before applying them.

The GUI starts with a first-run setup wizard when configuration has not been initialized. Existing settings can be edited from the application and are persisted between runs.

### Matching and review

The matching engine combines multiple signals, including:

- metadata such as artist, title, and album
- duration and filename information
- exact identity and SHA-256 file hashing
- conservative fuzzy similarity
- embedded artwork comparisons

Strong matches can be accepted by the engine. Fuzzy matches are kept as **unconfirmed** until reviewed. Conflict and fuzzy-review screens expose the information needed to make an explicit decision, and unresolved fuzzy matches are not silently treated as confirmed matches.

### Safety and change control

The application is designed to make modifying operations explicit:

- library paths are validated centrally
- synchronization plans are protected against stale filesystem state
- backups are created and verified before modifying operations
- execution uses transaction/rollback safeguards
- partial failures are represented in execution results rather than silently ignored
- unreadable or unsafe inputs are handled conservatively
- dry-run can be used to inspect a plan before execution
- a successful restore invalidates the previous synchronization plan, so the application requires a fresh scan before another apply operation

No personal music collection or developer-specific library path is required by the product.

## Backup and restore

The configured backup location is used for backup operations. The GUI exposes a **Backup Manager** for both Library A and Library B.

From the Backup Manager you can:

1. inspect available backups for the selected library
2. select a backup
3. explicitly confirm restoration
4. restore through the existing verified restore engine
5. return to the main application with the previous synchronization plan discarded

Before restoration, the restore engine protects the current library. A failed restore is reported as a failure rather than being reported as successful.

## Reports and health

The application can produce authoritative execution reports and export them as JSON. Reports distinguish planned/executed outcomes and include filesystem paths in a normalized display form.

The health dashboard summarizes library and current-plan information such as track counts, metadata completeness, artwork coverage, duplicate groups, unreadable files, unresolved conflicts, unresolved fuzzy matches, and library-only tracks.

## Portable configuration

Portable mode is enabled by placing the application's portable marker beside the application. In portable mode, configuration is stored with the application rather than in the normal user configuration location.

Portable configuration stores application settings; it does not copy or bundle music-library contents into the application directory.

## First-run setup

On first launch, the setup wizard guides the user through:

1. Library A
2. Library B
3. master/source selection and synchronization mode
4. backup/settings configuration
5. path validation
6. saving the configuration

The wizard validates missing, inaccessible, identical, and nested library paths before accepting the configuration. Cancelling setup does not perform a synchronization.

## Installation and running from source

### Requirements

- Windows 10/11 for the supported packaged workflow
- Python 3.11+
- `mutagen`
- `Pillow`
- Tk support from the Python installation for the GUI

The runtime dependencies are declared in `requirements.txt`:

```powershell
python -m pip install -r requirements.txt
```

Then run the GUI directly:

```powershell
python app.py
```

For Windows source checkouts, the included launchers are also available:

```text
install.bat
run.bat
```

`install.bat` installs the runtime requirements. `run.bat` starts `app.py` from the repository directory.

### Windows executable

The repository contains a PyInstaller specification in `harmelune.spec` and a Windows version-resource file in `build/windows_version.txt`. The packaged application is built as a one-file executable named `harmelune.exe`.

The Windows GitHub Actions workflow builds the executable, verifies its version metadata and startup behavior, and uploads the resulting artifact. These automated checks are not a substitute for a complete interactive Windows GUI test; see **Validation status** below.

## Typical workflow

```text
First launch / load settings
        ↓
Choose Library A + Library B
        ↓
Choose master + sync mode
        ↓
Scan
        ↓
Review conflicts / fuzzy matches
        ↓
Dry run
        ↓
Create verified backup as part of modifying operation
        ↓
Apply Safe / Reconcile / Mirror
        ↓
Inspect execution report / health state
        ↓
Use Backup Manager or restore when needed
```

A restore clears the current synchronization plan. The libraries must be scanned again before another synchronization can be applied.

## Troubleshooting

### The application asks for libraries again

This is expected on an unconfigured or newly portable installation. Complete the first-run wizard or select the library paths in the main window.

### A fuzzy match cannot be applied

Review the fuzzy-match candidates. Unconfirmed fuzzy matches are intentionally blocked from being treated as trusted matches until an explicit decision is made.

### Apply is unavailable

Check that both libraries have been scanned and that the current plan has no unresolved requirements. If a restore or other state-changing operation invalidated the plan, scan both libraries again.

### Backup Manager cannot open

Check that the selected library exists and that a valid backup location is configured. The GUI validates the backup root before opening the manager.

### A restore fails

The Backup Manager reports the restore error and does not mark the operation as successful. Investigate the reported filesystem/backup problem before retrying.

### Windows EXE behavior differs from source execution

Use the packaged artifact produced by the Windows build workflow and verify its version/startup result. A successful automated startup smoke test confirms that the executable launches, but it does not prove every interactive GUI path.

## Development

The repository is organized around a small application layer and a `harmelune/` package containing scanning, matching, review, dry-run, execution, backup/restore, reporting, health, settings, and safety modules.

Runtime dependencies are in `requirements.txt`. Development/test dependencies are in `requirements-dev.txt`.

The repository includes a cross-platform pytest workflow at `.github/workflows/test.yml` and a Windows packaging workflow at `.github/workflows/build-windows.yml`.

Run the test suite locally with:

```powershell
python -m pytest -q
```

The tests cover matching, review behavior, path safety, stale-plan protection, backups/restore, settings, first-run setup, health calculations, filesystem edge cases, GUI contracts, and repository hygiene.

## Validation status

The release validation distinguishes implementation from real-world verification.

- **Ubuntu CI:** automated pytest runs are used for the supported test workflow.
- **Windows CI:** automated pytest runs are used for the Windows test workflow.
- **Windows EXE:** the packaging workflow builds `harmelune.exe`, verifies version metadata, and performs an automated startup smoke test.
- **Interactive Windows GUI:** the automated build/startup workflow does **not** prove the complete human GUI workflow. Full interactive validation must be performed in an actual interactive Windows environment before treating that release-gate item as verified.
- **Disposable realistic-library validation:** a real end-to-end test with temporary libraries should be treated separately from unit/contract tests.

Do not interpret a passing build or startup smoke test as proof of complete interactive Windows operation.

## Repository hygiene

Do not commit:

- personal music files
- personal artwork or metadata
- local configuration files
- private library paths
- credentials, tokens, or API keys
- Python caches or test artifacts
- generated build/distribution artifacts

Use disposable temporary directories for filesystem integration tests.

## License

MIT

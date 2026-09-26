# Project architecture and contributor workflow

Harmelune is intentionally split into small modules around a simple pipeline:

```text
GUI / app.py
    │
    ├── settings + first-run setup
    │
    ▼
Scanner
    │
    ▼
Matcher ──→ Match explanations
    │
    ▼
SyncPlan
    │
    ├── review / conflict decisions
    ├── dry-run preview
    │
    ▼
Safe / Reconcile / Mirror
    │
    ├── path validation
    ├── freshness validation
    ├── verified backup
    └── transaction execution
            │
            ▼
       execution result
            │
            ├── report
            └── health information
```

The GUI coordinates these pieces; the core modules own the underlying decisions and filesystem rules.

## Repository layout

At a high level:

```text
harmelune/
├── artwork.py / artwork_hash.py   Artwork extraction and hashing
├── backup.py / backups.py         Backup creation, verification, listing
├── backup_ui.py                   Backup Manager GUI
├── conflict_ui.py                 Conflict review UI
├── direction.py                   Explicit source/destination selection
├── display.py                     User-facing path formatting
├── dry_run.py                     Read-only operation previews
├── execution_report.py            Execution-report presentation/export
├── explain.py                     Human-readable match evidence
├── first_run.py                   First-run setup wizard
├── freshness.py                   Synchronization-plan freshness checks
├── fuzzy_ui.py                    Fuzzy-match review UI
├── hashing.py                     File hashing
├── health.py                      Read-only library/plan health calculations
├── matcher.py                     Track matching and plan construction
├── mirror.py                      Destructive master-direction execution
├── models.py                      Core data models and sync modes
├── path_safety.py                 Library/backup path validation
├── reconcile.py                   Explicit reconciliation execution
├── report.py                      Serializable synchronization report
├── review.py                      Conflict/review decisions
├── scanner.py                     Read-only library scanning
├── settings.py                    Configuration and portable mode
├── sync.py                        Safe-mode execution
└── transaction.py                 Filesystem transaction and rollback
```

The exact file list can evolve. The important boundary is that scanning, planning, review, and execution remain distinct responsibilities.

## Application layer

### app.py

The top-level application layer owns the Tkinter window and coordinates user interactions.

It should not become the place where matching algorithms or filesystem safety rules are reinvented. When changing the UI, prefer calling the existing core modules.

## Configuration

### settings.py

Settings are application configuration, not music-library data. The store handles Library A/B paths, master selection, synchronization mode, backup location, fuzzy threshold, conflict defaults, appearance, and normal/portable configuration locations.

### first_run.py

The first-run wizard collects and validates the initial configuration. It uses the shared path-safety functions instead of implementing a second set of path rules.

## Read-only planning pipeline

### scanner.py

Scanning is deliberately read-only. It discovers supported audio files and extracts metadata, duration, hashes, artwork information, and filesystem state. Unreadable files become scan errors instead of being modified.

### matcher.py

The matcher turns two scan results into a SyncPlan. Its responsibility is to answer which tracks appear to correspond and what evidence supports each pairing. It does not copy, replace, delete, or restore files.

### explain.py

The explanation layer converts matcher evidence into user-facing identities, reasons, and conflicts. Keeping this separate makes the matcher easier to test without tying the algorithm to the GUI.

### models.py

Core dataclasses such as Track, Match, ScanResult, and SyncPlan are shared between pipeline stages. Keep these models lightweight and avoid filesystem side effects in them.

## Review and preview

### review.py

Review decisions represent explicit choices for conflict-sensitive matches.

### fuzzy_ui.py and conflict_ui.py

These modules present review information and collect user decisions.

### dry_run.py

Dry run is intentionally read-only. It converts a plan into the operations that an apply would perform without modifying libraries or creating backups.

## Execution boundaries

### direction.py

A SyncDirection makes source/destination intent explicit. Do not infer a source from labels such as laptop or phone; the current product model uses Library A/B and explicit master selection.

### path_safety.py

Centralizes validation of library and backup paths. Execution code should call these shared validators instead of creating local path checks.

### freshness.py

Checks whether the filesystem still matches the fingerprint captured when the plan was built.

### sync.py

Implements Safe mode. Safe mode copies source-only tracks without deleting or overwriting existing destination files.

### reconcile.py

Implements explicit conflict reconciliation. It creates operations only for explicit decisions and does not delete files.

### mirror.py

Implements the intentionally destructive master-direction mode. Mirror can copy, replace, or delete files and requires explicit MIRROR confirmation.

## Backups and rollback

### backup.py

Creates and verifies timestamped library backups. Verification compares file sets, sizes, modification timestamps, and SHA-256 hashes against the stored manifest.

### backups.py and backup_ui.py

Provide backup discovery and the GUI Backup Manager around the core backup/restore engine.

### transaction.py

Owns filesystem execution and rollback. It receives already-planned operations and verified backups; it should not decide which tracks match.

If an operation fails, it attempts to restore affected libraries and reports rollback failures separately.

## Reporting and health

### report.py

Provides a serializable synchronization report containing counts such as added, replaced, skipped, matched, fuzzy, metadata conflicts, artwork conflicts, and scan errors.

### execution_report.py

Provides the authoritative execution-report presentation/export path used by the application.

### health.py

Calculates read-only library and plan health statistics such as metadata completeness, artwork coverage, duplicate groups, unreadable files, and unresolved plan items.

## Testing architecture

Tests live under tests/ and are grouped by responsibility.

Examples include:

- test_scanner.py — scanning
- test_matcher.py / test_explain.py — matching and explanations
- test_fuzzy_review.py / test_review.py — review behavior
- test_dry_run.py / test_dry_run_engine.py — previews
- test_sync_safe.py — Safe mode
- test_reconcile.py — reconciliation
- test_mirror.py — Mirror mode
- test_backup_restore.py / test_backup_verified.py / test_backups.py — backup behavior
- test_transaction.py — rollback and filesystem transactions
- test_path_safety.py — path validation
- test_freshness.py — stale-plan protection
- test_first_run.py — setup wizard contracts
- test_settings.py / test_portable_settings.py — configuration
- test_health.py / test_health_percentages.py — health calculations
- test_report.py / test_execution_report.py — reports
- test_filesystem_edge_cases.py — filesystem edge cases
- test_app_contract.py / test_restore_gui_contract.py — GUI contracts
- test_repository_hygiene.py — repository hygiene
- test_release_metadata.py — packaging metadata

Run the complete suite with:

```powershell
python -m pytest -q
```

## CI and packaging

### Test workflow

.github/workflows/test.yml runs pytest on Ubuntu and Windows using Python 3.11.

### Windows packaging workflow

.github/workflows/build-windows.yml installs development dependencies, runs pytest, builds harmelune.exe with PyInstaller, verifies executable/version metadata, performs a short startup smoke test, and uploads the executable artifact.

The smoke test verifies startup, not complete interactive GUI behavior.

## Contributor workflow

Use this loop for normal changes:

```text
Issue
  ↓
Understand + plan
  ↓
Create focused branch
  ↓
Implement small change
  ↓
Run tests / validation
  ↓
Open focused PR
  ↓
Review CI + diff
  ↓
Merge
  ↓
Close / link issue
```

Keep PRs focused. A documentation change should not quietly include unrelated product refactors. A safety change should include tests for the affected boundary. A UI change should preserve the underlying core behavior.

## Where to make a change

| Need | Preferred area |
| --- | --- |
| Discover/read audio files | scanner.py |
| Decide whether tracks correspond | matcher.py |
| Explain match evidence | explain.py |
| Collect user review choices | review.py, fuzzy_ui.py, conflict_ui.py |
| Preview operations | dry_run.py |
| Validate paths | path_safety.py |
| Detect stale plans | freshness.py |
| Safe copy behavior | sync.py |
| Explicit reconciliation | reconcile.py |
| Destructive mirror behavior | mirror.py |
| Create/verify backups | backup.py |
| Execute/rollback filesystem operations | transaction.py |
| Produce reports | report.py, execution_report.py |
| Calculate health | health.py |
| Persist configuration | settings.py |
| Package Windows executable | harmelune.spec, .github/workflows/build-windows.yml |

## Release mindset

Before a release-oriented change is merged:

- run the full test suite
- check the relevant Windows packaging workflow
- verify that user-facing documentation matches actual behavior
- avoid claiming interactive Windows validation when only CI smoke tests exist
- keep generated artifacts and personal library data out of the repository

For changes involving synchronization, backups, restore, or Mirror, test with disposable temporary libraries before touching an important real collection.
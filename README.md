# Harmelune

> **Two libraries. One collection.**

Harmelune is a local music-library reconciliation and synchronization tool for comparing, reviewing, backing up, and synchronizing two independently maintained music folders.

It is built around a simple idea: **make synchronization decisions visible before files are changed.**

[![Tests](https://img.shields.io/badge/tests-144%20passed-success)](https://github.com/Ava-91/harmelune/actions)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

## ✨ Highlights

- 🎵 Compare two independent music libraries as **Library A** and **Library B**
- 🧭 Choose the master/source direction explicitly
- 🔎 Match tracks using metadata, duration, filenames, hashes, fuzzy similarity, and artwork
- ⚠️ Keep uncertain fuzzy matches unconfirmed until they are reviewed
- 🧩 Review conflicts before applying reconciliation decisions
- 🧪 Preview changes with dry-run mode
- 💾 Create and verify backups before modifying operations
- ↩️ Restore libraries through a protected backup/restore flow
- 🛡️ Guard against unsafe paths, stale synchronization plans, and partial failures
- 📊 Inspect execution reports and library health information
- 💻 Run from source or build a standalone Windows executable

## 📚 Table of contents

- [How it works](#how-it-works)
- [Core features](#core-features)
- [Safety model](#safety-model)
- [Backup and restore](#backup-and-restore)
- [First-run setup](#first-run-setup)
- [Installation](#installation)
- [Windows executable](#windows-executable)
- [Typical workflow](#typical-workflow)
- [Portable mode](#portable-mode)
- [Reports and health](#reports-and-health)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Validation status](#validation-status)
- [Repository hygiene](#repository-hygiene)
- [License](#license)

## 🚀 New here?

Start with the **[Getting started guide](docs/getting-started.md)** for a beginner-friendly Windows walkthrough from installation through your first dry run.

## How it works

Harmelune treats synchronization as a **reviewable plan**, not an immediate file operation.

You provide two folders:

```text
Library A ─────┐
               ├── Scan → Match → Review → Plan → Backup → Apply
Library B ─────┘
```

The two libraries do not have to represent a specific device pairing. They can be:

- folders on different computers
- removable drives
- exported collections
- backups
- independently maintained copies of the same collection
- any other local folders accessible to the application

You choose which library is the master/source and which synchronization mode should be used.

## Core features

### 🎼 Library synchronization

See the detailed [synchronization workflow](docs/synchronization-workflow.md) for the scan → match → review → dry-run → backup → apply sequence.

Harmelune supports three primary apply modes:

| Mode | Purpose |
| --- | --- |
| **Safe** | Synchronize without treating unconfirmed fuzzy matches as trusted identities |
| **Reconcile** | Review and apply decisions when both libraries contain different information for the same track |
| **Mirror** | Apply the selected master direction as a mirror operation |

A **dry run** can be used to preview the planned changes before anything is applied.

### 🔍 Matching and review

See [matching and match explanations](docs/matching.md) for the matching order, fuzzy evidence, ambiguity rules, and conflict explanations.

The matching engine combines multiple signals:

- artist, title, and album metadata
- duration
- filename information
- exact identity
- SHA-256 file hashing
- conservative fuzzy similarity
- embedded artwork comparisons

Strong matches can be accepted automatically.

Fuzzy matches remain **unconfirmed** until they are explicitly reviewed. Harmelune does not silently turn an uncertain match into a trusted identity.

### 🛡️ Safety and change control

Modifying a music library is high-impact, so Harmelune puts several checks around the operation:

- library paths are validated centrally
- identical and nested library paths are rejected during setup
- synchronization plans are protected against stale filesystem state
- verified backups are created before modifying operations
- transaction/rollback safeguards protect execution
- partial failures are represented in execution results
- unreadable or unsafe inputs are handled conservatively
- a restore invalidates the previous synchronization plan
- a fresh scan is required before another apply operation after a restore

**A passing test or build is not a guarantee that a real library operation is safe. Always review the planned changes and keep independent backups of important files.**

## Backup and restore

See the [safety, backups, and recovery guide](docs/safety-and-recovery.md) before trusting Harmelune with an important collection.

The configured backup location is used for backup operations.

The **Backup Manager** lets you:

1. inspect available backups for a selected library
2. select a backup
3. explicitly confirm restoration
4. restore through the verified restore engine
5. return to the main application with the previous synchronization plan discarded

Before restoration, the restore engine protects the current library. A failed restore is reported as a failure rather than being presented as successful.

## First-run setup

When Harmelune has no initialized configuration, the GUI opens a setup wizard.

The wizard walks through:

1. **Library A**
2. **Library B**
3. **Master/source selection**
4. **Synchronization mode**
5. **Backup/settings configuration**
6. **Path validation**
7. **Saving the configuration**

It checks for missing, inaccessible, identical, and nested library paths before accepting the configuration.

Cancelling setup does **not** perform a synchronization.

## Installation

### Requirements

- Windows 10/11 for the supported packaged workflow
- Python 3.11+
- `mutagen`
- `Pillow`
- Tk support from the Python installation

Runtime dependencies are declared in `requirements.txt`.

```powershell
python -m pip install -r requirements.txt
```

Then launch the GUI:

```powershell
python app.py
```

For Windows source checkouts, the repository also includes:

```text
install.bat
run.bat
```

`install.bat` installs the runtime requirements.

`run.bat` starts `app.py` from the repository directory.

### Development dependencies

Install the test/development dependencies with:

```powershell
python -m pip install -r requirements-dev.txt
```

Run the test suite with:

```powershell
python -m pytest -q
```

## Windows executable

Harmelune can be packaged as a standalone one-file Windows executable.

The repository contains:

```text
harmelune.spec
build/
└── windows_version.txt
```

Build it locally with PyInstaller:

```powershell
python -m PyInstaller --clean --noconfirm harmelune.spec
```

The expected output is:

```text
dist/
└── harmelune.exe
```

The Windows GitHub Actions workflow also:

- installs dependencies
- runs the test suite
- builds `harmelune.exe`
- verifies executable/version metadata
- performs an automated startup smoke test
- uploads the executable as a workflow artifact

The startup smoke test only verifies that the packaged process launches and remains running briefly. It does **not** prove every interactive GUI path.

## Typical workflow

```text
First launch / load settings
          ↓
Choose Library A + Library B
          ↓
Choose master + sync mode
          ↓
Scan both libraries
          ↓
Review conflicts / fuzzy matches
          ↓
Run a dry run
          ↓
Create and verify backup
          ↓
Apply Safe / Reconcile / Mirror
          ↓
Inspect execution report / health state
          ↓
Restore through Backup Manager if needed
```

If a restore or another state-changing operation invalidates the plan, scan the libraries again before applying another synchronization.

## Portable mode

Portable mode stores application configuration alongside the application instead of using the normal user configuration directory.

Enable it by placing the Harmelune portable marker beside the application.

Portable configuration stores **application settings only**. It does not copy or bundle music-library contents into the application directory.

The application also retains compatibility with legacy portable/configuration locations where required for existing installations.

## Reports and health

Harmelune can produce authoritative execution reports and export them as JSON.

Reports distinguish planned and executed outcomes and normalize filesystem paths for display.

The health dashboard can summarize information such as:

- track counts
- metadata completeness
- artwork coverage
- duplicate groups
- unreadable files
- unresolved conflicts
- unresolved fuzzy matches
- library-only tracks
- current synchronization-plan state

## Troubleshooting

For a fuller decision tree and FAQ, see [Troubleshooting and FAQ](docs/troubleshooting.md).

### The application asks for libraries again

This is expected on an unconfigured or newly portable installation.

Complete the first-run wizard or select the library paths in the main window.

### A fuzzy match cannot be applied

Review the available candidates.

Unconfirmed fuzzy matches are intentionally prevented from being treated as trusted matches until an explicit decision is made.

### Apply is unavailable

Make sure both libraries have been scanned and that the current plan has no unresolved requirements.

If a restore or another state-changing operation invalidated the plan, scan both libraries again.

### Backup Manager cannot open

Check that the selected library exists and that a valid backup location is configured.

The GUI validates the backup root before opening the manager.

### A restore fails

The Backup Manager reports the restore error and does not mark the operation as successful.

Investigate the reported filesystem or backup problem before retrying.

### The Windows EXE behaves differently from source execution

Use the artifact produced by the Windows build workflow and check its version/startup result.

Remember that an automated startup smoke test does not cover the complete interactive GUI.

## Development

See the [project architecture and contributor workflow](docs/architecture.md) for module responsibilities, test layout, CI, packaging, and contribution guidance.

The repository is organized around a small application layer and the `harmelune/` package.

Major areas include:

```text
harmelune/
├── scanning
├── matching
├── review
├── dry-run planning
├── execution
├── backup / restore
├── reporting
├── health
├── settings
└── safety
```

The exact module layout may evolve as the project develops.

### Tests

The test suite covers areas including:

- matching behavior
- review behavior
- path safety
- stale-plan protection
- backup and restore
- settings and portable configuration
- first-run setup
- health calculations
- filesystem edge cases
- GUI contracts
- repository hygiene

Run everything locally:

```powershell
python -m pytest -q
```

### CI

The repository includes:

- `.github/workflows/test.yml` for automated tests
- `.github/workflows/build-windows.yml` for Windows packaging and executable validation

## Validation status

Harmelune distinguishes automated validation from real-world verification.

| Area | Current validation |
| --- | --- |
| Ubuntu test workflow | Automated pytest |
| Windows test workflow | Automated pytest |
| Windows executable | PyInstaller build + metadata checks + startup smoke test |
| Interactive Windows GUI | Requires actual interactive validation |
| Realistic end-to-end library test | Should be validated separately with disposable test libraries |

A green CI run means the automated checks passed. It should **not** be interpreted as proof of complete interactive Windows operation or as a substitute for backups and careful review of a real music collection.

## Repository hygiene

Do not commit:

- personal music files
- personal artwork or metadata
- local configuration files
- private library paths
- credentials, tokens, or API keys
- Python caches
- test artifacts
- generated build/distribution artifacts

Use disposable temporary directories for filesystem integration tests.

## Project status

Harmelune is actively developed.

The repository is currently focused on making two-library synchronization predictable, reviewable, and recoverable rather than hiding destructive operations behind a single automatic sync button.

For planned work and known limitations, see the repository's [Issues](https://github.com/Ava-91/harmelune/issues).

## License

Harmelune is released under the [MIT License](LICENSE).

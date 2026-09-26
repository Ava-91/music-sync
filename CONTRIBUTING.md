# Contributing to Harmelune

Thanks for helping improve Harmelune.

## Before opening an issue

- Search existing issues first.
- For bugs, include the smallest reproducible description you can.
- Do not upload personal music files, private library paths, credentials, tokens, or other sensitive data.
- If the issue concerns a synchronization operation, describe the two-library setup without exposing private filenames or metadata.

## Development workflow

Harmelune follows a focused branch → pull request → validation → merge workflow.

1. Start from an up-to-date `main`.
2. Create a focused branch for one change.
3. Make the smallest clear implementation or documentation change.
4. Run the relevant tests locally.
5. Open a pull request with a concise summary and validation notes.
6. Address review or CI feedback before merging.

Keep unrelated cleanup out of feature or bug-fix pull requests.

## Local setup

Install runtime dependencies:

```powershell
python -m pip install -r requirements.txt
```

Install development dependencies:

```powershell
python -m pip install -r requirements-dev.txt
```

Run the test suite:

```powershell
python -m pytest -q
```

Build the Windows executable:

```powershell
python -m PyInstaller --clean --noconfirm harmelune.spec
```

## Safety-sensitive changes

Changes involving matching, path validation, backups, restore, planning, or file execution should include tests for the relevant safety behavior.

Do not weaken a safety check merely to make a happy-path test pass.

## Documentation

User-facing behavior should be documented when practical. Keep examples Windows-friendly and avoid documenting internal compatibility identifiers as current product branding.

## Pull requests

A good pull request should make it easy to answer:

- What changed?
- Why was it needed?
- How was it validated?
- Are there compatibility or safety considerations?


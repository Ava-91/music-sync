# Troubleshooting and FAQ

This page is a practical first stop when Harmelune does not behave as expected.

> **Rule of thumb:** if a plan looks wrong, do not apply it while troubleshooting. Preserve the evidence, check the relevant paths and settings, and scan again when the filesystem may have changed.

## Quick diagnosis

| Symptom | Start here |
| --- | --- |
| Setup keeps asking for folders | Check settings/portable mode and complete the first-run wizard |
| Library is not detected | Verify the folder exists, is a directory, and is accessible |
| A track is unmatched | Review metadata, filename, duration, and possible fuzzy candidates |
| A fuzzy match looks wrong | Read the match explanation and resolve it explicitly |
| Conflicts remain | Review title, artist, album, and artwork differences |
| Apply is blocked | Check scan freshness, unresolved decisions, and path validation |
| Backup cannot be created | Check the backup directory and free space |
| Restore fails | Preserve the error, verify the backup, and do not reuse an old plan |
| EXE will not start | Check the packaged artifact/version and launch it from a writable, accessible location |
| You need more help | Collect the diagnostic information listed at the end of this page |

## Library not detected or inaccessible

Harmelune requires each library to be an existing, accessible directory.

Check:

1. The path points to the folder you actually intend to use.
2. The folder still exists.
3. You can open it in Windows Explorer.
4. You have permission to read and traverse it.
5. It is not the same directory as the other library.
6. Neither library is nested inside the other.

If the library is on removable or network-backed storage, make sure the storage is connected and available before starting a scan.

## The scan finds fewer tracks than expected

The scanner considers supported audio extensions, including:

```text
.mp3 .m4a .m4b .flac .wav .ogg .opus .aac .wma
```

For a missing track:

- check its extension
- confirm the file is actually inside the selected library
- check whether the file can be opened
- look for scan errors
- make sure the file was not added after the scan completed

If the filesystem changed after scanning, perform a fresh scan.

## A track is unmatched

An unmatched track is not necessarily a bug.

Harmelune intentionally avoids forcing weak or ambiguous pairings.

Check:

- title metadata
- artist metadata
- album metadata
- filename
- duration
- file contents/hash
- artwork

A track can remain library-only when no unique strong match or sufficiently separated fuzzy candidate is available.

See [Matching and match explanations](matching.md) for the matching rules.

## A fuzzy match looks wrong

Do not apply the plan simply because a fuzzy match was found.

Open the match explanation and inspect:

- overall similarity
- title similarity
- filename similarity
- artist similarity
- album similarity
- duration evidence

Remember that a fuzzy match is initially **unconfirmed**.

If the evidence does not support the pairing, resolve or skip it rather than forcing the match.

## Metadata or artwork conflicts

A pair can match successfully and still contain differences.

Harmelune can report conflicts for:

- title
- artist
- album
- embedded artwork

A conflict is a review item, not automatically an error.

In Reconcile mode, choose which side to keep or skip the item according to the available decisions.

## Apply is blocked

First check the current plan.

Common reasons include:

### The plan is stale

The libraries changed after scanning.

**Fix:** scan both libraries again, review the new plan, and run another dry run.

### A required decision is missing

Reconcile mode blocks unresolved required decisions.

**Fix:** review fuzzy matches and conflict-sensitive items and make an explicit decision or skip them.

### A path is unsafe

Identical/nested libraries or overlapping backup locations are rejected.

**Fix:** choose independent directories.

### Mirror still has fuzzy matches

Mirror refuses to proceed while fuzzy matches remain unresolved.

**Fix:** review and resolve the fuzzy matches, then rebuild the plan if needed.

## Backup problems

### Backup location overlaps a library

Harmelune rejects a backup root that is the same as, inside, or contains a library.

Choose a separate backup directory.

### Backup verification fails

A backup is verified against its manifest using file sets, sizes, modification times, and SHA-256 hashes.

If verification fails, do not treat the backup as usable protection.

Check:

- available disk space
- filesystem errors
- permissions
- whether another process is changing files during backup

Retry only after the underlying problem is understood.

## Restore fails

A restore requires exact confirmation:

```text
RESTORE
```

Before restoring, Harmelune creates a safety backup of the current target.

If restore fails, the application reports the failure and attempts to recover the target from that safety backup.

If recovery also fails:

1. stop modifying the affected library
2. save the exact error message
3. preserve the backup directory
4. check disk space and permissions
5. avoid repeatedly retrying destructive operations
6. collect the diagnostic information below

After a successful restore, the old synchronization plan is invalid. Scan again before another apply.

## The Windows EXE does not start

The automated Windows build performs a short startup smoke test, but that test does not cover every interactive GUI path.

Try:

1. Confirm you have the expected `harmelune.exe`.
2. Check its version metadata if available.
3. Move it to a writable local directory if it is being launched from a restricted location.
4. Start it directly from Windows.
5. If you built it yourself, run the PyInstaller build again from a clean checkout.
6. Compare source execution with packaged execution if Python is available.

For a packaged build problem, record whether the process exits immediately or remains open but fails to show the expected window.

## Settings keep disappearing

Harmelune stores application settings separately from music-library contents.

Check whether you are running:

- normal mode, which uses the user configuration directory
- portable mode, which stores configuration beside the application

Portable mode is opt-in through the Harmelune portable marker.

Existing installations may also have legacy configuration compatibility, so do not delete old configuration directories while troubleshooting unless you know they are no longer needed.

## The application asks for setup again

This can happen when:

- settings have never been initialized
- the selected configuration location is different
- portable mode is active
- the settings file cannot be read or fails validation

Complete the wizard again and verify that the selected libraries and backup location are correct.

## The execution report looks unexpected

Reports contain counts for:

- added files
- replaced files
- skipped files
- matched tracks
- fuzzy matches
- metadata conflicts
- artwork conflicts
- scan errors

Compare those counts with the dry-run preview and the execution result.

If the numbers do not make sense, stop before another apply and collect the diagnostic information.

## FAQ

### Does Harmelune delete files in Safe mode?

No. Safe mode copies source-only tracks and does not delete destination files or overwrite an existing destination file.

### Can a fuzzy match be applied automatically?

Not as a trusted identity. Fuzzy matches start unconfirmed and require review.

### Does a dry run create a backup?

No. Dry run is a preview. Modifying execution is where verified backups are created.

### Can Reconcile delete files?

The current Reconcile implementation does not delete files. It applies explicit copy/replace decisions or skips/blocks them.

### Can Mirror delete files?

Yes. Mirror can delete destination-only tracks because its purpose is to make the selected master direction authoritative. It requires explicit `MIRROR` confirmation and a verified backup.

### What happens if a file changes after scanning?

The synchronization plan can become stale. Harmelune validates freshness before applying and blocks an outdated plan so you can scan again.

### Does restoring a backup leave the old plan usable?

No. Restore invalidates the previous synchronization plan. Perform a fresh scan.

### Does Harmelune upload my music?

The application is designed around local filesystem operations. The repository's synchronization workflow does not require uploading your music collection to a remote service.

## What to collect for a bug report

Avoid attaching personal music files or private paths unless absolutely necessary.

Instead provide:

- Harmelune version/commit
- Windows version
- source vs packaged EXE
- exact steps to reproduce
- expected behavior
- actual behavior
- exact error message
- whether the problem occurs with disposable test folders
- whether a fresh scan changes the result
- whether the issue is repeatable

If paths appear in an error, replace personal path components with placeholders such as `C:\MusicA` and `D:\MusicB` before posting publicly.

## Related guides

- [Getting started](getting-started.md)
- [Synchronization workflow](synchronization-workflow.md)
- [Matching and match explanations](matching.md)
- [Safety, backups, and recovery](safety-and-recovery.md)
- [Project architecture and contributor workflow](architecture.md)

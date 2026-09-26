# Synchronization workflow

Harmelune treats synchronization as a sequence of **scan → match → review → preview → protect → apply → verify** steps.

The important rule is simple:

> **A scan and plan describe what Harmelune knows. An apply operation changes files only after the required checks and confirmations pass.**

## 1. Scan both libraries

The scanner recursively discovers supported audio files and reads information such as:

- title
- artist
- album
- duration
- file size and modification time
- SHA-256 file hash
- embedded artwork information

Scanning is read-only. Files that cannot be read or parsed are reported as scan errors instead of being modified.

Harmelune also records a filesystem fingerprint used later to detect stale plans.

## 2. Build the comparison

The matcher compares Library A and Library B using several signals, in order:

1. byte-identical SHA-256 hashes
2. normalized artist/title-or-filename/album metadata
3. normalized filename plus duration or artist agreement
4. conservative fuzzy similarity

The result is a synchronization plan containing:

- tracks found only in Library A
- tracks found only in Library B
- matched track pairs
- confidence and match type
- metadata conflicts
- artwork conflicts
- evidence explaining why a pair matched

## 3. Review the plan

Before applying anything, inspect:

- library-only tracks
- confirmed matches
- fuzzy matches
- metadata conflicts
- artwork conflicts
- scan errors

### Fuzzy matches

A fuzzy match is intentionally **unconfirmed**.

The matcher uses a weighted similarity calculation based on title, filename, artist, album, and duration. A candidate also has to clear the configured threshold and have enough separation from the next-best candidate.

The UI exposes the evidence behind the match. If the evidence does not make sense, resolve the item explicitly instead of trusting the suggestion.

### Conflicts

A matched pair can still have differences in:

- title
- artist
- album
- embedded artwork

Reconcile mode requires explicit decisions for conflict-sensitive or unconfirmed matches.

## 4. Run a dry run

Dry-run functions build the operations that an apply would perform without:

- changing library files
- creating backups
- deleting files
- replacing files

The preview can show copy, replace, delete, skipped, and blocked operations depending on the selected mode.

Use the dry run as the final opportunity to catch an unexpected direction or operation.

## 5. Protect the libraries

Before a modifying operation, Harmelune validates the library paths and backup location.

It rejects:

- identical libraries
- nested libraries
- inaccessible library roots
- backup locations overlapping libraries
- stale synchronization plans

Modifying operations create verified backups of affected libraries before execution.

A backup is verified using its stored manifest, file set, sizes, modification times, and SHA-256 hashes.

## 6. Apply the selected mode

### Safe

Safe mode copies source-only tracks into the destination without treating unconfirmed fuzzy matches as trusted identities.

It is intended for conservative synchronization.

### Reconcile

Reconcile mode applies only explicit decisions.

Depending on the decision, a user can:

- copy Library A to Library B
- copy Library B to Library A
- keep Library A
- keep Library B
- skip an item

Unresolved required decisions block the operation.

Reconcile execution does not delete files.

### Mirror

Mirror mode makes the selected master/source direction authoritative.

Its preview can contain:

- copies for source-only tracks
- replacements where matched files differ
- deletions for tracks existing only on the destination

Mirror is destructive because destination-only files can be deleted.

It therefore requires:

1. a fresh plan
2. all fuzzy matches resolved
3. a verified backup
4. exact confirmation text: `MIRROR`

## 7. Transaction and rollback behavior

File operations are executed through the transaction layer.

If an operation fails:

1. execution stops
2. the failure is recorded
3. affected libraries are restored from their verified backups
4. rollback success or rollback failure is reported explicitly

A successful rollback is not hidden: the execution result records that the transaction was rolled back.

If rollback itself fails, the result is marked partial and reports the recovery errors.

## 8. Verify the result

After execution, inspect the result and generated report.

Reports record counts for:

- added files
- replaced files
- skipped files
- matched tracks
- fuzzy matches
- metadata conflicts
- artwork conflicts
- scan errors

The health view can also summarize metadata completeness, artwork coverage, duplicate groups, unreadable files, and unresolved plan issues.

## 9. Restore when necessary

The Backup Manager can restore a verified backup after explicit `RESTORE` confirmation.

Before restoring, Harmelune creates a safety backup of the current target library.

After a restore, the previous synchronization plan is invalidated. Run a fresh scan before applying another synchronization.

## Example: a normal Safe-mode session

Suppose Library A contains:

```text
Music/
├── Artist A/
│   └── Song One.flac
└── Artist B/
    └── Song Two.mp3
```

and Library B contains only `Song One.flac`.

A typical session is:

```text
Scan A + B
   ↓
Song One → confirmed match
Song Two → Library A only
   ↓
Review
   ↓
Dry run
   ↓
1 copy: Song Two → Library B
   ↓
Verified backup
   ↓
Apply Safe
   ↓
Execution report
```

No file should be treated as "mysteriously synchronized": the plan shows what was matched and what operation is about to happen.

## If the plan looks wrong

Stop before applying.

Check:

- whether the correct master was selected
- whether both library paths are correct
- whether a fuzzy match needs review
- whether metadata or artwork conflicts are expected
- whether the libraries changed after scanning
- whether the backup location is separate

If the filesystem changed after the scan, rebuild the plan rather than trying to force an old plan through execution.

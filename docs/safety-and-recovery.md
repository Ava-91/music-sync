# Safety, backups, and recovery

Harmelune is designed to make synchronization **reviewable and recoverable**, but no software can guarantee that every real-world filesystem operation is safe.

The safest workflow is:

```text
Scan
  ↓
Review
  ↓
Dry run
  ↓
Verified backup
  ↓
Apply
  ↓
Inspect result
```

Keep an independent backup of important music outside Harmelune as well.

## Path safety

Before modifying libraries, Harmelune validates the selected paths.

Library A and Library B must:

- exist
- be directories
- be readable and accessible
- be different directories
- not contain one another

The backup location must also be separate from the libraries it protects.

This prevents configurations such as:

- Library A = Library B
- Library A inside Library B
- Library B inside Library A
- backup directory inside a library
- library directory inside the backup root

These checks are intended to prevent accidental recursive copies and overlapping operations.

## Review before apply

Harmelune builds a synchronization plan before changing files.

Review:

- the selected master/source
- the destination
- library-only tracks
- fuzzy matches
- metadata conflicts
- artwork conflicts
- blocked items
- scan errors
- the exact operations shown by the dry run

Do not treat a green CI check, a high match score, or a successful dry run as proof that a real collection is safe to modify.

## Dry-run safety

Dry-run mode is read-only.

It builds the operations that would be applied without:

- modifying music files
- creating backups
- deleting files
- replacing files

This makes dry run useful for inspecting a plan, but it has an important limitation:

> A dry run is a preview of the filesystem state observed when the plan is built. It is not a lock on the filesystem.

If files change after scanning or while preparing to apply, the plan can become stale.

## Stale-plan protection

Harmelune records a filesystem fingerprint during scanning.

Before an apply operation, the current filesystem state is checked against the plan.

If the relevant library changed, the operation is rejected instead of silently applying an old plan.

The correct recovery is:

1. stop the current apply
2. scan the affected libraries again
3. review the new plan
4. run another dry run
5. apply only after the new plan is understood

## Verified backups

Modifying operations create backups before changing affected libraries.

Backups contain a manifest describing the backed-up files.

Verification checks:

- the file set
- file sizes
- modification timestamps
- SHA-256 hashes

If verification fails, the backup is not accepted as a valid protection for the operation.

Backup locations must not overlap the libraries being modified.

## What each mode protects

### Safe mode

Safe mode copies source-only tracks.

It does **not** delete destination files and does **not** overwrite an existing destination file. Existing destinations are skipped.

A verified backup of the destination is created before planned copies are executed.

### Reconcile mode

Reconcile mode applies only explicit decisions for items that need a decision.

It does not delete files.

Before changing an affected library, it creates and verifies a backup of that library.

If the transaction fails, the transaction layer attempts to restore affected libraries from those backups.

### Mirror mode

Mirror mode is different.

It can:

- copy source-only tracks
- replace different destination files
- delete destination-only tracks

Because deletion is part of its purpose, Mirror requires exact confirmation:

```text
MIRROR
```

It also requires a verified backup and blocks unresolved fuzzy matches.

Do not use Mirror merely because it is convenient. Use it only when the selected master and destination state are intentional.

## Transaction rollback

Harmelune executes modifying operations through a transaction layer.

If an operation fails:

1. the transaction stops
2. the failure is recorded
3. affected libraries are restored from verified backups
4. the result records whether rollback succeeded

Possible outcomes include:

- **SUCCESS** — all requested operations completed
- **FAILED** — an operation failed
- **BLOCKED** — required safety or review conditions prevented execution
- **PARTIAL** — execution or recovery encountered an additional failure

A rollback failure is especially important and is surfaced rather than hidden.

## Restore workflow

The Backup Manager can restore a verified backup.

Restore requires exact confirmation:

```text
RESTORE
```

Before replacing the target library contents, Harmelune creates a safety backup of the current target.

The restore process then:

1. validates the selected backup
2. protects the current target with a safety backup
3. restores the selected backup
4. verifies the restored target
5. reports success or recovery failure

If restoration fails partway through, Harmelune attempts to recover the previous target from the safety backup.

## What recovery does not guarantee

Recovery is a safety mechanism, not a guarantee against every possible failure.

For example, recovery can still be affected by:

- disk failure
- permission changes
- files becoming inaccessible
- insufficient storage
- external filesystem problems
- hardware or operating-system failures

If rollback itself fails, preserve the reported error information and avoid repeatedly modifying the affected library until the problem is understood.

## After a restore

A restore invalidates the previous synchronization plan.

Do not reuse an old plan after restoring.

Instead:

```text
Restore
  ↓
Fresh scan
  ↓
New plan
  ↓
Review
  ↓
New dry run
  ↓
Apply
```

## Independent backups

For irreplaceable music, keep at least one independent backup outside the directories Harmelune is operating on.

Good backup targets include storage that is not simultaneously being modified by the synchronization operation.

Harmelune's backup is an operational safety mechanism; it should not be treated as your only archival copy.

## Safety checklist

Before a real synchronization:

- [ ] Library A is the intended folder
- [ ] Library B is the intended folder
- [ ] Master/source direction is correct
- [ ] Backup location is separate from both libraries
- [ ] Both libraries were scanned recently
- [ ] Fuzzy matches were reviewed
- [ ] Metadata/artwork conflicts were understood
- [ ] Dry-run operations look correct
- [ ] Important files have an independent backup
- [ ] You understand whether the selected mode can delete or replace files

If any box is unclear, stop and review the plan before applying it.

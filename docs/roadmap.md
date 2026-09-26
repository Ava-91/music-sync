# Documentation roadmap

Harmelune's v1.1 documentation pass is complete.

The documentation is organized around the user journey:

```text
Discover
  ↓
Install
  ↓
Understand the workflow
  ↓
Understand matching
  ↓
Understand safety and recovery
  ↓
Troubleshoot
  ↓
Contribute
```

## User-facing documentation

| Guide | Purpose | Status |
| --- | --- | --- |
| [Getting started](getting-started.md) | Fresh Windows setup through the first dry run | Complete |
| [Synchronization workflow](synchronization-workflow.md) | Scan → match → review → dry run → backup → apply → verify | Complete |
| [Matching and match explanations](matching.md) | Matching evidence, fuzzy similarity, ambiguity, and conflicts | Complete |
| [Safety, backups, and recovery](safety-and-recovery.md) | Safety boundaries, backups, rollback, restore, and recovery | Complete |
| [Troubleshooting and FAQ](troubleshooting.md) | Common problems, FAQ, and useful bug-report diagnostics | Complete |

## Contributor documentation

| Guide | Purpose | Status |
| --- | --- | --- |
| [Architecture and contributor workflow](architecture.md) | Module responsibilities, tests, CI, packaging, and contribution workflow | Complete |

## README integration

The README links the major guides from the sections where they are most useful.

The intended path for a new user is:

1. Start with [Getting started](getting-started.md).
2. Read the [Synchronization workflow](synchronization-workflow.md).
3. Review [Matching and match explanations](matching.md).
4. Read [Safety, backups, and recovery](safety-and-recovery.md) before using an important collection.
5. Use [Troubleshooting and FAQ](troubleshooting.md) when something is unclear.
6. Contributors can continue with [Architecture and contributor workflow](architecture.md).

## Documentation rules

Documentation should:

- describe actual current behavior
- distinguish automated validation from real-world validation
- avoid promising safety guarantees the implementation cannot provide
- keep destructive operations clearly identified
- explain uncertainty rather than hiding it
- use Harmelune's current product terminology
- avoid reintroducing obsolete active branding
- keep user instructions separate from implementation detail where possible

Feature changes that alter behavior should update the relevant guide as part of the same change.

## Maintenance

This roadmap is a snapshot of the v1.1 documentation pass, not a promise that documentation will never change.

When product behavior changes, update the affected guide and README links instead of letting documentation drift.

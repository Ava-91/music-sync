# Matching and match explanations

Harmelune does not decide that two files are the same from a filename alone.

It builds matches from multiple pieces of evidence and records **why** each pair was matched.

## Matching order

For each track in Library A, Harmelune considers Library B candidates in this order:

1. **SHA-256 hash**
2. **Normalized metadata**
3. **Filename + duration or artist**
4. **Conservative fuzzy similarity**

Once a Library B track is used by a stronger match, it is not reused by a later matching stage.

## 1. SHA-256 exact matches

If both files have the same SHA-256 hash and that hash identifies exactly one unused candidate, Harmelune creates a confirmed **exact match**.

The explanation shown for this kind of match is:

> Byte-identical SHA-256

A matching hash is strong evidence that the file contents are identical.

## 2. Normalized metadata matches

If the hash stage does not match a track, Harmelune compares a normalized metadata key containing:

- artist
- title, falling back to the filename stem when title metadata is empty
- album

Normalization makes comparisons less sensitive to case, accents, punctuation, and repeated whitespace.

A unique candidate produces a confirmed **metadata match**.

The explanation identifies the normalized artist/title-or-filename/album key as the evidence.

## 3. Filename matches

If metadata does not produce a unique match, Harmelune can compare normalized filename stems.

A filename candidate is accepted when:

- the filename stem matches after normalization, and
- either duration is within **2 seconds** or the normalized artist matches.

This creates a confirmed **filename match**.

The explanation can include the duration difference and artist agreement when those signals are available.

## 4. Fuzzy matches

Remaining candidates are scored using a weighted similarity:

| Signal | Weight |
| --- | ---: |
| Title similarity | 45% |
| Filename similarity | 15% |
| Artist similarity | 20% |
| Album similarity | 10% |
| Duration agreement | 10% |

The configured fuzzy threshold defaults to **0.88**.

A fuzzy candidate is considered only when:

- its score reaches the threshold, and
- it is sufficiently separated from the next-best candidate by at least **0.03**

This reduces the chance of choosing between two nearly equivalent candidates.

### Fuzzy matches are not automatically trusted

Even when a fuzzy candidate clears the threshold, Harmelune creates it as:

> **Fuzzy match — review required**

The match remains unconfirmed until the user explicitly reviews it.

The explanation can show:

- overall fuzzy similarity
- title similarity
- filename similarity
- artist similarity
- album similarity
- duration difference or unavailable duration

## What "confidence" means

The confidence value is the matching score produced by the matcher.

It is **evidence for the pairing**, not a guarantee that the two files represent the same real-world recording.

A 98% filename match, for example, does not mean there is a 98% probability that the tracks are identical.

Treat the value as a comparison signal and inspect the reasons when a match matters.

## Match explanations

Every generated match carries a match type and evidence.

Typical identities are:

| Match type | User-facing identity |
| --- | --- |
| Hash | Exact match |
| Metadata | Confirmed metadata match |
| Filename | Confirmed filename match |
| Fuzzy + unconfirmed | Fuzzy match — review required |
| Fuzzy + explicitly confirmed | Confirmed fuzzy match |

The explanation also detects differences in:

- title
- artist
- album
- embedded artwork

Artwork differences are reported separately because two files can represent the same track while containing different embedded artwork.

## Ambiguous candidates

Harmelune does not force a fuzzy match when the evidence is too close.

For fuzzy matching, if the best candidate does not clear the threshold or does not have enough separation from the next-best candidate, no fuzzy match is created.

The track can therefore remain on the library-only side of the plan rather than being paired with a weak candidate.

This is intentional: **an unmatched track is safer than a confidently wrong match.**

## Duplicate and one-to-many situations

The matcher keeps track of which Library B candidates have already been used.

This prevents the same Library B track from being assigned to multiple Library A tracks during the normal matching pass.

If multiple candidates share a hash, metadata key, or filename key, the corresponding stage only accepts a unique candidate. Ambiguous candidates continue to later stages instead of being arbitrarily selected.

## Conflicts after a successful match

A match and a conflict are different things.

A pair can be successfully matched while still having:

- different title metadata
- different artist metadata
- different album metadata
- different embedded artwork

These differences are surfaced as metadata/artwork conflicts so the user can decide what should be preserved during reconciliation.

## What to do when a match looks wrong

Do not apply the plan just because a match exists.

1. Open the match details.
2. Read the evidence.
3. Compare the title, artist, album, filename, duration, and artwork information.
4. Check whether another candidate would make more sense.
5. Resolve the item explicitly when the workflow asks for a decision.
6. If the evidence is not trustworthy, skip it rather than forcing a pairing.

For fuzzy matches, the intended behavior is to **review first, apply later**.

## Practical examples

### Example A — exact duplicate

Two files have identical SHA-256 hashes.

Result:

```text
Exact match
└── Evidence: Byte-identical SHA-256
```

No fuzzy review is needed for the identity itself.

### Example B — same metadata, different encoding

Two files have the same normalized artist, title, and album but different file contents.

Result:

```text
Confirmed metadata match
└── Evidence: normalized artist/title/album key
```

The match can still have file or artwork differences that matter to a later reconciliation decision.

### Example C — plausible typo

One filename is slightly different, but title, artist, album, and duration are otherwise close.

If the candidate reaches the fuzzy threshold and has enough separation from the next candidate:

```text
Fuzzy match — review required
├── Overall similarity
├── Title similarity
├── Filename similarity
├── Artist similarity
├── Album similarity
└── Duration evidence
```

The user still needs to review it.

### Example D — two equally plausible candidates

If two candidates are too close to each other, Harmelune does not force a fuzzy pairing.

The safer result is an unmatched track that can be reviewed manually.

## What the matcher does not promise

Harmelune's matcher does **not** promise:

- perfect identification of every recording
- semantic understanding of music
- reliable matching from filename alone
- automatic resolution of every duplicate
- that a high confidence score guarantees correctness
- that artwork similarity proves track identity

The matching system is deliberately evidence-based and conservative. Human review remains part of the workflow for uncertain or conflicting cases.

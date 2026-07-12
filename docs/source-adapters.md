# Source Adapters

Source adapters ingest approved private content into the retrieval pipeline.

## Scope

- Private markdown loaders
- Approved internal folders
- Normalization for evidence ingestion

## Rules

- Only approved source locations
- No credentials in source control
- No public documentation of private paths

## Environment variables

```text
SOURCE_ROOT=/path/to/approved/source
SOURCE_ALLOWLIST=/path/to/approved/source1,/path/to/approved/source2
```

## How to use

1. Point `SOURCE_ROOT` at the approved private root.
2. Add one or more subfolders to `SOURCE_ALLOWLIST`.
3. Load approved markdown files only.
4. Fetch files by relative resource id, for example `docs/policy.md`.

## Current first-stage adapter

The current Stage 1 implementation uses a read-only private markdown loader:

- lists approved `.md` and `.markdown` files,
- fetches content with normalized newlines and trimmed trailing whitespace,
- returns file metadata such as path, size, and modified time,
- rejects attempts to escape the approved root.

# Source Adapters

Source adapters ingest approved private content into the retrieval pipeline.

## Scope

- Private markdown loaders
- Built-in public document adapters for PDF, DOCX, HTML, TXT, and Markdown
- Built-in public website adapter for allowlisted live URLs
- Built-in public GitHub repository ingestion adapter
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
PDF support requires: pip install -e ".[pdf]"
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

## Built-in public adapters

Public adopters can start with the built-in adapters exposed from `enterprise_adapters`:

- `AllowlistedDocumentSourceAdapter` for Markdown, TXT, HTML, DOCX, and PDF files
- `AllowlistedWebsiteSourceAdapter` for exact allowlisted live URLs
- `GitHubRepositorySourceAdapter` for allowlisted GitHub repositories and paths

Example:

```python
from pathlib import Path
from enterprise_adapters import (
    AllowlistedDocumentSourceAdapter,
    AllowlistedWebsiteSourceAdapter,
    GitHubRepositorySourceAdapter,
)

docs = AllowlistedDocumentSourceAdapter(
    source_root=Path("/approved/docs"),
    allowed_roots=[Path("/approved/docs/kubernetes")],
)

web = AllowlistedWebsiteSourceAdapter(
    allowed_urls=["https://kubernetes.io/docs/concepts/workloads/pods/"],
)

repo = GitHubRepositorySourceAdapter(
    repository="kubernetes/website",
    allowed_paths=["content/en/docs"],
)
```

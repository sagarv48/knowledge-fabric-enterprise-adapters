from __future__ import annotations

from pathlib import Path

import pytest

from enterprise_adapters.source_adapters import PrivateMarkdownSourceAdapter


def test_list_resources_only_includes_allowed_markdown(tmp_path: Path) -> None:
    source_root = tmp_path / "approved"
    allowed_root = source_root / "docs"
    allowed_root.mkdir(parents=True)
    (allowed_root / "alpha.md").write_text("# Alpha\nLine 1  \nLine 2", encoding="utf-8")
    (allowed_root / "beta.markdown").write_text("Beta", encoding="utf-8")
    (allowed_root / "ignore.txt").write_text("ignore", encoding="utf-8")

    adapter = PrivateMarkdownSourceAdapter(source_root=source_root, allowed_roots=[allowed_root])

    resources = adapter.list_resources()

    assert [resource.resource_id for resource in resources] == [
        "docs/alpha.md",
        "docs/beta.markdown",
    ]
    assert resources[0].metadata["extension"] == ".md"


def test_fetch_resource_normalizes_markdown_and_preserves_metadata(tmp_path: Path) -> None:
    source_root = tmp_path / "approved"
    allowed_root = source_root / "docs"
    allowed_root.mkdir(parents=True)
    file_path = allowed_root / "alpha.md"
    file_path.write_text("# Alpha\r\nLine 1  \r\nLine 2\r\n", encoding="utf-8")

    adapter = PrivateMarkdownSourceAdapter(source_root=source_root, allowed_roots=[allowed_root])
    payload = adapter.fetch_resource("docs/alpha.md")

    assert payload["resource_id"] == "docs/alpha.md"
    assert payload["relative_path"] == "docs/alpha.md"
    assert payload["content"] == "# Alpha\nLine 1\nLine 2\n"
    assert payload["metadata"]["extension"] == ".md"
    assert payload["metadata"]["source_root"] == str(source_root.resolve())


def test_fetch_resource_rejects_escape_attempt(tmp_path: Path) -> None:
    source_root = tmp_path / "approved"
    allowed_root = source_root / "docs"
    allowed_root.mkdir(parents=True)
    (allowed_root / "alpha.md").write_text("Alpha", encoding="utf-8")

    adapter = PrivateMarkdownSourceAdapter(source_root=source_root, allowed_roots=[allowed_root])

    with pytest.raises(ValueError, match="escapes the approved source root"):
        adapter.fetch_resource("../outside.md")


def test_fetch_resource_rejects_unapproved_but_in_root_path(tmp_path: Path) -> None:
    source_root = tmp_path / "approved"
    allowed_root = source_root / "docs"
    other_root = source_root / "notes"
    allowed_root.mkdir(parents=True)
    other_root.mkdir(parents=True)
    (other_root / "hidden.md").write_text("Hidden", encoding="utf-8")

    adapter = PrivateMarkdownSourceAdapter(source_root=source_root, allowed_roots=[allowed_root])

    with pytest.raises(ValueError, match="not under an approved allowlisted root"):
        adapter.fetch_resource("notes/hidden.md")

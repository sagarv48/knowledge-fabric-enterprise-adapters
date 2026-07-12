from __future__ import annotations

from pathlib import Path

import pytest

from enterprise_adapters.file_source_adapters import ApprovedFileStoreSourceAdapter


def test_list_resources_includes_code_like_files(tmp_path: Path) -> None:
    source_root = tmp_path / "approved"
    allowed_root = source_root / "repo"
    allowed_root.mkdir(parents=True)
    (allowed_root / "main.py").write_text("print('hello')\n", encoding="utf-8")
    (allowed_root / "config.yaml").write_text("name: test\n", encoding="utf-8")
    (allowed_root / "notes.txt").write_text("notes", encoding="utf-8")
    (allowed_root / "ignore.bin").write_bytes(b"\x00\x01")

    adapter = ApprovedFileStoreSourceAdapter(source_root=source_root, allowed_roots=[allowed_root])

    resources = adapter.list_resources()

    assert [resource.resource_id for resource in resources] == [
        "repo/config.yaml",
        "repo/main.py",
        "repo/notes.txt",
    ]


def test_fetch_resource_normalizes_text(tmp_path: Path) -> None:
    source_root = tmp_path / "approved"
    allowed_root = source_root / "repo"
    allowed_root.mkdir(parents=True)
    file_path = allowed_root / "main.py"
    file_path.write_text("line 1  \r\nline 2\r\n", encoding="utf-8")

    adapter = ApprovedFileStoreSourceAdapter(source_root=source_root, allowed_roots=[allowed_root])
    payload = adapter.fetch_resource("repo/main.py")

    assert payload["content"] == "line 1\nline 2\n"
    assert payload["metadata"]["extension"] == ".py"


def test_fetch_resource_rejects_unapproved_path(tmp_path: Path) -> None:
    source_root = tmp_path / "approved"
    allowed_root = source_root / "repo"
    other_root = source_root / "other"
    allowed_root.mkdir(parents=True)
    other_root.mkdir(parents=True)
    (other_root / "hidden.py").write_text("hidden", encoding="utf-8")

    adapter = ApprovedFileStoreSourceAdapter(source_root=source_root, allowed_roots=[allowed_root])

    with pytest.raises(ValueError, match="not under an approved allowlisted root"):
        adapter.fetch_resource("other/hidden.py")

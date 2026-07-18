from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from enterprise_adapters.standard_source_adapters import GitHubRepositorySourceAdapter


def test_github_repo_lists_only_allowed_text_files(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: int = 30):  # noqa: ANN001
        url = request.full_url
        if "/git/trees/" in url:
            payload = {
                "tree": [
                    {"path": "content/en/docs/intro.md", "type": "blob", "size": 100},
                    {"path": "content/en/docs/assets/logo.png", "type": "blob", "size": 200},
                    {"path": "content/en/blog/post.md", "type": "blob", "size": 300},
                    {"path": "README.md", "type": "blob", "size": 50},
                ]
            }
            return _fake_response(payload)
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("enterprise_adapters.standard_source_adapters.urlopen", fake_urlopen)

    adapter = GitHubRepositorySourceAdapter(
        repository="kubernetes/website",
        allowed_paths=["content/en/docs"],
        ref="main",
    )

    resources = adapter.list_resources()

    assert [resource.resource_id for resource in resources] == ["content/en/docs/intro.md"]
    assert resources[0].metadata["repository"] == "kubernetes/website"


def test_github_repo_fetches_and_normalizes_content(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: int = 30):  # noqa: ANN001
        url = request.full_url
        if "/contents/content/en/docs/intro.md" in url:
            payload = {
                "encoding": "base64",
                "content": base64.b64encode(b"Line 1  \r\nLine 2\r\n").decode("utf-8"),
                "html_url": "https://github.com/kubernetes/website/blob/main/content/en/docs/intro.md",
                "sha": "abc123",
                "size": 18,
            }
            return _fake_response(payload)
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("enterprise_adapters.standard_source_adapters.urlopen", fake_urlopen)

    adapter = GitHubRepositorySourceAdapter(
        repository="kubernetes/website",
        allowed_paths=["content/en/docs"],
        ref="main",
    )

    payload = adapter.fetch_resource("content/en/docs/intro.md")

    assert payload["content"] == "Line 1\nLine 2\n"
    assert payload["metadata"]["repository"] == "kubernetes/website"
    assert payload["metadata"]["sha"] == "abc123"


def test_github_repo_rejects_unapproved_path() -> None:
    adapter = GitHubRepositorySourceAdapter(
        repository="kubernetes/website",
        allowed_paths=["content/en/docs"],
        ref="main",
    )

    with pytest.raises(ValueError, match="not under an approved allowlisted path"):
        adapter.fetch_resource("content/en/blog/post.md")


def test_github_repo_allows_root_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: int = 30):  # noqa: ANN001
        url = request.full_url
        if "/git/trees/" in url:
            payload = {"tree": [{"path": "README.md", "type": "blob", "size": 10}]}
            return _fake_response(payload)
        if "/contents/README.md" in url:
            payload = {
                "encoding": "base64",
                "content": base64.b64encode(b"Readme\n").decode("utf-8"),
                "html_url": "https://github.com/kubernetes/website/blob/main/README.md",
                "sha": "def456",
                "size": 7,
            }
            return _fake_response(payload)
        raise AssertionError(f"Unexpected URL: {url}")

    monkeypatch.setattr("enterprise_adapters.standard_source_adapters.urlopen", fake_urlopen)

    adapter = GitHubRepositorySourceAdapter(
        repository="kubernetes/website",
        allowed_paths=["."],
        ref="main",
    )

    resources = adapter.list_resources()
    payload = adapter.fetch_resource("README.md")

    assert [resource.resource_id for resource in resources] == ["README.md"]
    assert payload["content"] == "Readme\n"


def _fake_response(payload: dict[str, object]):
    class _Headers:
        def get_content_type(self) -> str:
            return "application/json"

        def get_content_charset(self) -> str:
            return "utf-8"

    class _Response:
        headers = _Headers()

        def __enter__(self) -> "_Response":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(payload).encode("utf-8")

    return _Response()


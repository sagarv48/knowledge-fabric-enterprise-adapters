"""Unit tests for SaaS source connectors (Confluence, Notion, Google Drive, Jira)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from knowledge_fabric_adapters.connectors.confluence import (
    ConfluenceSourceAdapter,
    _ConfluenceHTMLToMarkdown,
)
from knowledge_fabric_adapters.connectors.google_drive import GoogleDriveSourceAdapter
from knowledge_fabric_adapters.connectors.jira import JiraSourceAdapter
from knowledge_fabric_adapters.connectors.notion import NotionSourceAdapter, _block_to_markdown


def test_confluence_html_to_markdown() -> None:
    html = "<h1>Title</h1><p>This is <strong>important</strong> documentation.</p><ul><li>Step 1</li><li>Step 2</li></ul>"
    parser = _ConfluenceHTMLToMarkdown()
    parser.feed(html)
    md = parser.get_text()
    assert "# Title" in md
    assert "This is important documentation." in md
    assert "- Step 1" in md
    assert "- Step 2" in md


def test_confluence_adapter_list_and_fetch() -> None:
    adapter = ConfluenceSourceAdapter(
        base_url="https://test.atlassian.net/wiki",
        space_keys=["ENG"],
        email="test@example.com",
        api_token="dummy",
    )

    list_payload = {
        "results": [
            {
                "id": "1001",
                "title": "Architecture Overview",
                "version": {"number": 2, "when": "2026-01-01T00:00:00Z"},
                "metadata": {"labels": {"results": [{"name": "arch"}, {"name": "core"}]}},
            }
        ]
    }
    fetch_payload = {
        "id": "1001",
        "title": "Architecture Overview",
        "space": {"key": "ENG"},
        "version": {"number": 2, "when": "2026-01-01T00:00:00Z"},
        "body": {
            "storage": {
                "value": "<p>Microservices communicate over gRPC.</p>"
            }
        },
    }

    with patch.object(adapter, "_request_json") as mock_req:
        mock_req.side_effect = [list_payload, fetch_payload]

        resources = adapter.list_resources()
        assert len(resources) == 1
        assert resources[0].resource_id == "1001"
        assert resources[0].name == "Architecture Overview"
        assert resources[0].metadata["space_key"] == "ENG"

        item = adapter.fetch_resource("1001")
        assert item["resource_id"] == "1001"
        assert "Microservices communicate over gRPC." in item["content"]
        assert item["path"] == "confluence://ENG/1001"


def test_notion_block_to_markdown() -> None:
    para_block = {
        "type": "paragraph",
        "paragraph": {"rich_text": [{"plain_text": "Hello world"}]},
    }
    heading_block = {
        "type": "heading_2",
        "heading_2": {"rich_text": [{"plain_text": "Subheading"}]},
    }
    assert _block_to_markdown(para_block) == "Hello world\n\n"
    assert _block_to_markdown(heading_block) == "## Subheading\n\n"


def test_notion_adapter_list_and_fetch() -> None:
    adapter = NotionSourceAdapter(api_key="secret_test", database_ids=["db_123"])

    query_payload = {
        "results": [
            {
                "id": "page_456",
                "created_time": "2026-01-01T00:00:00Z",
                "last_edited_time": "2026-01-02T00:00:00Z",
                "url": "https://notion.so/page_456",
                "properties": {
                    "Name": {"type": "title", "title": [{"plain_text": "Q1 Goals"}]}
                },
            }
        ],
        "has_more": False,
    }

    page_payload = {
        "id": "page_456",
        "properties": {
            "Name": {"type": "title", "title": [{"plain_text": "Q1 Goals"}]}
        },
        "url": "https://notion.so/page_456",
    }

    blocks_payload = {
        "results": [
            {
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"plain_text": "Deliver multi-tenancy"}]},
            }
        ],
        "has_more": False,
    }

    with patch.object(adapter, "_request") as mock_req:
        mock_req.side_effect = [query_payload, page_payload, blocks_payload]

        resources = adapter.list_resources()
        assert len(resources) == 1
        assert resources[0].resource_id == "page_456"
        assert resources[0].name == "Q1 Goals"

        item = adapter.fetch_resource("page_456")
        assert item["resource_id"] == "page_456"
        assert "Deliver multi-tenancy" in item["content"]


def test_jira_adapter_list_and_fetch() -> None:
    adapter = JiraSourceAdapter(base_url="https://test.atlassian.net", jql="project = SEC")

    search_payload = {
        "issues": [
            {
                "key": "SEC-101",
                "fields": {
                    "summary": "Investigate SSH anomaly",
                    "status": {"name": "Resolved"},
                    "priority": {"name": "High"},
                    "project": {"key": "SEC"},
                    "updated": "2026-01-01T12:00:00Z",
                },
            }
        ],
        "total": 1,
    }

    detail_payload = {
        "key": "SEC-101",
        "fields": {
            "summary": "Investigate SSH anomaly",
            "status": {"name": "Resolved"},
            "priority": {"name": "High"},
            "issuetype": {"name": "Incident"},
            "description": "Port scanning detected on jumpbox.",
            "comment": {
                "comments": [
                    {
                        "author": {"displayName": "SecOps Lead"},
                        "created": "2026-01-01T14:00:00Z",
                        "body": "IP address blacklisted in firewall.",
                    }
                ]
            },
        },
    }

    with patch.object(adapter, "_request_json") as mock_req:
        mock_req.side_effect = [search_payload, detail_payload]

        resources = adapter.list_resources()
        assert len(resources) == 1
        assert resources[0].resource_id == "SEC-101"
        assert "[SEC-101] Investigate SSH anomaly" in resources[0].name

        item = adapter.fetch_resource("SEC-101")
        assert item["resource_id"] == "SEC-101"
        assert "Port scanning detected on jumpbox." in item["content"]
        assert "SecOps Lead" in item["content"]
        assert item["path"] == "jira://SEC-101"

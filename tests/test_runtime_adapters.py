from __future__ import annotations

from enterprise_adapters.contracts import ReadOnlyResource
from enterprise_adapters.runtime_adapters import ReadOnlyRuntimeDiscoveryAdapter, load_runtime_auth_config


def test_runtime_discovery_lists_resources() -> None:
    adapter = ReadOnlyRuntimeDiscoveryAdapter.from_discovery(
        runtime_tools=[
            ReadOnlyResource(resource_id="tool-1", name="list_tools"),
            ReadOnlyResource(resource_id="tool-2", name="get_metadata"),
        ],
        case_types_or_equivalent=[
            ReadOnlyResource(resource_id="case-1", name="incident"),
        ],
        metadata_by_target_id={
            "tool-1": {"description": "List tools"},
            "case-1": {"description": "Incident metadata"},
        },
    )

    assert [item.name for item in adapter.list_runtime_tools()] == ["list_tools", "get_metadata"]
    assert [item.name for item in adapter.list_case_types_or_equivalent()] == ["incident"]
    assert adapter.get_metadata("case-1")["description"] == "Incident metadata"


def test_runtime_auth_config_defaults(monkeypatch) -> None:
    monkeypatch.delenv("RUNTIME_API_BASE_URL", raising=False)
    monkeypatch.delenv("RUNTIME_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("RUNTIME_ENV", raising=False)

    config = load_runtime_auth_config()

    assert config.base_url == ""
    assert config.auth_token == ""
    assert config.environment == "local"

from __future__ import annotations

import json
from pathlib import Path

from enterprise_adapters.runtime_snapshot_adapters import RuntimeSnapshotDiscoveryAdapter


def test_runtime_snapshot_adapter_from_mapping() -> None:
    adapter = RuntimeSnapshotDiscoveryAdapter.from_mapping(
        {
            "runtime_tools": [{"resource_id": "tool-1", "name": "list_runtime_tools"}],
            "case_types_or_equivalent": [{"resource_id": "case-1", "name": "incident"}],
            "metadata_by_target_id": {"case-1": {"description": "Snapshot metadata"}},
        },
        snapshot_name="local",
    )

    assert [item.name for item in adapter.list_runtime_tools()] == ["list_runtime_tools"]
    assert adapter.get_metadata("case-1")["description"] == "Snapshot metadata"


def test_runtime_snapshot_adapter_from_file(tmp_path: Path) -> None:
    snapshot_file = tmp_path / "snapshot.json"
    snapshot_file.write_text(
        json.dumps(
            {
                "runtime_tools": [{"resource_id": "tool-1", "name": "get_metadata"}],
                "case_types_or_equivalent": [{"resource_id": "case-1", "name": "incident"}],
                "metadata_by_target_id": {"tool-1": {"description": "Tool metadata"}},
            }
        ),
        encoding="utf-8",
    )

    adapter = RuntimeSnapshotDiscoveryAdapter.from_file(snapshot_file)

    assert adapter.snapshot_name == "snapshot"
    assert [item.name for item in adapter.list_case_types_or_equivalent()] == ["incident"]

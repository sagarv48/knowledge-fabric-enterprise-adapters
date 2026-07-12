from __future__ import annotations

import io
import json
import logging

from enterprise_adapters.observability import JsonLineFormatter, build_structured_logger, log_structured_event


def test_json_formatter_emits_event_fields() -> None:
    logger = build_structured_logger("test-observability", level=logging.INFO)
    stream = io.StringIO()
    logger.handlers[0].stream = stream  # type: ignore[attr-defined]

    log_structured_event(logger, "adapter.read", adapter="source", resource_id="docs/policy.md")

    payload = json.loads(stream.getvalue().strip())
    assert payload["event_type"] == "adapter.read"
    assert payload["adapter"] == "source"
    assert payload["resource_id"] == "docs/policy.md"
    assert payload["message"] == "adapter.read"


def test_json_formatter_can_be_instantiated() -> None:
    formatter = JsonLineFormatter()
    assert formatter is not None

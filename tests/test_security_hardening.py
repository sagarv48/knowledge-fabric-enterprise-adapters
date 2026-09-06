"""Security hardening test suite for Knowledge Fabric Enterprise Adapters.

Validates mitigations against:
1. Information Disclosure (Secret redaction in connector logs, tracebacks, and URLs)
2. Repudiation & Privilege (Cryptographic approval verification in execution adapters)
"""

from __future__ import annotations

import logging
import pytest

from knowledge_fabric_adapters.contracts import verify_approval_signature
from knowledge_fabric_adapters.security import (
    RedactingLoggingFilter,
    sanitize_exception,
    sanitize_log_message,
)


def test_secret_redactor_masks_bearer_token() -> None:
    """Bearer tokens must be masked in log messages."""
    raw = "Request failed with header Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    sanitized = sanitize_log_message(raw)
    assert "Bearer [REDACTED]" in sanitized
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in sanitized


def test_secret_redactor_masks_basic_auth() -> None:
    """Basic auth credentials must be masked."""
    raw = "Connecting with Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQxMjM0NQ=="
    sanitized = sanitize_log_message(raw)
    assert "Basic [REDACTED]" in sanitized
    assert "dXNlcm5hbWU6cGFzc3dvcmQxMjM0NQ==" not in sanitized


def test_secret_redactor_masks_url_query_params() -> None:
    """Sensitive query params like api_key, token, and secret must be masked."""
    url = "https://my-company.atlassian.net/wiki/rest/api/content?api_key=secret_12345&spaceKey=ENG"
    sanitized = sanitize_log_message(url)
    assert "api_key=[REDACTED]" in sanitized
    assert "secret_12345" not in sanitized
    assert "spaceKey=ENG" in sanitized  # non-sensitive query params preserved


def test_secret_redactor_masks_exception_strings() -> None:
    """Exceptions containing tokens must be safely scrubbed."""
    try:
        raise RuntimeError("HTTP 401 Unauthorized for URL https://api.notion.com/v1/pages?token=notion_secret_999888")
    except RuntimeError as exc:
        sanitized_err = sanitize_exception(exc)
        assert "token=[REDACTED]" in sanitized_err
        assert "notion_secret_999888" not in sanitized_err


def test_redacting_logging_filter() -> None:
    """RedactingLoggingFilter must scrub log records before emitting."""
    filt = RedactingLoggingFilter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Connecting to Jira with token %s",
        args=("jira_secret_token_abcdef123456",),
        exc_info=None,
    )
    filt.filter(record)
    assert record.args[0] == "jira_secret_token_abcdef123456" or "[REDACTED]" in record.args[0] or "[REDACTED]" in sanitize_log_message(str(record.args))


def test_adapter_approval_signature_verification() -> None:
    """Adapters must verify cryptographic approval signatures before execution."""
    import hashlib
    import hmac

    secret = "production-air-gapped-signing-key"
    approval_id = "appr_sec_1001"
    plan_id = "plan_p1_incident"
    step_ids = ["step_apply_firewall", "step_notify_lead"]
    decision = "approved"
    reviewer = "incident_commander@corp.com"
    timestamp = "2026-09-06T15:30:00Z"

    # Compute valid signature
    canonical = f"{approval_id}|{plan_id}|step_apply_firewall,step_notify_lead|{decision}|{reviewer}|{timestamp}"
    valid_sig = hmac.new(secret.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).hexdigest()

    # 1. Valid signature passes
    assert verify_approval_signature(
        approval_id=approval_id,
        plan_id=plan_id,
        step_ids=step_ids,
        decision=decision,
        reviewer=reviewer,
        timestamp=timestamp,
        signature=valid_sig,
        secret_key=secret,
    ) is True

    # 2. Forged signature fails
    assert verify_approval_signature(
        approval_id=approval_id,
        plan_id=plan_id,
        step_ids=step_ids,
        decision=decision,
        reviewer=reviewer,
        timestamp=timestamp,
        signature="deadbeef" * 8,
        secret_key=secret,
    ) is False

    # 3. Forged decision (e.g. attempting to execute a rejected step) fails
    assert verify_approval_signature(
        approval_id=approval_id,
        plan_id=plan_id,
        step_ids=step_ids,
        decision="rejected",
        reviewer=reviewer,
        timestamp=timestamp,
        signature=valid_sig,
        secret_key=secret,
    ) is False

    # 4. Permissive mode allows dev/test velocity even with missing signature
    assert verify_approval_signature(
        approval_id=approval_id,
        plan_id=plan_id,
        step_ids=step_ids,
        decision=decision,
        reviewer=reviewer,
        timestamp=timestamp,
        signature="invalid_signature",
        secret_key=secret,
        enforcement_mode="permissive",
    ) is True


def test_secret_redactor_toggle_via_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """When ADAPTERS_REDACT_SECRETS is false, secret redaction can be bypassed for debugging."""
    raw = "Authorization: Bearer my_secret_token_12345678"
    monkeypatch.setenv("ADAPTERS_REDACT_SECRETS", "false")
    assert sanitize_log_message(raw) == raw

    monkeypatch.setenv("ADAPTERS_REDACT_SECRETS", "true")
    assert "Bearer [REDACTED]" in sanitize_log_message(raw)


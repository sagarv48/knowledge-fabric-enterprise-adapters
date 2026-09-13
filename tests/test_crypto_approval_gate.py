"""Tests for the cryptographic approval verification gate in ApprovedRuntimeActionAdapter."""

from __future__ import annotations

import pytest

from enterprise_adapters.approvals import compute_approval_signature
from enterprise_adapters.execution import ApprovedRuntimeActionAdapter
from enterprise_adapters.policy import PolicyDecision, PolicyDecisionType


def _allow() -> PolicyDecision:
    return PolicyDecision(decision_id="d1", decision=PolicyDecisionType.ALLOW, reasons=["Permitted"])


def test_readonly_action_requires_no_signature() -> None:
    adapter = ApprovedRuntimeActionAdapter()
    receipt = adapter.execute_action({
        "action_name": "read_data",
        "write": False,
        "approval_id": "appr_read_1",
        "policy_decision": _allow(),
    })
    assert receipt["status"] == "executed"
    assert receipt["approval_id"] == "appr_read_1"


def test_write_action_with_valid_signature_succeeds() -> None:
    adapter = ApprovedRuntimeActionAdapter()
    approval_id = "appr_write_101"
    plan_id = "plan_infra_1"
    step_ids = ["deploy_service"]
    decision = "approved"
    reviewer = "lead@company.com"
    timestamp = "2026-09-13T12:00:00Z"

    sig = compute_approval_signature(
        approval_id=approval_id,
        plan_id=plan_id,
        step_ids=step_ids,
        decision=decision,
        reviewer=reviewer,
        timestamp=timestamp,
    )

    action = {
        "action_name": "deploy_service",
        "write": True,
        "approval_id": approval_id,
        "plan_id": plan_id,
        "step_ids": step_ids,
        "decision": decision,
        "reviewer": reviewer,
        "timestamp": timestamp,
        "signature": sig,
        "policy_decision": _allow(),
    }

    receipt = adapter.execute_action(action)
    assert receipt["status"] == "executed"
    assert receipt["approval_id"] == approval_id

    events = [e for e in adapter.audit_events() if getattr(e, "event_type", "") == "approval.verified"]
    assert len(events) == 1


def test_write_action_with_nested_approval_token_succeeds() -> None:
    adapter = ApprovedRuntimeActionAdapter()
    approval_id = "appr_token_202"
    plan_id = "plan_infra_2"
    step_ids = ["scale_cluster"]
    decision = "approved"
    reviewer = "sre@company.com"
    timestamp = "2026-09-13T12:30:00Z"

    sig = compute_approval_signature(
        approval_id=approval_id,
        plan_id=plan_id,
        step_ids=step_ids,
        decision=decision,
        reviewer=reviewer,
        timestamp=timestamp,
    )

    action = {
        "action_name": "scale_cluster",
        "write": True,
        "approval_id": approval_id,
        "policy_decision": _allow(),
        "approval_token": {
            "approval_id": approval_id,
            "plan_id": plan_id,
            "step_ids": step_ids,
            "decision": decision,
            "reviewer": reviewer,
            "timestamp": timestamp,
            "signature": sig,
        },
    }

    receipt = adapter.execute_action(action)
    assert receipt["status"] == "executed"


def test_write_action_with_tampered_signature_fails() -> None:
    adapter = ApprovedRuntimeActionAdapter()
    action = {
        "action_name": "delete_table",
        "write": True,
        "approval_id": "appr_fake_303",
        "plan_id": "plan_fake",
        "step_ids": ["delete_table"],
        "signature": "tampered_signature_hex_0000000000000000",
        "policy_decision": _allow(),
    }

    with pytest.raises(PermissionError, match="Cryptographic approval verification failed"):
        adapter.execute_action(action)

    failed_events = [e for e in adapter.audit_events() if getattr(e, "event_type", "") == "approval.verification_failed"]
    assert len(failed_events) == 1


def test_write_action_missing_signature_in_enforce_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FABRIC_APPROVAL_ENFORCEMENT", "enforce")
    adapter = ApprovedRuntimeActionAdapter()
    action = {
        "action_name": "restart_gateway",
        "write": True,
        "approval_id": "appr_restart_404",
        "policy_decision": _allow(),
    }

    with pytest.raises(PermissionError, match="requires a cryptographic approval signature"):
        adapter.execute_action(action)


def test_write_action_missing_signature_in_permissive_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FABRIC_APPROVAL_ENFORCEMENT", "permissive")
    adapter = ApprovedRuntimeActionAdapter()
    action = {
        "action_name": "restart_gateway",
        "write": True,
        "approval_id": "appr_restart_405",
        "policy_decision": _allow(),
    }

    receipt = adapter.execute_action(action)
    assert receipt["status"] == "executed"
    permissive_events = [
        e for e in adapter.audit_events()
        if getattr(e, "event_type", "") == "approval.signature_missing_permissive"
    ]
    assert len(permissive_events) == 1

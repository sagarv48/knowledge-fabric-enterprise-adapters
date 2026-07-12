from __future__ import annotations

import pytest

from enterprise_adapters.execution import ApprovedRuntimeActionAdapter
from enterprise_adapters.policy import PolicyDecision, PolicyDecisionType


def test_execute_action_requires_policy_decision() -> None:
    adapter = ApprovedRuntimeActionAdapter()

    with pytest.raises(PermissionError, match="policy_decision"):
        adapter.execute_action({"action_name": "write_summary", "approval_id": "approval_1"})


def test_execute_action_requires_approval_id() -> None:
    adapter = ApprovedRuntimeActionAdapter()
    decision = PolicyDecision(decision_id="policy_1", decision=PolicyDecisionType.ALLOW)

    with pytest.raises(PermissionError, match="approval_id"):
        adapter.execute_action({"action_name": "write_summary", "policy_decision": decision})


def test_execute_action_returns_receipt_and_audits() -> None:
    adapter = ApprovedRuntimeActionAdapter()
    decision = PolicyDecision(decision_id="policy_1", decision=PolicyDecisionType.ALLOW)
    receipt = adapter.execute_action(
        {"action_name": "write_summary", "approval_id": "approval_1", "policy_decision": decision}
    )

    assert receipt["status"] == "executed"
    assert receipt["approval_id"] == "approval_1"
    assert len(adapter.audit_events()) == 1
    assert adapter.audit_events()[0].event_type == "execution.completed"

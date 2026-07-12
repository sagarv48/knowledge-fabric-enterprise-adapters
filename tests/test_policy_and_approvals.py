from __future__ import annotations

from enterprise_adapters.approvals import ApprovalPackageGenerator
from enterprise_adapters.audit import InMemoryAuditTrail
from enterprise_adapters.policy import PolicyDecisionType, PolicyEvaluator


def test_read_only_action_is_allowed() -> None:
    evaluator = PolicyEvaluator()
    decision = evaluator.evaluate({"action_name": "list_runtime_tools", "write": False})

    assert decision.decision is PolicyDecisionType.ALLOW


def test_write_action_requires_approval() -> None:
    evaluator = PolicyEvaluator()
    decision = evaluator.evaluate({"action_name": "execute_write", "write": True})

    assert decision.decision is PolicyDecisionType.REQUIRES_APPROVAL


def test_approved_write_action_is_allowed() -> None:
    evaluator = PolicyEvaluator()
    decision = evaluator.evaluate({"action_name": "execute_write", "write": True, "approval_id": "approval_123"})

    assert decision.decision is PolicyDecisionType.ALLOW


def test_approval_request_generation() -> None:
    evaluator = PolicyEvaluator()
    decision = evaluator.evaluate({"action_name": "execute_write", "write": True})
    generator = ApprovalPackageGenerator()
    approval = generator.create(
        action={"action_name": "execute_write", "write": True},
        policy_decision=decision,
        requested_by="analyst",
    )

    assert approval.action_name == "execute_write"
    assert approval.policy_reasons == decision.reasons


def test_in_memory_audit_trail_records_events() -> None:
    trail = InMemoryAuditTrail()
    trail.record("policy.evaluated", action_name="execute_write")

    assert len(trail.events()) == 1
    assert trail.events()[0].event_type == "policy.evaluated"

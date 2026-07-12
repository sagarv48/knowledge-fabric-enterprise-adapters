from __future__ import annotations

import pytest

from enterprise_adapters.policy import PolicyDecision, PolicyDecisionType
from enterprise_adapters.simulation import SimulationOnlyRuntimeActionAdapter


def test_prepare_action_marks_payload_as_simulated() -> None:
    adapter = SimulationOnlyRuntimeActionAdapter()
    prepared = adapter.prepare_action({"action_name": "write_summary", "write": True})

    assert prepared["payload"]["simulated"] is True
    assert prepared["payload"]["validated"] is True
    assert prepared["metadata"]["requires_approval"] is True


def test_execute_action_returns_simulation_result() -> None:
    adapter = SimulationOnlyRuntimeActionAdapter()
    result = adapter.execute_action({"action_name": "write_summary", "write": True})

    assert result["status"] == "simulated"
    assert result["no_external_side_effects"] is True


def test_simulate_with_policy_respects_policy_decision() -> None:
    adapter = SimulationOnlyRuntimeActionAdapter()
    decision = PolicyDecision(decision_id="policy_1", decision=PolicyDecisionType.REQUIRES_APPROVAL)
    outcome = adapter.simulate_with_policy({"action_name": "write_summary", "write": True}, decision)

    assert outcome["status"] == "pending_approval"


def test_prepare_action_requires_action_name() -> None:
    adapter = SimulationOnlyRuntimeActionAdapter()

    with pytest.raises(ValueError, match="action_name is required"):
        adapter.prepare_action({"write": True})

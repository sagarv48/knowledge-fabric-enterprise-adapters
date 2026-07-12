from __future__ import annotations

from pathlib import Path

from enterprise_adapters.approvals import ApprovalPackageGenerator
from enterprise_adapters.approval_storage import SQLiteApprovalStore
from enterprise_adapters.policy import PolicyDecisionType, PolicyEvaluator


def test_sqlite_approval_store_persists_records(tmp_path: Path) -> None:
    store = SQLiteApprovalStore(tmp_path / "approvals.sqlite3")
    evaluator = PolicyEvaluator()
    decision = evaluator.evaluate({"action_name": "execute_write", "write": True})
    approval = ApprovalPackageGenerator().create(
        action={"action_name": "execute_write", "write": True},
        policy_decision=decision,
        requested_by="analyst",
    )

    record = store.save(approval, decision)
    loaded = store.get(record.approval_id)

    assert loaded is not None
    assert loaded.approval_id == record.approval_id
    assert loaded.decision == PolicyDecisionType.REQUIRES_APPROVAL.value
    assert len(store.list_all()) == 1

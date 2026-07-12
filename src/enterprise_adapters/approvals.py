"""Approval request shapes for private adapter actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha1

from enterprise_adapters.policy import PolicyDecision


@dataclass(slots=True)
class ApprovalRequest:
    """Human approval request for a private action."""

    approval_id: str
    action_name: str
    requested_by: str
    summary: str
    policy_reasons: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


class ApprovalPackageGenerator:
    """Builds approval requests from policy outcomes."""

    def create(self, *, action: dict[str, object], policy_decision: PolicyDecision, requested_by: str) -> ApprovalRequest:
        action_name = str(action.get("action_name", "unknown"))
        approval_id = _stable_id("approval", f"{action_name}:{requested_by}")
        summary = f"Approval required for action '{action_name}'."
        return ApprovalRequest(
            approval_id=approval_id,
            action_name=action_name,
            requested_by=requested_by,
            summary=summary,
            policy_reasons=policy_decision.reasons,
            metadata={"decision": policy_decision.decision.value},
        )


def _stable_id(prefix: str, seed: str) -> str:
    return f"{prefix}_{sha1(seed.encode('utf-8')).hexdigest()[:12]}"

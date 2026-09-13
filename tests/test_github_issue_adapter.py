"""Tests for GitHubIssueAdapter — no real API calls."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
from io import BytesIO

import pytest

from enterprise_adapters.policy import PolicyDecision, PolicyDecisionType


from enterprise_adapters.approvals import compute_approval_signature


def _allow() -> PolicyDecision:
    return PolicyDecision(
        decision_id="d1",
        decision=PolicyDecisionType.ALLOW,
        reasons=["Human approved."],
    )


def _approved_action(**kwargs) -> dict:
    approval_id = "approval-abc123"
    plan_id = "plan-p1-42"
    step_ids = ["create_github_issue"]
    decision = "approved"
    reviewer = "oncall-lead@company.com"
    timestamp = "2026-09-13T12:00:00Z"
    sig = compute_approval_signature(
        approval_id=approval_id,
        plan_id=plan_id,
        step_ids=step_ids,
        decision=decision,
        reviewer=reviewer,
        timestamp=timestamp,
    )
    base = {
        "action_name": "create_github_issue",
        "write": True,
        "approval_id": approval_id,
        "plan_id": plan_id,
        "step_ids": step_ids,
        "decision": decision,
        "reviewer": reviewer,
        "timestamp": timestamp,
        "signature": sig,
        "policy_decision": _allow(),
        "payload": {
            "title": "K8s pod restart loop detected",
            "body": "The payment pod is in CrashLoopBackOff. Evidence from K8s docs suggests checking resource limits.",
            "labels": ["ai-generated", "needs-review"],
        },
    }
    base.update(kwargs)
    return base


def test_adapter_raises_without_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    from enterprise_adapters.github_issue_adapter import GitHubIssueAdapter
    with pytest.raises(EnvironmentError, match="GITHUB_TOKEN"):
        GitHubIssueAdapter.from_env()


def test_adapter_raises_without_repo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.delenv("GITHUB_ISSUE_REPO", raising=False)
    from enterprise_adapters.github_issue_adapter import GitHubIssueAdapter
    with pytest.raises(EnvironmentError, match="GITHUB_ISSUE_REPO"):
        GitHubIssueAdapter.from_env()


def test_adapter_raises_without_approval_id() -> None:
    from enterprise_adapters.github_issue_adapter import GitHubIssueAdapter
    adapter = GitHubIssueAdapter(token="fake-token", repo="sagarv48/knowledge-fabric-demo")
    with pytest.raises(PermissionError, match="approval_id"):
        adapter.execute_action({
            "action_name": "create_github_issue",
            "write": True,
            "policy_decision": _allow(),
            # no approval_id
        })


def test_adapter_raises_without_policy_allow() -> None:
    from enterprise_adapters.github_issue_adapter import GitHubIssueAdapter
    adapter = GitHubIssueAdapter(token="fake-token", repo="sagarv48/knowledge-fabric-demo")
    deny_decision = PolicyDecision(decision_id="d2", decision=PolicyDecisionType.DENY, reasons=["Denied"])
    with pytest.raises(PermissionError, match="allow"):
        adapter.execute_action(_approved_action(policy_decision=deny_decision))


def test_adapter_raises_on_tampered_signature() -> None:
    from enterprise_adapters.github_issue_adapter import GitHubIssueAdapter
    adapter = GitHubIssueAdapter(token="fake-token", repo="sagarv48/knowledge-fabric-demo")
    with pytest.raises(PermissionError, match="Cryptographic approval verification failed"):
        adapter.execute_action(_approved_action(signature="bad_tampered_signature_hex"))


def test_adapter_raises_on_missing_signature_in_enforce_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FABRIC_APPROVAL_ENFORCEMENT", "enforce")
    from enterprise_adapters.github_issue_adapter import GitHubIssueAdapter
    adapter = GitHubIssueAdapter(token="fake-token", repo="sagarv48/knowledge-fabric-demo")
    with pytest.raises(PermissionError, match="requires a cryptographic approval signature"):
        action = _approved_action()
        del action["signature"]
        adapter.execute_action(action)


def test_adapter_creates_issue_successfully() -> None:
    from enterprise_adapters.github_issue_adapter import GitHubIssueAdapter

    fake_response_body = json.dumps({
        "number": 42,
        "html_url": "https://github.com/sagarv48/knowledge-fabric-demo/issues/42",
    }).encode("utf-8")

    mock_response = MagicMock()
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    mock_response.read.return_value = fake_response_body

    adapter = GitHubIssueAdapter(token="fake-token", repo="sagarv48/knowledge-fabric-demo")

    with patch("urllib.request.urlopen", return_value=mock_response):
        receipt = adapter.execute_action(_approved_action())

    assert receipt["status"] == "executed"
    assert receipt["metadata"]["issue_number"] == 42
    assert "issues/42" in receipt["metadata"]["issue_url"]
    assert receipt["approval_id"] == "approval-abc123"
    assert len(adapter.audit_events()) >= 1


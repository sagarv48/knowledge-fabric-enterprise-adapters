# Adoption Guide: Wiring an Enterprise Integration from Scratch

This guide walks you through a complete, working integration from nothing to a running
enterprise adapter, step by step. We use one concrete use case the whole way through
so every step feels real rather than theoretical.

---

## The scenario

> **"We have an internal Markdown knowledge base stored on disk (or exported from
> Confluence/SharePoint), and a ticketing system. We want to let an AI answer questions
> from that knowledge base and, when needed, open tickets — but only after a human approves."**

This is exactly what the three-repo stack is designed for:

| Part | What it does in our scenario |
|------|------------------------------|
| **knowledge-fabric** | Indexes the Markdown docs so they can be searched by evidence retrieval |
| **intent-fabric** | Turns a question into a structured plan ("open ticket X with these details") |
| **knowledge-fabric-enterprise-adapters** (this repo) | Loads private docs, discovers the ticketing system, gates ticket creation behind policy and approval |

---

## Before you start

You need:

- Python 3.11+
- Git
- A local copy of this repo (private)
- Optional: a local copy of `knowledge-fabric` and `intent-fabric` for full end-to-end testing

---

## Step 1 — Install and verify the repo works today

```bash
git clone <your-private-repo-url> knowledge-fabric-enterprise-adapters
cd knowledge-fabric-enterprise-adapters

python3 -m pip install -e ".[dev]"
python3 -m pytest
```

If all tests pass, your local environment is good. If not, check that you are using
Python 3.11+ and that no dependencies are missing.

---

## Step 2 — Put your private docs somewhere safe

Create a local folder to act as your private knowledge base root. This should live
**outside** the repo so it is never accidentally committed.

```bash
mkdir -p ~/enterprise-docs/knowledge-base/product
mkdir -p ~/enterprise-docs/knowledge-base/runbooks

# Add a couple of real or placeholder Markdown files
cat > ~/enterprise-docs/knowledge-base/product/overview.md << 'EOF'
# Product Overview

Our platform handles payments for enterprise customers.
The main failure modes are: database timeout, auth expiry, and rate limiting.
EOF

cat > ~/enterprise-docs/knowledge-base/runbooks/restart-service.md << 'EOF'
# Restart Payment Service

1. SSH into the host
2. Run: `systemctl restart payment-service`
3. Verify: `curl http://localhost:9000/healthz`
EOF
```

Your private content is now outside the repo and outside git history — exactly right.

---

## Step 3 — Write your first source adapter

Create a new file for your integration. Use the existing `PrivateMarkdownSourceAdapter`
directly — no new code needed yet.

Open a Python shell in the repo:

```python
from pathlib import Path
from enterprise_adapters.source_adapters import PrivateMarkdownSourceAdapter

adapter = PrivateMarkdownSourceAdapter(
    source_root=Path.home() / "enterprise-docs" / "knowledge-base",
    allowed_roots=[
        Path.home() / "enterprise-docs" / "knowledge-base" / "product",
        Path.home() / "enterprise-docs" / "knowledge-base" / "runbooks",
    ],
)

# List everything the adapter can see
resources = adapter.list_resources()
for r in resources:
    print(r.resource_id, "—", r.name)

# Fetch the full content of one resource
payload = adapter.fetch_resource("product/overview.md")
print(payload["content"])
```

If you see your docs listed and the content printed, the source adapter is working.

If your docs are a mix of Markdown and other file types (Python, YAML, JSON, etc.),
use `ApprovedFileStoreSourceAdapter` instead — it supports a wider set of extensions:

```python
from enterprise_adapters.file_source_adapters import ApprovedFileStoreSourceAdapter

adapter = ApprovedFileStoreSourceAdapter(
    source_root=Path.home() / "enterprise-code",
    allowed_roots=[Path.home() / "enterprise-code" / "payments-service"],
)
```

---

## Step 4 — Write a custom source adapter for a new system

When your source is not a local folder — for example, a SharePoint site or an internal
wiki API — create a new adapter that follows the same contract.

Create `src/enterprise_adapters/my_wiki_source_adapter.py`:

```python
"""Read-only adapter for our internal wiki API."""

from __future__ import annotations

import urllib.request
import json

from enterprise_adapters.contracts import ReadOnlyResource


class InternalWikiSourceAdapter:
    """Fetches approved pages from an internal wiki API."""

    def __init__(self, base_url: str, auth_token: str, allowed_page_ids: list[str]) -> None:
        self._base_url = base_url.rstrip("/")
        self._auth_token = auth_token
        self._allowed_page_ids = set(allowed_page_ids)

    def list_resources(self) -> list[ReadOnlyResource]:
        return [
            ReadOnlyResource(resource_id=page_id, name=f"wiki-page-{page_id}")
            for page_id in sorted(self._allowed_page_ids)
        ]

    def fetch_resource(self, resource_id: str) -> dict[str, object]:
        if resource_id not in self._allowed_page_ids:
            raise ValueError(f"Page '{resource_id}' is not in the approved allowlist")
        url = f"{self._base_url}/pages/{resource_id}"
        request = urllib.request.Request(
            url, headers={"Authorization": f"Bearer {self._auth_token}"}
        )
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode("utf-8"))
        return {
            "resource_id": resource_id,
            "content": data.get("body", ""),
            "metadata": {"title": data.get("title", ""), "page_id": resource_id},
        }
```

A few rules to follow when writing any new source adapter:

1. **Never skip the allowlist check.** If `resource_id` is not in the approved set,
   raise `ValueError`. This prevents path traversal and accidental disclosure.
2. **Normalize content.** Strip leading/trailing whitespace, normalize line endings.
3. **Never commit credentials.** Read `auth_token` from `os.environ` in real code.
4. **Write a test.** Copy `tests/test_source_adapters.py` as a starting point.

Read credentials from the environment, not from code:

```python
import os

adapter = InternalWikiSourceAdapter(
    base_url=os.environ["WIKI_API_URL"],
    auth_token=os.environ["WIKI_AUTH_TOKEN"],
    allowed_page_ids=["page-101", "page-102"],
)
```

---

## Step 5 — Discover your ticketing system

In the same Python shell, wire up the read-only discovery adapter for your ticketing
system. You are not writing any tickets yet — just listing what is there.

```python
from enterprise_adapters.contracts import ReadOnlyResource
from enterprise_adapters.runtime_adapters import (
    ReadOnlyRuntimeDiscoveryAdapter,
    load_runtime_auth_config,
)

adapter = ReadOnlyRuntimeDiscoveryAdapter.from_discovery(
    runtime_tools=[
        ReadOnlyResource(resource_id="create_ticket", name="Create support ticket"),
        ReadOnlyResource(resource_id="list_tickets", name="List open tickets"),
    ],
    case_types_or_equivalent=[
        ReadOnlyResource(resource_id="incident", name="Incident"),
        ReadOnlyResource(resource_id="change_request", name="Change Request"),
    ],
    metadata_by_target_id={
        "incident": {"description": "Production incidents", "priority_levels": ["P1", "P2", "P3"]},
        "change_request": {"description": "Planned system changes"},
    },
)

# Prove you can discover without touching anything
for tool in adapter.list_runtime_tools():
    print("Tool:", tool.name)

metadata = adapter.get_metadata("incident")
print("Incident metadata:", metadata)
```

This is the read-only discovery stage. Nothing is created. Nothing is changed.
You now know what the ticketing system can do.

---

## Step 6 — Run a policy check before any write

When the AI decides a ticket should be created, route it through policy evaluation first.

```python
from enterprise_adapters.policy import PolicyEvaluator

evaluator = PolicyEvaluator()

# Simulate what the AI wants to do
action = {
    "action_name": "create_ticket",
    "write": True,
    "payload": {
        "title": "Payment service restarted by AI",
        "body": "The payment service was restarted after a timeout.",
        "type": "incident",
        "priority": "P2",
    },
}

decision = evaluator.evaluate(action)
print("Decision:", decision.decision)
print("Reasons:", decision.reasons)
```

You will see: `Decision: requires_approval` — because this is a write action with no
approval yet. That is exactly the right behavior.

---

## Step 7 — Generate an approval request

When policy says `requires_approval`, the system generates an approval request.
In a real system this would be sent to a Slack channel, email, or approval workflow.
Here we generate it and show what it contains:

```python
from enterprise_adapters.approvals import ApprovalPackageGenerator
from enterprise_adapters.approval_storage import SQLiteApprovalStore

generator = ApprovalPackageGenerator()
store = SQLiteApprovalStore("/tmp/enterprise-adapters-approvals.sqlite3")

approval = generator.create(
    action=action,
    policy_decision=decision,
    requested_by="on-call-engineer",
)
record = store.save(approval, decision)

print("Approval ID:", record.approval_id)
print("Summary:", record.summary)
print("Send this approval ID to the human reviewer")
```

The approval record is now durable. If the process restarts, the approval is not lost.
Give the `approval_id` to the human reviewer — by Slack message, email, or a UI.

---

## Step 8 — Execute only after human approval

When the human approves (they send back the `approval_id`), wire it into the action
and execute:

```python
from enterprise_adapters.policy import PolicyDecision, PolicyDecisionType
from enterprise_adapters.execution import ApprovedRuntimeActionAdapter

# Human approved — approval_id is now confirmed
approved_action_id = record.approval_id

# Re-evaluate policy now that we have the approval_id
approved_action = dict(action)
approved_action["approval_id"] = approved_action_id

allow_decision = PolicyDecision(
    decision_id=decision.decision_id,
    decision=PolicyDecisionType.ALLOW,
    reasons=["Human approved — proceeding with execution."],
)
approved_action["policy_decision"] = allow_decision

executor = ApprovedRuntimeActionAdapter()
receipt = executor.execute_action(approved_action)

print("Execution ID:", receipt["execution_id"])
print("Status:", receipt["status"])
print("Logs:", receipt["logs"])
```

In a real integration, `execute_action` is where you call the ticketing system's API.
Before doing that, subclass `ApprovedRuntimeActionAdapter` and override `execute_action`
to make the real HTTP call:

```python
import urllib.request
import json as json_lib
import os
from enterprise_adapters.execution import ApprovedRuntimeActionAdapter, ExecutionReceipt
from enterprise_adapters.policy import PolicyDecisionType
from enterprise_adapters.audit import InMemoryAuditTrail

class JiraTicketAdapter(ApprovedRuntimeActionAdapter):
    """Creates Jira tickets after approval."""

    def __init__(self) -> None:
        super().__init__(audit_trail=InMemoryAuditTrail())
        self._jira_url = os.environ["JIRA_API_URL"]
        self._jira_token = os.environ["JIRA_API_TOKEN"]

    def execute_action(self, action: dict) -> dict:
        # Let the parent class enforce the policy + approval gates
        # (this will raise PermissionError if not approved)
        prepared = self.prepare_action(action)

        # Now we know it is approved — make the real API call
        payload = prepared["payload"]
        body = json_lib.dumps({
            "fields": {
                "project": {"key": "OPS"},
                "summary": payload["payload"]["title"],
                "description": payload["payload"]["body"],
                "issuetype": {"name": "Incident"},
            }
        }).encode("utf-8")
        request = urllib.request.Request(
            f"{self._jira_url}/rest/api/2/issue",
            data=body,
            headers={
                "Authorization": f"Bearer {self._jira_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request) as response:
            result = json_lib.loads(response.read().decode("utf-8"))

        return {
            "execution_id": prepared["prepared_action_id"],
            "action_name": action["action_name"],
            "status": "executed",
            "approval_id": action["approval_id"],
            "logs": [f"Jira ticket created: {result.get('key', 'unknown')}"],
            "metadata": {"jira_key": result.get("key")},
        }
```

---

## Step 9 — Add structured logging

Turn on structured logging so every adapter event produces a parseable log line:

```python
from enterprise_adapters.observability import build_structured_logger, log_structured_event

logger = build_structured_logger("enterprise_adapters.ticketing")

log_structured_event(
    logger,
    "ticket.created",
    approval_id=record.approval_id,
    action_name="create_ticket",
    jira_key="OPS-1234",
)
```

Output looks like:

```json
{"event_type": "ticket.created", "level": "INFO", "logger": "enterprise_adapters.ticketing", "message": "ticket.created", "action_name": "create_ticket", "approval_id": "approval_abc123", "jira_key": "OPS-1234"}
```

Pipe this into your log aggregator (Splunk, CloudWatch, Datadog, etc.) and you have a
durable audit trail without any extra tooling.

---

## Step 10 — Write a test for your adapter

Every adapter should have a matching test. Here is the minimum test shape for the
ticketing adapter:

Create `tests/test_jira_ticket_adapter.py`:

```python
from unittest.mock import MagicMock, patch

from enterprise_adapters.policy import PolicyDecision, PolicyDecisionType


def _allow_decision() -> PolicyDecision:
    return PolicyDecision(
        decision_id="policy_test",
        decision=PolicyDecisionType.ALLOW,
        reasons=["Human approved."],
    )


def test_jira_adapter_prepare_requires_approval_id() -> None:
    from enterprise_adapters.execution import ApprovedRuntimeActionAdapter
    adapter = ApprovedRuntimeActionAdapter()

    # Without approval_id, execute_action must raise
    action = {
        "action_name": "create_ticket",
        "write": True,
        "policy_decision": _allow_decision(),
        # no approval_id
    }
    try:
        adapter.execute_action(action)
        raise AssertionError("Expected PermissionError")
    except PermissionError:
        pass


def test_jira_adapter_executes_with_approval() -> None:
    from enterprise_adapters.execution import ApprovedRuntimeActionAdapter
    adapter = ApprovedRuntimeActionAdapter()

    action = {
        "action_name": "create_ticket",
        "write": True,
        "approval_id": "approval_abc123",
        "policy_decision": _allow_decision(),
        "payload": {"title": "Test ticket", "body": "Test body"},
    }
    receipt = adapter.execute_action(action)
    assert receipt["status"] == "executed"
    assert receipt["approval_id"] == "approval_abc123"
    assert len(adapter.audit_events()) == 1
```

Run it:

```bash
python3 -m pytest tests/test_jira_ticket_adapter.py -v
```

---

## Step 11 — Connect to Knowledge Fabric and Intent Fabric

Once your source adapter is loading content, connect it to the knowledge layer:

```bash
# In the knowledge-fabric repo
python3 -m knowledge_fabric.ingestion.cli \
  --source-path ~/enterprise-docs/knowledge-base \
  --source-type markdown \
  --collection enterprise-docs
```

Then ask a question:

```bash
python3 -m knowledge_fabric.mcp.server
```

In another terminal:

```bash
curl -X POST http://localhost:8080/mcp/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "how do I restart the payment service?", "collection": "enterprise-docs"}'
```

The response is an evidence package — a set of relevant chunks from your docs with
retrieval scores. Pass that to Intent Fabric:

```bash
# In the intent-fabric repo
python3 -m intent_fabric.mcp.server
```

```bash
curl -X POST http://localhost:8081/mcp/plan \
  -H "Content-Type: application/json" \
  -d '{
    "evidence": [...evidence from above...],
    "goal": "open an incident ticket for a payment service restart"
  }'
```

Intent Fabric returns a plan with a list of actions. Hand approved write actions to your
enterprise adapter as shown in Steps 6–8.

---

## What you have built

After completing these steps you have:

```text
~/enterprise-docs/          <- private content, never committed
         |
         v
  PrivateMarkdownSourceAdapter     <- reads approved docs only
         |
         v
  knowledge-fabric retrieval       <- indexes and scores evidence
         |
         v
  intent-fabric planning           <- turns evidence into structured actions
         |
         v
  PolicyEvaluator                  <- gates write actions
         |
         v
  ApprovalPackageGenerator         <- creates human-reviewable approval request
         |
         v
  SQLiteApprovalStore              <- persists the approval durably
         |
     [human approves]
         |
         v
  ApprovedRuntimeActionAdapter     <- executes only after ALLOW + approval_id
         |
         v
  Ticketing system / real API      <- your subclass makes the real call
```

The path from question to action is auditable at every step. Nothing is written without
human sign-off. Private content never leaves the private layer.

---

## Common mistakes and how to avoid them

| Mistake | What goes wrong | Fix |
|---------|----------------|-----|
| Committing credentials to git | Secrets in git history are permanent and hard to revoke | Use `os.environ` always; never hardcode tokens |
| Skipping the allowlist check | Any file on disk becomes reachable via the adapter | Always validate `resource_id` against `allowed_roots` |
| Calling `execute_action` without `policy_decision` | `PermissionError` at runtime | Always run `PolicyEvaluator.evaluate(action)` first |
| Building the write path before the read path | Hard to test; high blast radius | Always implement read-only discovery first |
| Putting private endpoints in docs | Internal topology exposed in public or semi-public docs | Use placeholder URLs in docs; real URLs in `.env` only |
| Skipping approval storage | If the process restarts, approvals are lost | Always `store.save()` before calling `execute_action` |

---

## Next: adapting to your own system

To add the next enterprise integration:

1. Copy the relevant source adapter (`source_adapters.py` or `file_source_adapters.py`)
   as your starting point.
2. Implement `list_resources` and `fetch_resource` for your system.
3. Use `ReadOnlyRuntimeDiscoveryAdapter.from_discovery` to describe what the system can do.
4. Subclass `ApprovedRuntimeActionAdapter` and override `execute_action` with your real API call.
5. Wire in `PolicyEvaluator`, `ApprovalPackageGenerator`, and `SQLiteApprovalStore`.
6. Add a test file under `tests/`.

That is the full onboarding loop for any new enterprise system.

---

## Wiring a real enterprise adapter end-to-end

This section is the bridge between the tutorial above and a live production integration.
It answers the one remaining question: *"how do I make `execute_action` call my real system?"*

### The three things you must provide

Every real adapter needs exactly three things:

1. **Credentials** — read from environment variables, never from code
2. **An HTTP call** (or SDK call) to your target system inside `execute_action`
3. **A durable audit trail** — use `SQLiteAuditTrail`, not `InMemoryAuditTrail`, in production

### Full production adapter template

Copy this file to `src/enterprise_adapters/my_system_adapter.py` and fill in the blanks:

```python
"""Production adapter for <Your System Name>.

Environment variables required:
    MY_SYSTEM_API_URL    e.g. https://api.mysystem.example.com
    MY_SYSTEM_API_TOKEN  a long-lived service token or OAuth access token
    AUDIT_DB_PATH        path to the SQLite audit database
"""

from __future__ import annotations

import json
import os
import urllib.request

from enterprise_adapters.audit import build_audit_trail
from enterprise_adapters.execution import ApprovedRuntimeActionAdapter


class MySystemAdapter(ApprovedRuntimeActionAdapter):
    """Sends approved actions to <Your System Name>."""

    def __init__(self) -> None:
        # Use SQLiteAuditTrail in production — reads AUDIT_DB_PATH env var
        super().__init__(audit_trail=build_audit_trail())
        self._api_url = os.environ["MY_SYSTEM_API_URL"].rstrip("/")
        self._api_token = os.environ["MY_SYSTEM_API_TOKEN"]

    def execute_action(self, action: dict) -> dict:
        # 1. Let the parent enforce policy + approval_id before anything else.
        #    This raises PermissionError if the action is not approved.
        prepared = self.prepare_action(action)

        # 2. Build the request payload from the prepared action.
        payload = prepared["payload"]
        body = json.dumps({
            # Replace these keys with what your system's API expects
            "title": payload.get("payload", {}).get("title", ""),
            "body": payload.get("payload", {}).get("body", ""),
        }).encode("utf-8")

        # 3. Make the real API call.
        request = urllib.request.Request(
            f"{self._api_url}/api/actions",          # replace with your endpoint
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

        # 4. Return a standard receipt so the caller can trace what happened.
        return {
            "execution_id": prepared["prepared_action_id"],
            "action_name": action["action_name"],
            "status": "executed",
            "approval_id": action["approval_id"],
            "logs": [f"Action sent to <Your System>: {result}"],
            "metadata": {"system_response": result},
        }
```

### Wiring it into the full flow

```python
import os
from enterprise_adapters.policy import PolicyEvaluator, PolicyDecision, PolicyDecisionType
from enterprise_adapters.approvals import ApprovalPackageGenerator
from enterprise_adapters.approval_storage import SQLiteApprovalStore
from enterprise_adapters.audit import build_audit_trail

# --- Set these in your environment, never in code ---
# MY_SYSTEM_API_URL=https://api.mysystem.example.com
# MY_SYSTEM_API_TOKEN=<token>
# APPROVAL_DB_PATH=/var/lib/enterprise-adapters/approvals.sqlite3
# AUDIT_DB_PATH=/var/lib/enterprise-adapters/audit.sqlite3
# ADAPTER_API_KEY=<32-byte-hex>

evaluator = PolicyEvaluator()
generator = ApprovalPackageGenerator()
store = SQLiteApprovalStore(os.environ["APPROVAL_DB_PATH"])

# Step 1: An AI or user proposes an action
action = {
    "action_name": "create_ticket",
    "write": True,
    "payload": {"title": "Service down", "body": "Payment service timed out."},
}

# Step 2: Policy check
decision = evaluator.evaluate(action)
if decision.decision.value == "requires_approval":
    approval = generator.create(action=action, policy_decision=decision, requested_by="on-call")
    store.save(approval, decision)
    print(f"Send this to your approver: {approval.approval_id}")
    # → Send approval_id via Slack, email, or approval workflow
    # → Wait for human to confirm

# Step 3: Human confirms (they send back the approval_id)
received_approval_id = approval.approval_id   # in reality, received from the human

# Step 4: Re-build with approval and execute
action["approval_id"] = received_approval_id
action["policy_decision"] = PolicyDecision(
    decision_id=decision.decision_id,
    decision=PolicyDecisionType.ALLOW,
    reasons=["Human approved."],
)

from enterprise_adapters.my_system_adapter import MySystemAdapter
adapter = MySystemAdapter()
receipt = adapter.execute_action(action)
print("Done:", receipt["logs"])
```

### Required environment variables for production

Create a `.env` file **outside** the repo (never commit it):

```bash
# Authentication
ADAPTER_API_KEY=<run: openssl rand -hex 32>

# Real embedding provider (choose one)
EMBEDDING_PROVIDER=ollama          # local, free
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBED_MODEL=nomic-embed-text

# OR:
# EMBEDDING_PROVIDER=openai
# OPENAI_API_KEY=sk-...

# Real LLM planner (choose one)
INTENT_PLANNER=ollama
OLLAMA_PLAN_MODEL=llama3

# OR:
# INTENT_PLANNER=openai
# OPENAI_API_KEY=sk-...
# OPENAI_PLAN_MODEL=gpt-4o-mini

# Durable storage
APPROVAL_DB_PATH=/var/lib/enterprise-adapters/approvals.sqlite3
AUDIT_DB_PATH=/var/lib/enterprise-adapters/audit.sqlite3

# Your enterprise system credentials
MY_SYSTEM_API_URL=https://api.mysystem.example.com
MY_SYSTEM_API_TOKEN=<your-token>
```

Load it at startup:

```bash
set -a; source .env; set +a
python3 -m enterprise_adapters.server
```

Or with Docker:

```bash
docker compose --env-file .env -f deploy/local/docker-compose-tls.yml up --build
```

### Minimum test for any real adapter

```python
# tests/test_my_system_adapter.py
import pytest
from enterprise_adapters.policy import PolicyDecision, PolicyDecisionType


def _allow(decision_id: str = "d1") -> PolicyDecision:
    return PolicyDecision(
        decision_id=decision_id,
        decision=PolicyDecisionType.ALLOW,
        reasons=["Human approved."],
    )


def test_adapter_raises_without_approval_id() -> None:
    from enterprise_adapters.execution import ApprovedRuntimeActionAdapter
    adapter = ApprovedRuntimeActionAdapter()
    with pytest.raises(PermissionError):
        adapter.execute_action({
            "action_name": "create_ticket",
            "write": True,
            "policy_decision": _allow(),
            # missing approval_id
        })


def test_adapter_raises_without_policy_decision() -> None:
    from enterprise_adapters.execution import ApprovedRuntimeActionAdapter
    adapter = ApprovedRuntimeActionAdapter()
    with pytest.raises(PermissionError):
        adapter.execute_action({
            "action_name": "create_ticket",
            "write": True,
            "approval_id": "abc",
            # missing policy_decision
        })


def test_adapter_mock_executes_with_both(monkeypatch: pytest.MonkeyPatch) -> None:
    """Smoke-test the base class without calling a real API."""
    from enterprise_adapters.execution import ApprovedRuntimeActionAdapter
    adapter = ApprovedRuntimeActionAdapter()
    receipt = adapter.execute_action({
        "action_name": "create_ticket",
        "write": True,
        "approval_id": "approval-xyz",
        "policy_decision": _allow(),
    })
    assert receipt["status"] == "executed"
    assert receipt["approval_id"] == "approval-xyz"
    assert len(adapter.audit_events()) == 1
```

---

## Production readiness checklist

Before calling your integration production-ready, verify each item below.

### Infrastructure

- [ ] `ADAPTER_API_KEY` is set and rotated on a schedule
- [ ] TLS is terminated by Caddy or an ingress controller (`deploy/local/Caddyfile` or `deploy/kubernetes/ingress.yaml`)
- [ ] The adapter service container is behind a firewall — port 8080 is not publicly reachable
- [ ] `/healthz` is used by your load balancer or Kubernetes readiness probe
- [ ] `APPROVAL_DB_PATH` points to a persistent volume (not the container filesystem)
- [ ] `AUDIT_DB_PATH` points to a persistent volume

### Embeddings and planning

- [ ] `EMBEDDING_PROVIDER` is set to `ollama` or `openai` — **not** `mock`
- [ ] The chosen embedding model dimensions match the `pgvector` column in your database
- [ ] `INTENT_PLANNER` is set to `ollama` or `openai` — rule-based fallback is only for dev
- [ ] You have verified the LLM planner returns sensible plans for your use case

### Adapters

- [ ] Every adapter reads credentials from environment variables
- [ ] No credentials, internal URLs, or private content exist in any file tracked by git
- [ ] Every new adapter has tests in `tests/` covering at least: missing approval_id, missing policy_decision, happy path
- [ ] `execute_action` overrides in your adapters use `build_audit_trail()` so events are durable

### Observability

- [ ] Structured JSON logs from `build_structured_logger` are piped to your log aggregator
- [ ] Approval records in `SQLiteApprovalStore` are backed up on a schedule
- [ ] Audit records in `SQLiteAuditTrail` are backed up on a schedule

### Operations

- [ ] You have read `docs/operations-runbook.md`
- [ ] You have a documented process for rotating `ADAPTER_API_KEY`
- [ ] You have a documented process for pausing write adapters during an incident
- [ ] Someone on the team has run through the adoption guide end-to-end in a staging environment

---

## What "production ready" means for this stack

The framework is production-ready as a deployment scaffold. Your integration is
production-ready when:

1. **Real embeddings** are wired (`EMBEDDING_PROVIDER=ollama` or `openai`)
2. **Real LLM planner** is wired (`INTENT_PLANNER=ollama` or `openai`)
3. **Auth is on** (`ADAPTER_API_KEY` is set and TLS is in front)
4. **Durable audit trail** is on (`AUDIT_DB_PATH` points to a persistent volume)
5. **Your system adapter** has a working `execute_action` override with real API calls
6. **All five items above are tested** in a staging environment before go-live

The rule-based planner and mock embeddings remain available — they make local dev
and CI fast. But they must not be the active providers in production.


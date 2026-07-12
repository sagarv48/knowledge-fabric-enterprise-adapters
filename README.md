# Knowledge Fabric Enterprise Adapters

This is the private adapter layer that connects the open-source cores to enterprise-only systems.

- **Knowledge Fabric** provides evidence packages.
- **Intent Fabric** turns evidence into structured plans and approval-ready actions.
- **This repo** adds private source adapters and private runtime adapters around those public cores.

The main idea is simple:

> keep retrieval and planning open and reusable, keep enterprise-specific details private, and only allow write actions after policy and human approval.

## What this repository is for

Use this repo when you need to:

- ingest approved private documents into the knowledge layer,
- discover private runtime metadata in a read-only way,
- prepare actions for review without executing them,
- execute approved actions behind policy and audit gates,
- keep deployment details, secrets, and private system knowledge out of the public repos.

## Runtime shape

This repo now includes a tiny private adapter service with a health endpoint so the
deployment manifests have a real target:

- `GET /healthz` for readiness and liveness checks
- `GET /` for a simple runtime status response

## Production shape at a glance

```text
Codebases / Repos      SharePoint / File Stores      Websites / Wikis      Videos / Media
        \                     |                           |                     /
         \                    |                           |                    /
          -> Source Adapters -> Normalization -> Knowledge Fabric Retrieval ->
             Evidence Packages -> Intent Fabric Planning -> Private Runtime Adapters
```

In plain English:

- source adapters pull content in,
- retrieval finds the best evidence,
- planning turns evidence into a safe next step,
- private adapters carry out approved actions only when allowed.

## What belongs here

- Private source adapters
- Read-only runtime discovery adapters
- Policy-gated runtime adapters
- Environment-specific deployment setup
- Secret handling and environment variables
- Audit, logging, and observability wiring

## What does not belong here

- Public retrieval logic
- Public planning logic
- Open-source contract definitions that already live in Phase 1 or Phase 2
- Credentials committed to git
- Internal URLs or private source content in public docs

## How to use this repo

### 1. Start with the adoption guide

The fastest way to onboard is to follow the adoption guide, which walks through a complete
integration end-to-end using a real use case:

```
docs/adoption-guide.md
```

It covers: loading private docs → discovery → policy evaluation → approval → execution →
connecting to Knowledge Fabric and Intent Fabric.

### 2. Then read the broader docs

- `docs/adoption-guide.md` ← **start here**
- `docs/phase-boundaries.md`
- `docs/architecture.md`
- `docs/implementation-plan.md`
- `docs/source-adapters.md`
- `docs/runtime-adapters.md`
- `docs/security-model.md`
- `docs/operations-runbook.md`

They explain the boundaries and the order of work.

### 2. Build read-only integrations first

The safest first step is always discovery:

- read approved private content,
- list runtime tools or equivalent metadata,
- fetch metadata only,
- verify what exists before writing anything.

### 3. Add policy gates before any writes

No write path should be active until:

1. policy checks pass,
2. human approval is captured,
3. the action payload is prepared and auditable.

### 4. Keep secrets out of git

Use environment variables or secret stores for:

- private endpoints,
- auth tokens,
- runtime credentials,
- deployment-specific values.

### 5. Keep runtime and retrieval separate

This repo should not duplicate the retrieval engine or planning engine. It should only adapt to them.

### 6. Start with Stage 1

For the current implementation, Stage 1 is the focus:

- approved source roots,
- read-only private markdown loading,
- resource listing,
- resource fetch with normalized content,
- contract tests that prove the allowlist behavior.

If you only want to try the current code, run:

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

Then import and use the source adapter directly:

```python
from pathlib import Path
from enterprise_adapters.source_adapters import PrivateMarkdownSourceAdapter

adapter = PrivateMarkdownSourceAdapter(
    source_root=Path("/approved/private/root"),
    allowed_roots=[Path("/approved/private/root/docs")],
)

resources = adapter.list_resources()
payload = adapter.fetch_resource("docs/policy.md")
```

### 7. Think in adapters, not one giant app

The production pattern is usually:

1. pull content from each source type,
2. normalize it into one shared shape,
3. let Knowledge Fabric retrieve evidence,
4. let Intent Fabric turn evidence into a plan,
5. let this repo handle private systems only after approval.

## Example development flow

```text
Approved source -> source adapter -> Knowledge Fabric
Knowledge Fabric evidence -> Intent Fabric
Intent Fabric plan -> policy check -> approval
Approved action -> runtime adapter -> private system
```

## Repo structure

```text
knowledge-fabric-enterprise-adapters/
  docs/
  src/enterprise_adapters/
  tests/
```

Current code includes:

- adapter contracts,
- basic package entrypoint,
- health-check HTTP service,
- docs for boundaries and operations,
- local and Kubernetes deployment manifests,
- minimal tests.

## Suggested implementation order

1. Read-only source ingestion
2. Read-only runtime discovery
3. Policy and approval gates
4. Simulated payload preparation
5. Approved runtime execution

## Stage 2 snapshot

The current runtime discovery starter includes:

- a read-only runtime discovery adapter,
- environment-based runtime auth settings,
- list/fetch methods for tools and case-like targets,
- tests that prove the read-only contract.

Example usage:

```python
from enterprise_adapters.contracts import ReadOnlyResource
from enterprise_adapters.runtime_adapters import ReadOnlyRuntimeDiscoveryAdapter

adapter = ReadOnlyRuntimeDiscoveryAdapter.from_discovery(
    runtime_tools=[ReadOnlyResource(resource_id="tool-1", name="list_runtime_tools")],
    case_types_or_equivalent=[ReadOnlyResource(resource_id="case-1", name="incident")],
    metadata_by_target_id={"case-1": {"description": "Incident metadata"}},
)

tools = adapter.list_runtime_tools()
metadata = adapter.get_metadata("case-1")
```

## Current implementation status

Implemented:

- private repo scaffold,
- adapter contracts,
- private docs set,
- basic CLI entrypoint,
- initial tests,
- Stage 1 read-only source ingestion,
- Stage 2 read-only runtime discovery,
- Stage 3 policy and approval gate,
- Stage 4 simulation-only action preparation,
- Stage 5 approved runtime execution.
- Stage 6 file-store source adapter,
- Stage 7 runtime snapshot discovery adapter,
- Stage 8 deployment manifests,
- Stage 9 observability wiring,
- Stage 10 persistent approval storage,
- containerized health service and deployment targets.

Not implemented yet:

- vendor-specific enterprise integrations,
- real secret backends,
- managed storage backends for large-scale approval retention.

## Next step

The staged implementation is complete.
Next, you can harden the repo with deployment manifests, observability wiring, and persistent approval storage.

If you want to keep building toward real production use, the next practical milestone is to add one more read-only source adapter from a different source type (for example a file store or website crawler) and one more runtime discovery adapter for a different private system.

## Quick start

```bash
python3 -m pip install -e ".[dev]"
python3 -m pytest
python3 -m enterprise_adapters
```

To start the private health service locally:

```bash
python3 -m enterprise_adapters.server
```

To run the container locally:

```bash
docker compose -f deploy/local/docker-compose.yml up --build
```

## Phase boundaries

- Phase 1: Knowledge Fabric — retrieval only
- Phase 2: Intent Fabric — planning, approval, simulation only
- Phase 3: this repo — private enterprise adapters

Keep those boundaries sharp. That makes the whole system easier to reason about.

## Contributing

If you add a new adapter or deployment shape, include:

- a short doc update,
- tests for the contract,
- a clear note about whether it is read-only or write-capable.

## License

This repo is private. Follow the same internal governance you use for enterprise code.

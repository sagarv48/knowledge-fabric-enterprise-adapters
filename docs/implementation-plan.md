# Phase 3 Implementation Plan

This plan starts with the safest possible path: read-only integrations first, then policy gates, then approved write actions.

## Guiding principle

```text
Read-only first -> policy gate -> human approval -> simulated payload -> approved execution
```

Keep the private adapter layer small, auditable, and easy to explain.

## Stage 1: Read-only source ingestion

Goal: bring approved private content into the enterprise adapter layer without any write actions.

### Build

- source root allowlist
- private markdown loader
- private document metadata loader
- content normalization
- adapter contract tests

### Done when

- approved documents can be listed and fetched,
- no secrets are committed,
- no public repo contains private source details.

## Stage 2: Read-only runtime discovery

Goal: inspect private runtime systems without changing anything.

### Build

- runtime tool discovery
- case-type-or-equivalent discovery
- metadata fetch
- environment variable based auth configuration

### Done when

- runtime targets can be listed,
- metadata can be fetched,
- no write APIs are exposed.

## Stage 3: Policy and approval gate

Goal: prevent direct writes and make all actions reviewable.

### Build

- policy evaluator
- approval request model
- approval persistence shape
- audit trail for decisions

### Done when

- write actions are blocked by default,
- every write request has an approval path,
- policy decisions are explicit and logged.

## Stage 4: Simulated payload preparation

Goal: prepare action payloads without executing anything.

### Build

- action preparation adapter
- payload validation
- dry-run/simulation output
- contract checks against Intent Fabric payloads

### Done when

- payloads can be prepared safely,
- simulation output is deterministic,
- no external side effects occur.

## Stage 5: Approved runtime execution

Goal: only execute actions after approval and policy checks.

### Build

- execution adapter
- approval verification
- execution logging
- rollback/incident notes where relevant

### Done when

- execution requires explicit approval,
- logs capture what happened and why,
- write paths are isolated from read-only discovery.

## Suggested implementation order

1. source adapter contracts
2. read-only source loader
3. runtime discovery contracts
4. read-only runtime discovery adapter
5. policy engine
6. approval request generator
7. simulation/payload preparation
8. approved write adapter
9. deployment manifests
10. observability and audit

The deployment-manifest step is now implemented with:

- `Dockerfile`
- `deploy/local/docker-compose.yml`
- `deploy/kubernetes/namespace.yaml`
- `deploy/kubernetes/configmap.yaml`
- `deploy/kubernetes/persistentvolumeclaim.yaml`
- `deploy/kubernetes/deployment.yaml`
- `deploy/kubernetes/service.yaml`

## Cross-repo dependencies

- **Knowledge Fabric** provides evidence packages.
- **Intent Fabric** provides plans, approvals, and simulation results.
- **This repo** translates approved enterprise intent into private adapter behavior.

## Early success criteria

The first practical milestone is complete when:

- one private source adapter works end-to-end,
- one read-only runtime discovery adapter works end-to-end,
- the adapter layer can explain what it would do without doing it,
- policy and approval gates are present before any write action exists.

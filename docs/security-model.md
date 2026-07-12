# Security Model

Phase 3 follows a simple rule: **read first, write later, only with approval**.

## Security principles

- Private repo only
- No credentials in source
- Human approval before writes
- Audit everything important
- Prefer least privilege for private systems

## Boundary reminders

- Knowledge Fabric and Intent Fabric remain vendor-neutral dependencies
- Runtime adapters do not replace retrieval or planning
- Simulation must stay separate from execution

## Approved execution rule

No execution path should proceed unless both of the following are true:

1. policy decision is `allow`
2. human approval id is present

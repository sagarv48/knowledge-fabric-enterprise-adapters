# Phase 3 Boundaries

## In scope

- Private source adapters
- Read-only runtime metadata
- Policy-gated action execution
- Deployment and environment wiring
- Audit and observability

## Out of scope

- Public retrieval logic
- Public planning logic
- Credential storage in source control
- Product-specific content in open-source repos

## Operating principle

Start with read-only flows. Add write actions only after policy checks, approvals, and logging are in place.

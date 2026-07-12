# Knowledge Fabric Enterprise Adapters

This is the private adapter layer that sits between the open-source cores:

- **Knowledge Fabric** for evidence retrieval
- **Intent Fabric** for planning, approvals, and simulation

It is intentionally separate from the public repos so enterprise-specific details stay isolated.

## What belongs here

- Private source adapters
- Read-only runtime metadata adapters
- Policy-gated runtime adapters
- Environment-specific deployment and secrets handling
- Audit and observability wiring

## What does not belong here

- Public retrieval logic
- Public planning logic
- Product-specific details in open-source docs
- Credentials in source control

## Starting point

This repo begins with contracts, boundaries, and adapter scaffolding. Real integrations should be added gradually, starting with read-only flows first.

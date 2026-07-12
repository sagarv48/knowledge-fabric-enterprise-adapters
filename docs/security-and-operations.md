# Security and Operations

## Security rules

- Do not commit credentials.
- Use environment variables or secret stores.
- Keep private adapter logs free of sensitive payloads when possible.
- Enforce policy and approval gates before write actions.

## Operational rules

- Prefer read-only adapters first.
- Add observability before enabling write actions.
- Keep deployment examples private.

## Human note

If a flow feels hard to explain, it probably needs a better boundary. Keep the adapter layer simple and auditable.

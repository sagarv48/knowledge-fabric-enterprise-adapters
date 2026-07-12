# Operations Runbook

## Startup checklist

1. Verify environment variables are set.
2. Verify read-only adapters work.
3. Verify approval gates are active.
4. Verify audit logging is enabled.

## Before any write action

1. Run policy checks.
2. Capture human approval.
3. Prepare action payload.
4. Execute only if explicitly approved.

## Stage 5 execution shape

The approved execution adapter should:

- reject actions without a policy decision,
- reject actions without approval,
- record an audit event when execution completes,
- return a receipt that can be traced later.

## Incident response

- Pause write adapters first
- Preserve logs and audit records
- Revert to read-only mode if needed

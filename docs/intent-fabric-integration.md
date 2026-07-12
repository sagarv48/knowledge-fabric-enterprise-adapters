# Intent Fabric Integration

Phase 3 consumes plan, approval, and simulation payloads from Intent Fabric.

```text
Plan
  ->
Policy Decision
  ->
Approval Request
  ->
Simulation Result
  ->
Private runtime adapter
```

Runtime adapters should only act after policy and approval gates are satisfied.

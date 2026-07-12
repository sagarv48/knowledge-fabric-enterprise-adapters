# Phase 3 Architecture

```text
Knowledge Fabric
  ->
Evidence Packages
  ->
Intent Fabric
  ->
Plans / Approval Packages / Simulation Results
  ->
Private Enterprise Adapters
  ->
Read-only metadata or policy-gated actions
```

Phase 3 is intentionally private and sits outside the open-source cores.

## Production shape

In a real enterprise setup, the private adapter layer usually sits between many source types and the two public cores:

```text
Codebases / Repos      SharePoint / File Stores      Websites / Wikis      Videos / Media
        \                     |                           |                     /
         \                    |                           |                    /
          -> Source Adapters -> Normalization -> Knowledge Fabric Retrieval ->
             Evidence Packages -> Intent Fabric Planning -> Private Runtime Adapters
```

## What each part does

- **Source adapters** bring in approved private content from codebases, document stores, websites, and transcripts.
- **Normalization** turns those different inputs into a common shape that can be indexed and searched.
- **Knowledge Fabric** retrieves the most relevant evidence.
- **Intent Fabric** turns that evidence into a safe plan, approval package, or simulation result.
- **Private runtime adapters** only act after policy and approval gates are satisfied.

The important scaling idea is not “one giant AI system.” It is many small, well-bounded adapters feeding one shared evidence and planning flow.

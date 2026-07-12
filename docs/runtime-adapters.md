# Runtime Adapters

Runtime adapters interact with private systems in a read-only or policy-gated manner.

## Read-only discovery first

Required discovery methods:

- `list_runtime_tools`
- `list_case_types_or_equivalent`
- `get_metadata`

## Write path

Write-capable actions must remain disabled until:

1. policy checks pass
2. human approval is captured
3. the action is explicitly prepared for execution

## Environment variables

```text
RUNTIME_API_BASE_URL=
RUNTIME_AUTH_TOKEN=
RUNTIME_ENV=local
```

Leave secrets blank in committed examples.

## Stage 2 starter implementation

The current codebase includes a generic read-only runtime discovery adapter that:

- lists runtime tools,
- lists case-types-or-equivalent targets,
- fetches metadata for a target id,
- loads connection settings from environment variables.

That means you can inspect a private runtime system without giving it write permission yet.

## Stage 4 preview

When you are ready to simulate action payloads, the repo also includes a simulation-only runtime action adapter that:

- prepares payloads without executing them,
- marks payloads as simulated and validated,
- emits simulation results with no external side effects,
- respects policy decisions before proceeding.

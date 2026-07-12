# Knowledge Fabric Integration

Phase 3 reads evidence packages from Knowledge Fabric.

The integration contract is intentionally simple:

```text
query_text
items[]
retrieval_summary
```

Phase 3 adapters can use the evidence to enrich private source lookups or prepare operational context, but they should not replace the retrieval layer.

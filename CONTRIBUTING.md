# Contributing to Knowledge Fabric Enterprise Adapters

Thank you for contributing to Enterprise Adapters! We welcome contributions to source connectors, runtime action gates, and security sanitization.

---

## Development Setup

### 1. Prerequisites
- Python 3.11 or 3.12
- Git

### 2. Setup Virtual Environment
```bash
git clone https://github.com/sagarv48/knowledge-fabric-enterprise-adapters.git
cd knowledge-fabric-enterprise-adapters

python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

python3 -m pip install --upgrade pip
python3 -m pip install -e ".[dev]"
```

---

## Coding Standards & Testing

Before submitting a pull request, ensure all checks pass:

```bash
# 1. Run unit tests
python3 -m pytest tests/

# 2. Check code style and linting
python3 -m ruff check src tests

# 3. Verify type checking
python3 -m pyright src
```

---

## Adding a New Source Connector

To add a new SaaS or document source connector:

1. Subclass `StandardSourceAdapter` in `src/enterprise_adapters/standard_source_adapters.py` or implement `KnowledgeSourceAdapter` in `src/knowledge_fabric_adapters/contracts.py`.
2. Implement `list_resources` and `read_resource` returning `ReadOnlyResource` objects with complete metadata (breadcrumbs, titles, URLs).
3. Ensure no raw credentials or Bearer tokens leak in log messages by applying `sanitize_log_message`.
4. Add comprehensive unit tests mocking HTTP responses using the standard library.

---

## Pull Request Guidelines

1. Create a feature branch: `git checkout -b feat/my-new-connector`.
2. Keep third-party dependencies to an absolute minimum (the core package uses the Python standard library only).
3. Ensure all tests pass with zero regressions.

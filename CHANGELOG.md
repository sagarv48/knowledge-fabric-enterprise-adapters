# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-09-06

### Added
- Enterprise SaaS source connectors for Confluence, Notion, Google Drive, and Jira.
- Automated secret scrubber and redaction filter (`SecretScrubber`) stripping Bearer tokens, passwords, and sensitive query params from HTTP logs and exceptions.
- Intent Fabric HMAC-SHA256 signature verification gate for action execution adapters.
- Multi-stage hardened `Dockerfile` with non-root user (`UID 10001`), `/healthz` liveness probes, and Kubernetes manifests (`deploy/kubernetes`).
- Automated document sync CLI (`knowledge-fabric-sync`).
- End-to-end demo scripts (`demo/01-ingest-k8s-docs.sh` and `demo/02-demo.py`) for live Path A evaluation with Kubernetes documentation and GitHub issue creation.

### Changed
- Standardized ruff and pyright CI workflows with Python 3.11 and 3.12 support.
- Aligned demo database configuration defaults with `knowledge-fabric` production conventions.

## [0.1.0] - 2026-07-12

### Added
- Initial enterprise adapter interfaces and connector scaffolding.

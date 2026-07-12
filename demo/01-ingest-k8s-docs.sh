#!/usr/bin/env bash
# demo/01-ingest-k8s-docs.sh
#
# Step 1: Sparse-clone the Kubernetes website repo (only Markdown docs)
#         and ingest into knowledge-fabric.
#
# Prerequisites:
#   - knowledge-fabric installed and PostgreSQL running (docker compose up -d)
#   - python3 -m pip install -e ".[dev]" in the knowledge-fabric repo
#
# Usage:
#   cd knowledge-fabric-enterprise-adapters
#   bash demo/01-ingest-k8s-docs.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K8S_DOCS_DIR="${SCRIPT_DIR}/../_k8s-docs"
KF_DIR="${SCRIPT_DIR}/../../knowledge-fabric"

echo "==> Sparse-cloning Kubernetes docs (English only)..."
if [ ! -d "$K8S_DOCS_DIR" ]; then
  git clone \
    --depth 1 \
    --filter=blob:none \
    --sparse \
    https://github.com/kubernetes/website.git \
    "$K8S_DOCS_DIR"
  git -C "$K8S_DOCS_DIR" sparse-checkout set content/en/docs
  echo "    Cloned to $K8S_DOCS_DIR"
else
  echo "    Already cloned, pulling latest..."
  git -C "$K8S_DOCS_DIR" pull --depth 1
fi

DOC_COUNT=$(find "$K8S_DOCS_DIR/content/en/docs" -name "*.md" | wc -l | tr -d ' ')
echo "==> Found $DOC_COUNT Markdown files."

echo "==> Ingesting into knowledge-fabric..."
cd "$KF_DIR"
python3 -m knowledge_fabric.ingestion.cli \
  --source-path "$K8S_DOCS_DIR/content/en/docs" \
  --source-type markdown \
  --collection k8s-docs

echo ""
echo "Done. K8s docs are now indexed in knowledge-fabric."
echo "Run demo/02-demo.py to start the interactive demo."

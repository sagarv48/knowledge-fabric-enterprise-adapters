# Path A Demo: Kubernetes docs → AI plan → GitHub Issue

This demo runs the full end-to-end stack:

```
K8s docs (open-source Markdown)
    ↓  ingested via PrivateMarkdownSourceAdapter
knowledge-fabric  (lexical retrieval)
    ↓  evidence package
intent-fabric  (Foundry Local / mistral-nemo → real AI plan)
    ↓  plan + policy check
enterprise-adapters  (approval gate → GitHubIssueAdapter)
    ↓  approved
sagarv48/knowledge-fabric-demo  (GitHub issue created)
```

---

## Prerequisites

### 1. Foundry Local running with Mistral loaded

```bash
foundry server start
foundry model load mistral-nemo-12b-instruct
# verify:
foundry status
```

### 2. A GitHub personal access token

Create one at https://github.com/settings/tokens/new

Required scope: **repo** (for issue creation on public repos a fine-grained PAT with `Issues: write` on `sagarv48/knowledge-fabric-demo` is enough).

### 3. Packages installed

Option A — Install packages (recommended):
```bash
pip install knowledge-fabric intent-fabric knowledge-fabric-enterprise-adapters
```

Option B — Sibling local clones:
```bash
cd ../knowledge-fabric && pip install -e ".[dev]"
cd ../intent-fabric    && pip install -e ".[dev]"
cd ../knowledge-fabric-enterprise-adapters && pip install -e ".[dev]"
```

### 4. PostgreSQL running (for knowledge-fabric retrieval)

```bash
cd ../knowledge-fabric
docker compose up -d
```

---

## Step 1 — Ingest K8s docs

```bash
# From the knowledge-fabric-enterprise-adapters root:
bash demo/01-ingest-k8s-docs.sh
```

This sparse-clones only `content/en/docs/` from the Kubernetes website repo (~150 MB)
and ingests all Markdown files into the local PostgreSQL database.

---

## Step 2 — Set environment variables

Create a `.env` file **outside** any repo:

```bash
# GitHub
export GITHUB_TOKEN=ghp_yourtoken
export GITHUB_ISSUE_REPO=sagarv48/knowledge-fabric-demo

# Foundry Local planner (Mistral)
export INTENT_PLANNER=foundry
export FOUNDRY_BASE_URL=http://127.0.0.1:61633
export FOUNDRY_PLAN_MODEL=mistral-nemo-12b-instruct-generic-gpu

# knowledge-fabric database (docker-compose defaults)
export KF_DB_HOST=localhost
export KF_DB_PORT=5432
export KF_DB_NAME=knowledge_fabric
export KF_DB_USER=knowledge_fabric
export KF_DB_PASSWORD=<your-password>
```

Load it:

```bash
set -a; source .env; set +a
```

---

## Step 3 — Run the demo

```bash
cd knowledge-fabric-enterprise-adapters
python3 demo/02-demo.py
```

You will be prompted to:
1. Enter a question (or press Enter for the default)
2. See the evidence retrieved and the AI plan
3. Approve or decline the GitHub issue creation

Example questions that work well:

- `Why is my pod stuck in CrashLoopBackOff?`
- `How do I set resource limits on a container?`
- `What is the difference between a Deployment and a StatefulSet?`
- `How does Kubernetes handle node failures?`

---

## What you will see

```
[1/5] Retrieving evidence from K8s docs...
       Found 5 relevant chunks.
       Top result: concepts/workloads/pods/pod-lifecycle.md

[2/5] Generating action plan...
[PLANNER] Using: FoundryLocalLLMPlanner
       Plan: Create an incident ticket to investigate the CrashLoopBackOff issue.
       Steps: 1
         → [ticket_create] Create incident ticket

[3/5] Policy decision: requires_approval
       • Plan contains simulated user-impacting actions that require approval.

[4/5] This action requires human approval.
       Approve and create a GitHub issue? [y/N]: y

[5/5] Creating GitHub issue...

======================================================================
  ✅ Issue created!
     URL:    https://github.com/sagarv48/knowledge-fabric-demo/issues/1
     Number: #1
     Repo:   sagarv48/knowledge-fabric-demo
======================================================================
```

---

## Running without PostgreSQL

The demo works even if PostgreSQL is not running. Evidence retrieval will return
nothing, but the Foundry Local planner will still generate a real AI plan from
the query alone. The GitHub issue will still be created.

---

## Notes

- `INTENT_PLANNER=foundry` uses `mistral-nemo-12b-instruct` via Foundry Local's
  OpenAI-compatible endpoint — no API key, fully offline.
- Embeddings use `MockEmbeddingProvider` (no approved embedding models in Foundry).
  Retrieval is real and effective via PostgreSQL full-text search.
- Issues are created in `sagarv48/knowledge-fabric-demo` — a safe test target.
  Delete or close them freely.

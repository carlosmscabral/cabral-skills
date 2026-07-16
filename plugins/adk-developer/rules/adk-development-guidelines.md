---
trigger: always_on
description: Guidelines for high-fidelity Google ADK development, grounded in the bundled agents-cli skills, with pre-flight validation and deployment discipline.
---
# Google ADK Development Guidelines

You are in a workspace configured with the **adk-developer** plugin, which bundles the ADK skills
listed below. Follow these guidelines during any Agent Development Kit (ADK) work.

### 0. Shallow Copy of Python ADK Samples
ALWAYS start by cloning a shallow copy of the Python ADK samples (`git clone --depth 1 https://github.com/google/adk-samples.git` and check the `python/` subfolder), which includes proven ADK Agents in Python. Use a `/tmp` directory or a gitignored/antigravity ignored local folder. 

### 1. Use the bundled agents-cli skills first
Before running commands, consult the relevant bundled skill (read its `skills/<name>/SKILL.md`):
- `google-agents-cli-workflow` — the end-to-end ADK development lifecycle and command flow. You must ALWAYS pre-load this tool as it guides on the usage of the rest.
- `google-agents-cli-scaffold` — creating/structuring agent projects.
- `google-agents-cli-adk-code` — ADK agent/tool/callback code patterns.
- `google-agents-cli-adk-frontend` — connecting clients/frontends to the deployed agent.
- `google-agents-cli-adk-auth` — configuring 3-legged OAuth (3LO) and GCP Agent Identity Auth Manager integration.
- `google-agents-cli-eval` — eval sets and scoring.
- `google-agents-cli-deploy` — Agent Runtime / Cloud Run / GKE deployment.
- `google-agents-cli-publish` — publishing / registering the agent.
- `google-agents-cli-observability` — tracing, logging, analytics.


### 2. Documentation grounding
Ground decisions on the bundled skills first, then official ADK/GCP docs. If the `adk-docs-mcp`
server (from this plugin's `mcp_config.json`) is available, use its read-only tools to fetch
real-time classes, schemas, and SDK specs. Consider also searching for examples under python samples that are related to the agent in scope to find best-practices. If still unclear/unsure, ground your implementation/decisions on the ADK Code itself (you should have it locally as a lib). 

### 3. Pre-flight validation before deploy
Before any long-running Cloud Run / Agent Runtime deployment, validate locally: parse and assert
Pydantic models, agent manifests, and tool definitions with a fast local dry-run. Do not push to
the cloud if local validation fails.



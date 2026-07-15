---
trigger: always_on
description: Guidelines for high-fidelity Google ADK development, grounded in the bundled agents-cli skills, with pre-flight validation and deployment discipline.
---
# Google ADK Development Guidelines

You are in a workspace configured with the **adk-developer** plugin. Its skills are installed
under `.agents/skills/` (this plugin bundles them). Follow these guidelines during any Agent
Development Kit (ADK) work.

> **Applying these rules:** `agy plugin install` registers the plugin's skills/mcp but NOT its
> `rules/`. Copy this file into the project so it loads: `cp <plugin>/rules/*.md .agents/rules/`.

### 1. Use the bundled agents-cli skills first
Before running commands, consult the relevant skill (read its `.agents/skills/<name>/SKILL.md`):
- `google-agents-cli-workflow` — the end-to-end ADK development lifecycle and command flow.
- `google-agents-cli-scaffold` — creating/structuring agent projects.
- `google-agents-cli-adk-code` — ADK agent/tool/callback code patterns.
- `google-agents-cli-adk-frontend` — connecting clients/frontends to the deployed agent.
- `google-agents-cli-eval` — eval sets and scoring.
- `google-agents-cli-deploy` — Agent Runtime / Cloud Run / GKE deployment.
- `google-agents-cli-publish` — publishing / registering the agent.
- `google-agents-cli-observability` — tracing, logging, analytics.

### 2. Pre-flight validation before deploy
Before any long-running Cloud Run / Agent Runtime deployment, validate locally: parse and assert
Pydantic models, agent manifests, and tool definitions with a fast local dry-run. Do not push to
the cloud if local validation fails.

### 3. Documentation grounding
Ground decisions on the bundled skills first, then official ADK/GCP docs. If the `adk-docs-mcp`
server (from this plugin's `mcp_config.json`) is available, use its read-only tools to fetch
real-time classes, schemas, and SDK specs. Do not fetch source from the network otherwise.

### 4. Secure end-user auth
When propagating end-user identity to downstream APIs (e.g. BigQuery), assert the token matches
the acting end user — never a broad service identity standing in for the user.

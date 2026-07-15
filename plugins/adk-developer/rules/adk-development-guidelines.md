---
trigger: always_on
description: Guidelines for high-fidelity Google ADK development, pre-flight validations, and GCP deployment grounding.
---
# Google ADK Development and Deployment Guidelines

You are operating inside a workspace configured with the **ADK Developer Plugin**. Follow these guidelines strictly during any Agent Development Kit (ADK) development, testing, and deployment.

### 1. Use the bundled `agents-cli` AI Skills (already installed)
- This plugin **materializes** the Google `agents-cli` skill playbooks into `.agents/plugins/adk-developer/skills/` at promotion time. They are already present — you do **not** fetch, clone, or install anything to get them.
- Consult the right skill for the task before running commands:
  - `google-agents-cli-workflow` — the end-to-end development lifecycle and command flow.
  - `google-agents-cli-scaffold` — creating and structuring new agent projects.
  - `google-agents-cli-adk-code` — writing ADK agent/tool/callback code.
  - `google-agents-cli-adk-frontend` — connecting clients/frontends to the deployed agent.
  - `google-agents-cli-eval` — building eval sets and scoring agent behavior.
  - `google-agents-cli-deploy` — deploying to Agent Runtime, Cloud Run, or GKE.
  - `google-agents-cli-publish` — publishing/registering the agent.
  - `google-agents-cli-observability` — tracing, logging, and analytics.
- Each skill's `references/` directory holds the detailed patterns (workflows, sample references, flags, schemas). **Read those bundled references** rather than reaching for external sources.

### 2. Pre-Flight Pydantic & Schema Validation
- **Dry-Run Validations**: Before triggering any long-running Cloud Run or GCP Agent Runtime deployment, **always validate local Pydantic rules, schemas, agent manifests, and tool definitions locally**.
- Write simple, fast-running Python tests or a local dry-run script to parse and assert the validity of your Pydantic models and configurations.
- Do NOT push code to Cloud environments if local validation fails — this prevents wasteful waits on simple syntax or schema mismatches.

### 3. Documentation & Code Grounding
- **Primary Source Grounding**: Ground architectural decisions on the bundled `agents-cli` skills first, then official ADK/GCP documentation.
- **ADK Docs MCP Server**: If the `adk-docs-mcp` server is configured, use its read-only tools (`list_doc_sources`, `fetch_docs`) to retrieve real-time classes, schemas, and SDK specifications. This is documentation retrieval via a declared server — not skill installation. (In an air-gapped posture this server may be unavailable; fall back to the bundled skill references.)
- **Local Source Inspection**: For advanced tool callbacks or complex execution states, inspect the **locally installed** `agents-cli` / ADK SDK library source in the workspace environment to confirm function signatures. Do not fetch source from the network.

### 4. Reference-First Implementation (from bundled skills)
- Patterns for User OAuth, token propagation, BigQuery MCP connections, and credential caching are captured in the bundled skills' references — start with `google-agents-cli-workflow/references/samples.md` and `google-agents-cli-adk-code/references/`.
- Model your local schemas, credential caches, and tool architectures on those bundled, version-pinned references. Do **not** clone or read external sample repositories at runtime — this keeps behavior deterministic and compatible with the air-gapped `strict-banking-harness` posture. If a newer upstream sample is genuinely required, it must be vendored into the `agents-cli` skills upstream (see the cabral-skills sync process) and delivered as a pinned release — never pulled ad hoc.

### 5. Secure Auth & End-User Propagation
- Use the auth patterns in `google-agents-cli-deploy` and `google-agents-cli-adk-frontend` (plus, if available, the `adk-docs-mcp` server) for GCP authentication and managed Auth Server specifications.
- When handling End-User propagation, assert that the authentication token passed to downstream APIs (like BigQuery) matches the exact credentials of the acting end user — never a broad service identity standing in for the user.

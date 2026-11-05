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
Before any long-running Cloud Run, GKE, BYOC container, or Agent Runtime deployment, validate locally: verify clean package imports across the module DAG, assert Pydantic models and `FunctionTool` JSON schema declarations, and run deterministic callback/unit smoke checks in seconds. Do not build or push to the cloud if local validation fails.

### 4. Modular Package Architecture (Anti-Monolith)
Keep Python ADK agents structured as clean, runtime-agnostic packages that deploy identically across Docker/BYOC containers (Cloud Run, GKE), `adk web` / `agents-cli`, or managed Agent Runtime:
- **`agent.py` is strictly a thin composition root (`<= 150-200` lines):** It wires `root_agent` (`LlmAgent` / workflow agents) and `App`/plugins, while `__init__.py` exports the public entrypoint (`root_agent` / `agent`). Never accumulate prompts, regex banks, HTTP clients, or business logic inside `agent.py`.
- **Split proactively once total agent code exceeds `~250` lines or spans `>= 3` concerns:** Partition into single-responsibility modules/subpackages instead of growing `agent.py` + `tools.py` into monoliths during eval/hardening iterations:
  - `config.py` — typed env/settings, constants, canonical fallback strings.
  - `prompts.py` — system instructions and prompt templates.
  - `tools/` — cohesive domain tool modules; keep `FunctionTool` parameter types (`ToolContext`, Pydantic schemas) imported at module top level (never hidden behind `TYPE_CHECKING`) so `typing.get_type_hints()` resolves cleanly under `from __future__ import annotations`.
  - `guardrails/` — deterministic `before_model_callback` / `after_model_callback` / `before_tool_callback`, patterns, and sanitizers.
  - `model_router.py`, `memory.py`, `telemetry.py`, `sub_agents/` — dedicated modules added only when those capabilities exist.
- **Strict acyclic import DAG & lazy I/O:** Enforce one-way imports (`config` -> `telemetry`/`prompts` -> `tools`/`guardrails`/`model_router` -> `agent`) with explicit relative or package-qualified imports, zero circular imports, and zero `sys.path` hacks. Instantiate network/SDK/DB clients lazily (never at module `import` time) so container healthchecks, schema introspection, and unit tests run deterministically offline.




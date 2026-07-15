# Cabral Skills

A collection of AI coding agent skills following the [Agent Skills](https://agentskills.io) open standard. Compatible with [50+ AI coding agents](https://agentskills.io) including Cursor, GitHub Copilot, Cline, Windsurf, Gemini CLI, and more.

This repository is the **single source of truth** for both:

- **Skills** (`skills/`) — standalone, reusable Agent Skills, installable via `npx skills` (see below).
- **Harness plugins** (`plugins/`) — Antigravity harness customization plugins consumed by the [Dynamic Harness Configurator](https://github.com/carlosmscabral/antigravity-dynamic-harness-configuration). Plugins do not vendor their own skills; they reference skills from `skills/` by name and materialize them at promotion time. See [Harness plugins](#harness-plugins).

## Available Skills

| Skill | Description |
|---|---|
| [apigee-x-proxy-development](skills/apigee-x-proxy-development/) | Comprehensive Apigee X API proxy development — 44+ policies, flows, endpoints, fault handling, JavaScript, shared flows, caching patterns, load balancing, WebSocket/SSE, multi-tenant isolation, and more (8,800+ lines of reference documentation) |
| [aws-lambda-to-cloud-run-migration](skills/aws-lambda-to-cloud-run-migration/) | Migrates AWS Lambda functions to Google Cloud Run — analyzes AWS lock-ins (SNS, SQS, SDKs, IAM), build/trigger mechanisms, and service integrations to provide migration reports, containerization guidance, and GCP service mapping |
| [aws-lambda-fleet-to-cloud-run](skills/aws-lambda-fleet-to-cloud-run/) | Fleet-level migration of 10-100+ AWS Lambda functions to Cloud Run — discovery, grouping strategy (1:1 vs consolidation), dependency-graph-based wave sequencing, and consolidated migration program documents |
| [visual-docs](skills/visual-docs/) | Didactic visual documentation — flow, sequence, and state diagrams, ASCII packet/byte walks, and annotated code explanation, with a teaching-first strategy (progressive disclosure, narration, legends) and a deterministic compile-to-validate step so every diagram actually renders |
| [pytest-linter](skills/pytest-linter/) | Runs clean Python styling — Black/Ruff compliance checks and pytest execution on changed Python scripts |
| [sec-auditor](skills/sec-auditor/) | Static security scanning — audits code for shell injections and verifies API credential masking |
| [gcp-iam-troubleshooter](skills/gcp-iam-troubleshooter/) | Advanced diagnostics for complex GCP authorization errors, cross-project lookups, and token impersonations |
| [gcp-network-troubleshooter](skills/gcp-network-troubleshooter/) | Advanced diagnostics for private VPC connectivity, serverless network bridges, and firewall blocks |
| [google-agents-cli-adk-frontend](skills/google-agents-cli-adk-frontend/) | Client-side integration for ADK agents — schemas, parsing pathways, headers, and FastAPI proxy gotchas for connecting frontends to Vertex AI Reasoning Engine / GCP Agent Runtime |

### Vendored skills

These are **third-party skills vendored from [google/agents-cli](https://github.com/google/agents-cli)** (Apache-2.0), pinned to an upstream tag. **Do not hand-edit them** — they are refreshed with `scripts/vendor-agents-cli.sh`. Exact upstream repo/tag/commit are recorded in [`vendored.json`](vendored.json). See [AGENTS.md](AGENTS.md#vendored-skills-googleagents-cli) for the sync process.

| Skill | Description |
|---|---|
| [google-agents-cli-workflow](skills/google-agents-cli-workflow/) | Entrypoint for the ADK development lifecycle — develop, run, debug, test, deploy, publish, and monitor agents, with coding guidelines |
| [google-agents-cli-scaffold](skills/google-agents-cli-scaffold/) | Create/enhance/upgrade ADK agent projects — `agents-cli scaffold` commands, templates, deployment and CI/CD wiring |
| [google-agents-cli-adk-code](skills/google-agents-cli-adk-code/) | ADK Python API patterns — agent types, tool definitions, callbacks, orchestration, and state management |
| [google-agents-cli-eval](skills/google-agents-cli-eval/) | ADK evaluation methodology — eval metrics, dataset schema, LLM-as-judge scoring, and common failure causes |
| [google-agents-cli-deploy](skills/google-agents-cli-deploy/) | Deploy ADK agents to Agent Runtime, Cloud Run, or GKE — workflows, service accounts, secrets, CI/CD, rollback |
| [google-agents-cli-publish](skills/google-agents-cli-publish/) | Publish/register agents with Gemini Enterprise and the Agent Registry via `agents-cli publish` |
| [google-agents-cli-observability](skills/google-agents-cli-observability/) | Monitor deployed ADK agents — Cloud Trace, prompt/response logging, and BigQuery Agent Analytics |

## Installation

### Using [npx skills](https://github.com/vercel-labs/skills) (recommended)

The skills manager automatically detects your agent and installs to the right location.

```bash
# Install all skills from this collection
npx skills add carlosmscabral/cabral-skills

# Install a specific skill
npx skills add carlosmscabral/cabral-skills --skill apigee-x-proxy-development

# Install for a specific agent
npx skills add carlosmscabral/cabral-skills -a cursor
npx skills add carlosmscabral/cabral-skills -a copilot
npx skills add carlosmscabral/cabral-skills -a cline
```

### Manual installation

Copy the desired skill directory from `skills/` into your agent's skill directory:

```bash
git clone https://github.com/carlosmscabral/cabral-skills.git
cp -r cabral-skills/skills/apigee-x-proxy-development /your/agent/skills/directory/
```

## Skill Structure

Each skill follows the [Agent Skills specification](https://agentskills.io/specification):

```
skill-name/
  SKILL.md              # Metadata + instructions (loaded on activation)
  references/           # Detailed reference documentation (loaded on demand)
  examples/             # Optional: runnable code examples
  scripts/              # Optional: executable utility scripts
```

Skills use progressive disclosure: only the name and description are loaded at startup (approx. 100 tokens). The full SKILL.md body loads when the skill activates. Reference files load only when needed during task execution.

## Harness plugins

The `plugins/` directory holds Antigravity **plugins** — capability bundles installed with `agy plugin install`. Each plugin carries only the components Antigravity registers on install: `skills/`, `agents/`, `hooks.json`, `mcp_config.json`, `commands/` (plus `scripts/` referenced by its hooks). It **does not vendor skill bodies** and **does not carry `rules/`** (rules are workspace policy, not a plugin component). Instead, its `plugin.json` declares the skills it uses:

```jsonc
{
  "name": "standard-harness",
  "version": "1.0.0",
  "skills": ["pytest-linter", "visual-docs"]   // names of directories under skills/
}
```

Plugins are consumed by the [Dynamic Harness Configurator (DHC)](https://github.com/carlosmscabral/antigravity-dynamic-harness-configuration), **pinned to a git tag** of this repo. The DHC downloads this repo at the pinned tag once, materializes each selected plugin's declared skills from `skills/` into the plugin bundle, then runs `agy plugin install` — a pure local operation, so it works even under the air-gapped strict-banking posture. (Rules are authored separately by the configurator into the workspace's `.agents/rules/`.)

Consumption is dual and independent:

- **Skills** → `npx skills add carlosmscabral/cabral-skills` (reads `skills/` only; `plugins/` is ignored).
- **Plugins** → the DHC installer (reads `plugins/` + `skills/` at the pinned tag).

Releasing: tag this repo (`vX.Y.Z`); the DHC installer's pinned tag is then bumped in a separate DHC commit. Because plugins and skills share one tag, a skill edit propagates to every plugin that references it on the next release.

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

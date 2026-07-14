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

The `plugins/` directory holds Antigravity harness customization plugins. Each plugin bundles its own harness assets — `rules/`, `hooks.json`, `agents/`, `scripts/`, `mcp_config.json`, `.antigravityignore` — but **does not vendor skill bodies**. Instead, its `plugin.json` declares the skills it uses:

```jsonc
{
  "name": "standard-harness",
  "version": "1.0.0",
  "skills": ["pytest-linter", "visual-docs"]   // names of directories under skills/
}
```

Plugins are consumed by the [Dynamic Harness Configurator (DHC)](https://github.com/carlosmscabral/antigravity-dynamic-harness-configuration), **pinned to a git tag** of this repo. The DHC installer downloads this repo at the pinned tag once, then the configurator agent materializes each promoted plugin's declared skills from `skills/` into the active plugin — a pure local copy, so it works even under the air-gapped strict-banking posture.

Consumption is dual and independent:

- **Skills** → `npx skills add carlosmscabral/cabral-skills` (reads `skills/` only; `plugins/` is ignored).
- **Plugins** → the DHC installer (reads `plugins/` + `skills/` at the pinned tag).

Releasing: tag this repo (`vX.Y.Z`); the DHC installer's pinned tag is then bumped in a separate DHC commit. Because plugins and skills share one tag, a skill edit propagates to every plugin that references it on the next release.

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

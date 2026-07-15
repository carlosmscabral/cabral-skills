# Cabral Skills

My personal collection of AI coding-agent **skills** and **plugins**. Skills follow the
[Agent Skills](https://agentskills.io) open standard (compatible with 50+ agents — Cursor, Copilot,
Cline, Windsurf, Gemini CLI, …); plugins target the Antigravity (`agy`) harness.

Everything here is activated with **native mechanisms** — `npx skills add` for standalone skills,
`agy plugin install` for the plugin — no external orchestrator required.

## Standalone skills (`skills/`)

Self-contained, `npx`-installable skills:

| Skill | Description |
|---|---|
| [apigee-x-proxy-development](skills/apigee-x-proxy-development/) | Comprehensive Apigee X API proxy development — 44+ policies, flows, endpoints, fault handling, JavaScript, shared flows, caching, load balancing, WebSocket/SSE, multi-tenant isolation, and more (8,800+ lines of reference documentation) |
| [aws-lambda-to-cloud-run-migration](skills/aws-lambda-to-cloud-run-migration/) | Migrates a single AWS Lambda function to Google Cloud Run — analyzes AWS lock-ins (SNS, SQS, SDKs, IAM), build/trigger mechanisms, and service integrations into a migration report with containerization and GCP service mapping |
| [aws-lambda-fleet-to-cloud-run](skills/aws-lambda-fleet-to-cloud-run/) | Fleet-level migration of 10–100+ Lambda functions — discovery, grouping (1:1 vs consolidation), dependency-graph wave sequencing, and a consolidated migration program |
| [visual-docs](skills/visual-docs/) | Didactic visual documentation — flow/sequence/state diagrams, ASCII packet walks, annotated code, with a compile-to-validate step so every diagram actually renders |

### Install

```bash
# all four
npx skills add carlosmscabral/cabral-skills

# just one
npx skills add carlosmscabral/cabral-skills --skill apigee-x-proxy-development

# target a specific agent
npx skills add carlosmscabral/cabral-skills -a cursor
```

`npx skills` reads the top-level `skills/` dir only — `plugins/` and `archive/` are ignored.

## The ADK plugin (`plugins/adk-developer/`)

A **self-contained** Antigravity plugin for Google Agent Development Kit work. It blends my own
material with kept-updated upstream skills, all bundled inside the plugin so
`agy plugin install plugins/adk-developer` works directly:

- **Authored:** `google-agents-cli-adk-frontend` skill + `rules/adk-development-guidelines.md`.
- **Vendored (synced from [google/agents-cli](https://github.com/google/agents-cli), Apache-2.0):**
  `google-agents-cli-{workflow,scaffold,adk-code,eval,deploy,publish,observability}` — pinned in
  [`vendored.json`](vendored.json), refreshed via `scripts/vendor-agents-cli.sh`.
- **MCP:** `adk-docs-mcp` (read-only ADK docs), via `mcp_config.json`.

### Develop ADK in a project

Two ways, both work — pick by scope.

**Global (all projects) — remote one-liner.** `agy plugin install` supports a remote repo
**subfolder**, so no local clone is needed:

```bash
agy plugin install https://github.com/carlosmscabral/cabral-skills/tree/main/plugins/adk-developer
# toggle later: agy plugin enable|disable adk-developer
```

This installs the plugin's skills + MCP (and its bundled always-on rule) globally to
`~/.gemini/config/plugins/`. Whether the bundled rule also applies for a *global* install is still
being confirmed (see [ROADMAP.md](ROADMAP.md)); if it doesn't surface, use the rules fallback below.

**Workspace-local (one project) — auto-discovered.** Copy/clone/symlink the plugin into the
project's `.agents/plugins/`; Antigravity auto-discovers `**/.agents/plugins/*/plugin.json` on
interactive startup and loads **all** components (skills, MCP, and the bundled rule), scoped to that
project:

```bash
git clone --depth 1 https://github.com/carlosmscabral/cabral-skills /tmp/cs
mkdir -p .agents/plugins
cp -r /tmp/cs/plugins/adk-developer .agents/plugins/adk-developer
# disable without deleting: rename .agents/plugins/adk-developer/plugin.json -> plugin.json.disabled
```

**Rules fallback** (only if a global install doesn't surface the bundled rule):

```bash
mkdir -p .agents/rules && cp <plugin>/rules/*.md .agents/rules/
```

## External sources

Third-party skills/plugins I use but install fresh from their own upstream (e.g. `obra/superpowers`
for spec-driven development, `google/skills`) are listed with install commands in
**[SOURCES.md](SOURCES.md)**. I point at them rather than vendoring; I only vendor something when I
need to pin or blend it into a plugin.

## Layout

```
skills/            # standalone, npx-installable
plugins/
  adk-developer/   # the one self-contained plugin (skills + rules + MCP bundled)
scripts/           # vendor-agents-cli.sh (syncs the vendored ADK skills)
vendored.json      # provenance/pin for vendored upstreams
SOURCES.md         # external pointers (install commands)
archive/           # retired scaffolding, kept in-tree but inactive (see archive/README.md)
AGENTS.md          # maintainer guide (how to author skills & blend plugins)
```

## License

Apache License 2.0 — see [LICENSE](LICENSE). Vendored third-party skills retain their upstream
licenses; provenance is recorded in [`vendored.json`](vendored.json).

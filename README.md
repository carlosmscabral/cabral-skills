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
| 🚦 [apigee-x-proxy-development](skills/apigee-x-proxy-development/) | Comprehensive Apigee X API proxy development — 44+ policies, flows, endpoints, fault handling, JavaScript, shared flows, caching, load balancing, WebSocket/SSE, multi-tenant isolation, and more (8,800+ lines of reference documentation) |
| ⛵ [aws-lambda-to-cloud-run-migration](skills/aws-lambda-to-cloud-run-migration/) | Migrates a single AWS Lambda function to Google Cloud Run — analyzes AWS lock-ins (SNS, SQS, SDKs, IAM), build/trigger mechanisms, and service integrations into a migration report with containerization and GCP service mapping |
| 🚢 [aws-lambda-fleet-to-cloud-run](skills/aws-lambda-fleet-to-cloud-run/) | Fleet-level migration of 10–100+ Lambda functions — discovery, grouping (1:1 vs consolidation), dependency-graph wave sequencing, and a consolidated migration program |
| 🎓 [visual-docs](skills/visual-docs/) | Didactic Markdown visual explanations — flow/sequence/state/ERD Mermaid diagrams, ASCII packet & byte walks, and annotated code walkthroughs, with an offline zero-dependency Mermaid validator (`validate-diagrams.sh`) |
| 📽️ [preso-builder](skills/preso-builder/) | Spec-first Google Slides builder in clean **Google Cloud Zen Editorial** style (`#FFFFFF` / `#F8F9FA` / `#202124` charcoal / `#1A73E8` blue canvases, top mini 4-color bar, adaptive *Ma* negative space, `Google Sans` Regular hierarchy, `ROUND_RECTANGLE` cards) — ingests codebases, markdown, or decks; **18 archetypes** incl. editorial covers, blue/dark statement pivots, capability heat-matrices with dashed co-build overlays, KPI spotlights, horizon staircases, dark closing asks, `2×2`/`2×3` executive grids, architecture walkthrough callouts (`image_split`), native editable diagrams (`cycle` / `timeline` / `funnel` / `layered_cake` / `swimlanes`), and workstream cards; blank-deck default; duration tiers (5/15/45 min); geometry-aware fit checks and a render-audit loop on real thumbnails. Bundles its Python engine in `engine/` |

### Install

```bash
# all skills
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

- **Authored:** `google-agents-cli-adk-frontend` and `google-agents-cli-adk-auth` skills + `rules/adk-development-guidelines.md`.
- **Vendored (synced from [google/agents-cli](https://github.com/google/agents-cli), Apache-2.0):**
  `google-agents-cli-{workflow,scaffold,adk-code,eval,deploy,publish,observability}` — pinned in
  [`vendored.json`](vendored.json), refreshed via `scripts/vendor-agents-cli.sh`.
- **MCP:** `adk-docs-mcp` (read-only ADK docs), via `mcp_config.json`.

### `architecture-walkthrough` plugin

One vendored skill, [`cloud-architecture-diagram`](plugins/architecture-walkthrough/skills/cloud-architecture-diagram/),
synced from [duboc/agy-skills](https://github.com/duboc/agy-skills) (Apache-2.0). The skill builds one
offline `.html` file: hand-placed Google Cloud product cards, hover explanations, and a stepped slideshow
of the request flow. A local patch narrows the trigger to **HTML walkthroughs**. Editable architecture
diagrams stay with Dendrite, and Mermaid/ASCII docs stay with `visual-docs`. The pin is a commit SHA in
[`vendored.json`](vendored.json), refreshed via `scripts/vendor-agy-skills.sh`.

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
  adk-developer/   # ADK plugin (skills + rules + MCP bundled)
  architecture-walkthrough/  # vendored HTML architecture walkthrough skill
scripts/           # vendor-*.sh (sync the vendored skills) + patches/ (local deltas)
vendored.json      # provenance/pin for vendored upstreams
SOURCES.md         # external pointers (install commands)
archive/           # retired scaffolding, kept in-tree but inactive (see archive/README.md)
AGENTS.md          # maintainer guide (how to author skills & blend plugins)
```

## License

Apache License 2.0 — see [LICENSE](LICENSE). Vendored third-party skills retain their upstream
licenses; provenance is recorded in [`vendored.json`](vendored.json).

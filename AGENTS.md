# AGENTS.md — cabral-skills maintainer guide

How to work on **this repository**. Canonical contributor guide; `CLAUDE.md` symlinks to it.

## What this repo is

My personal source of truth for two artifact kinds, both activated with **native mechanisms**
(no external orchestrator):

- **Skills** (`skills/<name>/`) — standalone, `npx`-installable [Agent Skills](https://agentskills.io). Self-contained.
- **Plugins** (`plugins/<name>/`) — **self-contained** Antigravity plugins installed with
  `agy plugin install`. A plugin bundles everything it needs *inside its own dir*: `skills/`,
  optional `agents/`, `hooks.json`, `mcp_config.json`, `commands/`, `scripts/`, `rules/`, and a
  `plugin.json`.

There is one real plugin today — `adk-developer`. Retired scaffolding lives in `archive/`
(in-tree, inactive; see `archive/README.md`).

## Working on a skill

When you **add or change** a standalone skill under `skills/<name>/`:

1. Keep the standard layout: `SKILL.md` (with `name` + `description` frontmatter) at the root,
   plus optional `references/`, `examples/`, `scripts/`.
2. If it ships scripts, make them executable (`chmod +x`) and document how to run them in `SKILL.md`.
3. **Update the README skills table.**
4. Run the [validation checklist](#validation-checklist) before tagging.

## Authoring a plugin (the blend recipe)

This is the reusable process — the pattern for any future plugin (e.g. an Apigee plugin), not just
`adk-developer`. **A plugin is a self-contained directory** that `agy plugin install <dir>` can
consume directly. Blend = *your* authored material + *upstream* material kept updated, all bundled:

```
plugins/<name>/
  plugin.json          # name, version, description, skills[] (manifest of bundled skills)
  skills/              # BOTH authored and vendored skill bodies live here
    <my-authored-skill>/
    <vendored-upstream-skill>/
  rules/*.md           # authored rules (see "Rules" — installer ignores these; copied per project)
  mcp_config.json      # optional: MCP servers
  hooks.json           # optional: hooks (reference scripts by ABSOLUTE path — relative CWD fails)
  agents/ commands/    # optional
```

### Authored parts
Write your own skills/rules directly under the plugin. They are the source of truth — edit in place.

### Vendored parts (kept updated)
To blend in an external upstream you want to track:

1. Add a **per-plugin sync script** under `scripts/` (model it on `scripts/vendor-agents-cli.sh`):
   download the upstream at a **pinned tag**, copy the chosen skill dirs into
   `plugins/<name>/skills/`, and write provenance (repo/tag/commit/license/skills) into
   `vendored.json`.
2. Add the upstream to the drift workflow matrix
   (`.github/workflows/check-vendored-upstreams.yml`) so a newer release opens a tracking issue.
   It **never auto-syncs** — syncing stays deliberate and pinned.
3. **Never hand-edit vendored skill dirs** — edits are lost on the next sync. Fix upstream (or
   fork and point the sync at your fork).

> When to vendor vs point: if you just *use* an external plugin/skill as-is, **point** at it in
> [`SOURCES.md`](SOURCES.md) and `agy plugin install`/`npx skills add` it from upstream. Vendor
> only when you need to **pin** it or **blend** it into a plugin alongside your own material.

### Rules are a bundled plugin component
Per the Antigravity plugin schema, `rules/*.md` are a first-class bundled component (always-on,
Priority 0). When a plugin is discovered as a **workspace-local** plugin under
`.agents/plugins/<name>/`, its rules load automatically along with skills/agents/hooks/MCP. So
author rules under `plugins/<name>/rules/` — they travel with the plugin; no manual copy needed for
the workspace-local path.

**Open caveat (see [ROADMAP.md](ROADMAP.md)):** whether a **globally**-installed plugin
(`agy plugin install`) also surfaces its bundled rules is still being verified. Until confirmed, if
a global install doesn't apply the rule, copy it into the project as a fallback:

```bash
mkdir -p .agents/rules && cp /path/to/plugins/<name>/rules/*.md .agents/rules/
```

(Optionally ship a tiny `apply-rules.sh` in the plugin for that fallback.)

### plugin.json
Carry `name`, `version`, `description`, and a `skills[]` array listing the bundled skill dir names
(a manifest of what's inside `skills/`). Bump `version` on every change.

## Vendored upstreams

Tracked in [`vendored.json`](vendored.json); a scheduled Action
(`.github/workflows/check-vendored-upstreams.yml`) watches each and files an issue on a newer
release (never auto-syncs).

### google/agents-cli → `plugins/adk-developer/skills/`

The `google-agents-cli-{workflow,scaffold,adk-code,eval,deploy,publish,observability}` skills are
vendored from [google/agents-cli](https://github.com/google/agents-cli) (Apache-2.0), pinned to an
upstream tag. (`google-agents-cli-adk-frontend` and `google-agents-cli-adk-auth` in the same dir are **authored** — not vendored,
safe to edit.)

**To sync to a newer upstream release:**

```bash
scripts/vendor-agents-cli.sh <upstream-tag>   # e.g. v1.2.0
```

This downloads the tag, replaces the seven vendored dirs under `plugins/adk-developer/skills/`, and
rewrites `vendored.json`. Then: review the diff, update the README if descriptions changed, run the
[validation checklist](#validation-checklist), and cut a new release tag (a sync is at least a
**minor** bump).

## Consuming this repo

- **A standalone skill:** `npx skills add carlosmscabral/cabral-skills --skill <name>` (or omit
  `--skill` for all four). Reads `skills/` only.
- **The ADK plugin:** global via a remote **subfolder** URL
  (`agy plugin install https://github.com/carlosmscabral/cabral-skills/tree/main/plugins/adk-developer`)
  or workspace-local by copying/symlinking it into `.agents/plugins/` (auto-discovered). See README
  "Develop ADK in a project"; note the rules caveat above.
- **External stuff:** see [SOURCES.md](SOURCES.md).

## Releasing

1. Land changes on `main` with the README updated.
2. Run the [validation checklist](#validation-checklist).
3. Cut a semver tag and push:
   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z: <what changed>"
   git push origin main vX.Y.Z
   ```
   - **patch** — content fix within a skill/plugin.
   - **minor** — new skill/plugin/capability, or a vendored-upstream sync.
   - **major** — a breaking layout change (removed/relocated skills or plugins).

## Validation checklist

Run the repository validation CLI to verify manifest parity, frontmatter, script permissions, workspace hygiene, link integrity, vendor digests, and trigger overlaps:

```bash
python3 scripts/validate_repo.py
```

To auto-repair fixable issues (such as script permissions, vendor digests, or `__pycache` artifacts):

```bash
python3 scripts/validate_repo.py --fix
```

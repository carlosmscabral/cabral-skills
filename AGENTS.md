# AGENTS.md — cabral-skills maintainer guide

This file tells an AI agent (or a human) how to work on **this repository**. It is the
canonical contributor guide; `CLAUDE.md` is a symlink to it.

## What this repo is

`cabral-skills` is the **single source of truth** for two kinds of artifact:

- **Skills** (`skills/<name>/`) — standalone, reusable [Agent Skills](https://agentskills.io). Each is self-contained.
- **Plugins** (`plugins/<name>/`) — Antigravity plugins, i.e. **capability bundles** installed with `agy plugin install`. A plugin carries only the components Antigravity registers on install: `skills/`, `agents/`, `hooks.json`, `mcp_config.json` (`mcpServers`), `commands/` — plus `scripts/` referenced by its hooks, and a `plugin.json` that **references** skills by name. Plugins **do not** contain skill bodies, and **do not** carry `rules/` (rules are workspace policy, not a plugin component — see below).

This repo is **consumer-agnostic and standalone**. It does not depend on, and does not need
to know about, any particular consumer. Skills and plugins can be installed by hand (see
[Consuming](#consuming-this-repo)), by `npx skills`, or by any downstream tool. One such
downstream tool is the [Dynamic Harness Configurator (DHC)](https://github.com/carlosmscabral/antigravity-dynamic-harness-configuration),
but that is just an example — our only obligation to any consumer is a clean tagged release.

## The one rule that ties skills and plugins together

**A plugin never vendors skill bodies.** It lists skill *names* in `plugin.json`:

```jsonc
{ "name": "standard-harness", "version": "1.0.0", "skills": ["pytest-linter", "visual-docs"] }
```

Every string in a `skills` array **must** match a directory under `skills/`. There must be
no `skills/` subdirectory inside `plugins/<name>/` in this repo — skill bodies live only in
top-level `skills/` and are copied into a plugin by the consumer at install/promotion time.

## Working on a skill

When you **add or change** a skill:

1. Edit under `skills/<name>/`. Keep the standard layout: `SKILL.md` (with `name` +
   `description` frontmatter) at the root, plus optional `references/`, `examples/`,
   `scripts/`. See the README "Skill Structure" section.
2. If the skill ships scripts, make sure they are executable (`chmod +x`) and that the
   `SKILL.md` explains how to run them.
3. **Update the README skills table** (`README.md`) — add/adjust the row for this skill.
4. A skill edit is picked up by every plugin that references it, automatically, on the next
   release. You do **not** edit plugins to propagate a skill change.
5. If you **rename or delete** a skill, grep every `plugins/*/plugin.json` for the old name
   and fix the `skills` arrays, or a consumer's materialization step will warn on a missing
   skill. Run the [validation check](#validation-checklist).

## Working on a plugin

A plugin is exactly what `agy plugin install` registers. Its components (confirmed by
`agy plugin validate <dir>`) are: **skills, agents, hooks, mcpServers, commands**. That's the
whole surface — anything else in the dir is ignored by the installer.

When you **add or change** a plugin:

1. Edit under `plugins/<name>/`. Its `hooks.json`, `agents/`, `scripts/`, `mcp_config.json`
   stay **inside the plugin** — they are plugin-specific and not shared.
2. `hooks.json` references scripts by the workspace-relative path
   `.agents/plugins/<name>/scripts/...`. Keep scripts in the plugin's `scripts/` dir so those
   paths resolve wherever the plugin is installed.
3. To give a plugin a skill, add the skill's name to `plugin.json` `skills[]` — do **not**
   copy the skill into the plugin. If the skill doesn't exist yet, author it under `skills/`
   first (see above).
4. Every `plugin.json` should carry `name`, `version`, and (if it uses any) `skills`.
5. **Update the README** — the "Harness plugins" section and, if the plugin surfaces a new
   skill, the skills table.
6. **No `rules/` in plugins.** Rules (`trigger: always_on` / `file_match(...)` markdown) are
   **not** an `agy plugin install` component — Antigravity loads them only from a workspace
   `.agents/rules/` dir. They are *workspace policy*, not portable capability, so they don't
   belong in a reusable plugin. If a behavior feels like a rule, express it as a **skill**
   (model-invoked guidance) or a **hook** (hard enforcement); leave genuine project policy for
   the consumer to author into `.agents/rules/` (the DHC configurator does this from its
   interview).
7. **Shared non-skill assets:** if an agent/hook ever needs to be shared across plugins, do
   **not** duplicate it — introduce a top-level `shared/` pool and reference it, mirroring how
   skills work. (Not needed today; there is currently no cross-plugin duplication.)

## Vendored skills (google/agents-cli)

The `google-agents-cli-*` skills (except `google-agents-cli-adk-frontend`, which is authored
here) are **third-party, vendored from [google/agents-cli](https://github.com/google/agents-cli)**
(Apache-2.0), pinned to an upstream tag. They are redistributed as normal top-level skills so
they are `npx`-installable and referenceable by the `adk-developer` plugin.

**Rules for vendored skills:**

- **Never hand-edit** `skills/google-agents-cli-{workflow,scaffold,adk-code,eval,deploy,publish,observability}/`.
  Local edits are lost on the next sync. Fix bugs upstream, or (if urgent) fork upstream and
  point the sync at your fork.
- The exact upstream `repo` / `tag` / `commit` / `license` is recorded in [`vendored.json`](vendored.json).
- Provenance/attribution for Apache-2.0 is carried by `vendored.json`; keep it accurate.

**To sync to a newer upstream release:**

```bash
scripts/vendor-agents-cli.sh <upstream-tag>   # e.g. v1.2.0
```

This downloads `google/agents-cli` at that tag, replaces the vendored skill dirs, and rewrites
`vendored.json`. Then: review the diff, update the README if descriptions changed, run the
[validation checklist](#validation-checklist), and cut a new cabral-skills release tag (a sync
is at least a **minor** bump). A scheduled GitHub Action
(`.github/workflows/check-agents-cli-upstream.yml`) watches upstream and opens an issue when a
newer release exists — that is your signal to run the sync; it never syncs automatically
(determinism is the point).

## Releasing (the contract with all consumers)

Consumers pin a **git tag** of this repo; that tag is the entire public contract. So:

1. Land your skill/plugin changes on `main` with the README updated.
2. Run the [validation checklist](#validation-checklist).
3. Cut a semver tag and push it:
   ```bash
   git tag -a vX.Y.Z -m "vX.Y.Z: <what changed>"
   git push origin main vX.Y.Z
   ```
   - **patch** — content fix within a skill/plugin.
   - **minor** — new skill or plugin, or a new capability.
   - **major** — a breaking change to the layout or the `plugin.json` schema (e.g. renaming
     the `skills` field), which would break a consumer's materialization logic.
4. That's where this repo's responsibility **ends**. Downstream consumers adopt the new tag
   on their own side and on their own schedule. For the DHC harness specifically, the "bump
   the pinned tag" procedure lives in that repo's `AGENTS.md` — intentionally not here, so
   this repo stays consumer-agnostic. If you maintain both, cut the tag here first, then go
   bump DHC (its installer 404s on a tag that doesn't exist yet).

## Consuming this repo

You never need DHC to use anything here.

- **A skill, via the skills manager:** `npx skills add carlosmscabral/cabral-skills --skill <name>`
  (or omit `--skill` for all). Reads `skills/` only; `plugins/` is ignored.
- **A skill, by hand:** `cp -r skills/<name>/ /your/agent/skills/dir/`.
- **A plugin, by hand:** plugins install with Antigravity's native plugin manager. Because
  plugins don't vendor skill bodies, first materialize the referenced skills into a staging
  copy of the plugin, then install it:
  1. copy the plugin to a staging dir, then for each entry in its `plugin.json` `skills[]`:
     `cp -r skills/<skill>/ <staging>/<name>/skills/<skill>/`
  2. `agy plugin install <staging>/<name>` (registers skills/agents/hooks/mcpServers/commands),
     then `agy plugin enable <name>`. Verify with `agy plugin list`.
  3. Plugins do **not** carry rules — if you want project rules, author them into your
     workspace `.agents/rules/` yourself. (This is exactly what the DHC configurator automates.)

## Validation checklist

Before tagging, confirm every `plugin.json` is valid and every referenced skill exists:

```bash
python3 - <<'PY'
import json, glob, os, sys
bad = 0
for pj in glob.glob("plugins/*/plugin.json"):
    m = json.load(open(pj))
    for s in m.get("skills", []):
        if not os.path.isdir(f"skills/{s}"):
            print(f"MISSING: {pj} references skills/{s}"); bad += 1
    if os.path.isdir(os.path.join(os.path.dirname(pj), "skills")):
        print(f"VENDORED: {pj} has a skills/ subdir — skills must live in top-level skills/"); bad += 1
for sk in glob.glob("skills/*/SKILL.md"):
    head = open(sk).read(400)
    if "name:" not in head or "description:" not in head:
        print(f"FRONTMATTER: {sk} missing name/description"); bad += 1
print("OK" if not bad else f"{bad} problem(s)"); sys.exit(1 if bad else 0)
PY
```

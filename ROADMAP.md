# ROADMAP — understanding Antigravity (`agy`) plugin behavior

Open questions to resolve so we can author local-repo plugins with confidence. The goal is a solid,
**verified** mental model of how `agy` discovers, installs, and enforces plugin components — not
guesses. Each item lists what we currently believe, how to verify it, and why it matters.

> Ground rule: verify against the real `agy` CLI (its `--help`, actual runs, and the on-disk result)
> or official Antigravity docs. Do not treat community blogs — or our own assumptions — as settled.

## 1. Install location: global vs. local

- **Believe:** `agy plugin install <path>` installs **globally** to `~/.gemini/jetski/plugins/`
  (available to all projects), not into a project-local `.agents/`. (Seen in earlier live testing.)
- **Verify:** after an install, inspect `~/.gemini/jetski/plugins/` and run `agy plugin list` from a
  *different* project dir; confirm the plugin still shows.
- **Open:** Is there any way to install a plugin **project-locally** (scoped to one workspace)? Does
  dropping a plugin under `.agents/plugins/<name>/` (workspace auto-discovery) differ from
  `agy plugin install`, and does that difference persist in headless `agy -p` runs?
- **Why it matters:** decides whether a per-project ADK setup is "install once, global" or something
  we re-do per repo.

## 2. Remote installs from a git URL — and monorepo subfolders

- **Believe:** `agy plugin install https://github.com/obra/superpowers` works because that repo's
  **root is the plugin** (`plugin.json` at top level).
- **Open (key):** Does `agy plugin install` support a **subdirectory of a remote repo** (our case:
  `cabral-skills/plugins/adk-developer/`)? Is there an `owner/repo/path`, `#subdir`, or `--subdir`
  form? Check `agy plugin install --help`.
- **Decision it drives:** if no subdir support, either (a) keep a local clone and install from the
  path, or (b) give the ADK plugin **its own repo** so its root is the plugin and the remote
  one-liner works like superpowers.
- **Why it matters:** determines whether our monorepo can serve installable plugins directly, or
  whether "installable plugin" implies "dedicated repo."

## 3. Rule enforcement — do plugin `rules/` ever load?

- **Believe:** `agy plugin install` registers skills/agents/hooks/MCP/commands but **NOT** `rules/`;
  rules load only from a workspace `.agents/rules/` (hence our per-project copy step).
- **Verify:** install the ADK plugin *without* copying rules, start `agy`, and check whether
  `adk-development-guidelines` is active (e.g. it references its own presence). Then copy into
  `.agents/rules/` and re-check.
- **Open:** Do global rule locations exist (`~/.gemini/config/…`)? Does `trigger: always_on` vs.
  `file_match(...)` change load behavior? Is enforcement different interactive vs. headless (`-p`)?
- **Why it matters:** confirms the "rules ship in the plugin as source, copied per project" recipe is
  actually necessary, and whether a global rules dir could remove the copy step.

## 4. Discovery: interactive vs. headless (`agy -p`)

- **Believe (earlier testing):** interactive `agy` auto-discovers `.agents/plugins/*/`; headless
  `agy -p` **skips the plugin tree** but still loads direct scope (`.agents/rules/*.md`,
  `.agents/skills/*`, `.agents/hooks.json`) + global (`~/.gemini/config/*`).
- **Verify:** run the same task interactively and with `-p`; diff which skills/rules/hooks are active.
- **Why it matters:** if headless drops plugins, any CI/automation using our plugin needs the
  components materialized into direct scope, not just installed.

## 5. Multiple plugins, precedence, and conflicts

- **Open:** With several plugins installed, do same-named skills/hooks collide? Load order /
  precedence? Does `agy plugin enable/disable` toggle cleanly? What does `agy plugin list` report
  (versions, source, enabled state)?
- **Why it matters:** as we add more local plugins (Apigee, etc.), we need to know they compose
  without silent shadowing.

## 6. Update / reinstall semantics

- **Open:** After we sync vendored skills and re-release, does `agy plugin install <same source>`
  **replace** the global copy cleanly (old skills removed, not merged)? Is there an `update`
  subcommand? Does version in `plugin.json` gate anything?
- **Why it matters:** our agents-cli sync flow (see AGENTS.md) assumes reinstall = clean refresh.

## 7. Hooks: paths and triggering

- **Believe:** hook commands must use **absolute** paths (relative CWD failed with exit 127
  earlier). Global vs. local install may change what the "plugin dir" resolves to.
- **Open:** For a globally-installed plugin, what is the working directory / base path hooks resolve
  against? How do we confirm a hook actually fired (where are the logs)?
- **Why it matters:** any future plugin that ships hooks needs reliable path + observability.

## Deliverable

Once 1–4 are verified, write the confirmed model into `AGENTS.md` (replacing "believe" language
with facts) so the blend-plugin recipe rests on tested behavior. Items 5–7 can follow as we build
the next local plugin.

---
_Scope: cabral-skills local plugins. The DHC repo is frozen/out of scope._

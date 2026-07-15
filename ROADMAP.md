# ROADMAP — understanding Antigravity (`agy`) plugin behavior

Working model of how `agy` discovers, installs, and enforces plugin components. The **Confirmed
model** below now comes from official Antigravity plugin docs; the **Still open** items still need
verification against the real CLI.

> Ground rule: verify against the real `agy` CLI (its `--help`, actual runs, and the on-disk result)
> or official docs. Don't treat community blogs — or our own assumptions — as settled.

## Confirmed model (Antigravity plugin docs, 2026-07)

### Plugin bundle schema
`.agents/plugins/<name>/` contains: `plugin.json` (required marker) + `rules/*.md`
(**always-on, Priority 0**) + `skills/<name>/SKILL.md` + `agents/*.md` + `hooks.json` +
`mcp_config.json`. → **Rules ARE a first-class bundled plugin component** — this corrects our
earlier "plugins don't/shouldn't carry rules" assumption.

### Install scope (CLI is always global)
- `agy plugin install` / `link` / `import` write **exclusively** to the global config dir
  **`~/.gemini/config/plugins/`**. There is no flag to install into a workspace `.agents/`.
  (Path correction: docs say `config/plugins`, not the `jetski/plugins` we'd noted from memory.)
- `agy plugin enable <name>` / `disable <name>` operate **only** on global plugins — they physically
  rename `plugin.json` ⇄ `plugin.json.disabled` in the global dir. Run against a workspace-local
  plugin they fail with "plugin not found."

### Two ways to make a plugin active
1. **Global (all projects):** `agy plugin install <zip | dir | git-url>` → `~/.gemini/config/plugins/`.
2. **Workspace-local (one project):** manually copy / clone / **symlink** into
   `.agents/plugins/<name>/`. Zero-registry **auto-discovery** on interactive TUI startup via glob
   `**/.agents/plugins/*/plugin.json`. Disable by renaming that `plugin.json` → `plugin.json.disabled`.

### Remote subfolder install — SUPPORTED ✅
`agy plugin install https://github.com/owner/repo/tree/branch/plugins/my-plugin` clones the repo,
navigates to the subpath, and stages **only that subfolder** for global install. → **Our monorepo
can serve the ADK plugin directly; no dedicated repo needed.** For us:
```bash
agy plugin install https://github.com/carlosmscabral/cabral-skills/tree/main/plugins/adk-developer
```

### Rules loading
Bundled plugin rules are supported (always-on, Priority 0). For a **workspace-local** plugin under
`.agents/plugins/`, auto-discovery loads its rules along with skills/agents/hooks/MCP. Standalone
workspace `.agents/rules/*.md` files are also supported.

## Still open / to verify

1. **[Rules × global install] — the key one for our ADK setup.** Does a **globally**-installed
   plugin's bundled `rules/` load, or do only workspace-local (`.agents/plugins/`) plugin rules
   activate? Our earlier observation suggested global plugin rules didn't apply; the docs list rules
   as a bundled component but describe auto-discovery specifically for `.agents/plugins/`.
   **Verify:** global-install the ADK plugin, do *not* copy rules, start `agy`, check whether
   `adk-development-guidelines` is active. Result decides whether the per-project rules copy is still
   needed for the global path.
2. **[Headless `agy -p`]** Does `-p` load global plugins and/or workspace `.agents/plugins/`?
   Earlier we saw `-p` skip the plugin tree — re-verify against the current build.
3. **[Precedence]** With multiple plugins: same-named skills/hooks collisions and load order; how do
   multiple always-on (Priority 0) rules order relative to each other and to `.agents/rules/`?
4. **[Update semantics]** Does re-`install` from the same source cleanly replace the global copy
   (old vendored skills removed, not merged)? How do `link` / `import` differ from `install`?
5. **[Hooks base path]** For a global plugin, what working dir / base path do hook commands resolve
   against? Is an absolute path still required (relative failed with exit 127 earlier)? Where do we
   see that a hook fired?

## Implications for our repo (act on once confirmed)

- **README:** add the remote-subfolder one-liner and the workspace-local symlink option (done).
- **Rules copy step:** keep as a *fallback* until open item #1 is settled. Workspace-local placement
  loads rules for sure; the global path is TBD.
- Offer users a clear choice: global remote install (all projects) vs. workspace-local symlink
  (one project, rules definitely load, easy per-project disable).

---
_Scope: cabral-skills local plugins. The DHC repo is frozen/out of scope._

# archive/

Retired material kept **in-tree** for reference — **not active, not installed, not maintained**.
Nothing here is picked up by `npx skills add` (which reads top-level `skills/`) or by
`agy plugin install` (which you point at `plugins/<name>/`). Treat it as read-only history you can
still browse without digging through git.

## What's here and why

### `plugins/` — DHC scaffolding plugins
`standard-harness`, `strict-banking-harness`, `gcp-troubleshooter` were built to validate the
**Dynamic Harness Configurator (DHC)** flow, not for real use. The DHC is stopped/frozen (pinned
to cabral-skills `v1.0.x`–`v1.3.0`); these plugins stay only as examples of the plugin shape
(rules/hooks/agents/scripts).

### `skills/` — scaffolding skills
`pytest-linter`, `sec-auditor`, `gcp-iam-troubleshooter`, `gcp-network-troubleshooter` were thin
stubs created to exercise the DHC, superseded by the personal setup.

### `superpowers/` + `vendor-superpowers.sh` — the old full vendoring of obra/superpowers
We briefly vendored the whole `obra/superpowers` methodology here (pinned at **v6.1.1**, commit
`c984ea2e7aeffdcc865784fd6c5e3ab75da0209a`, MIT). The personal model instead treats superpowers
as an **external pointer** — install it fresh from upstream (`agy plugin install obra/superpowers`).
See `SOURCES.md` at the repo root. This vendored copy is kept only as a snapshot.

## If you ever want one back
Move the directory back out of `archive/` (e.g. `git mv archive/plugins/<name> plugins/<name>`)
and, for a plugin, make it self-contained per the "authoring a plugin" recipe in `AGENTS.md`.

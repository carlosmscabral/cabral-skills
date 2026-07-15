#!/bin/bash
# standard-harness: post-edit lint/format hook.
#
# Fires on postToolUse after a file-editing tool (write_to_file / replace_file_content /
# multi_replace_file_content). Formats ONLY the just-edited file ($TargetFile) with whatever
# tools are installed locally; missing tools are skipped silently (no network installs).
#
# Non-blocking by design: always exits 0 so the agent can read any stdout feedback and keep
# going. It does NOT gate command execution (that is a security concern; see strict-banking).

# Observability via agy's OWN hook logs (not a growing file): one line to stderr, which
# agy captures (command_hook_executor). Confirms the hook fired and shows the TargetFile
# value it received (reveals if the runtime doesn't populate $TargetFile).
echo "[standard-harness] post-edit hook fired; TargetFile='${TargetFile:-<unset>}'" >&2

f="${TargetFile:-}"
[ -n "$f" ] && [ -f "$f" ] || exit 0

did=""
case "$f" in
  *.py)
    if command -v ruff >/dev/null 2>&1; then
      ruff check --fix -q "$f" 2>/dev/null
      ruff format -q "$f" 2>/dev/null
      did="ruff"
    elif command -v black >/dev/null 2>&1; then
      black -q "$f" 2>/dev/null
      did="black"
    fi
    ;;
  *.js|*.jsx|*.ts|*.tsx|*.mjs|*.cjs|*.json|*.css|*.md)
    if command -v prettier >/dev/null 2>&1; then
      prettier --write --log-level warn "$f" >/dev/null 2>&1 && did="prettier"
    elif command -v npx >/dev/null 2>&1; then
      # --no-install: use a locally-installed prettier only; never fetch from the network
      npx --no-install prettier --write --log-level warn "$f" >/dev/null 2>&1 && did="prettier"
    fi
    ;;
esac

[ -n "$did" ] && echo "[standard-harness] formatted $f ($did)"
exit 0

#!/usr/bin/env bash
# Deterministically validate Mermaid diagrams in Markdown by COMPILING them.
# A diagram either parses or it doesn't — no eyeballing.
#
# Usage:  validate-diagrams.sh <file.md | dir> [more ...]
# Backends (auto): local `mmdc` > `npx @mermaid-js/mermaid-cli` > Kroki HTTP.
#   - Kroki uses $KROKI_URL (default https://kroki.io); self-host for private repos.
# Exit 0 = all diagrams compiled; 1 = at least one failed / no backend available.
set -uo pipefail

KROKI_URL="${KROKI_URL:-https://kroki.io}"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# Backend: override with VD_BACKEND=mmdc|npx|kroki, else auto-detect.
backend="${VD_BACKEND:-}"
if [ -z "$backend" ]; then
  if command -v mmdc >/dev/null 2>&1; then backend="mmdc"
  elif command -v npx >/dev/null 2>&1; then backend="npx"
  elif command -v curl >/dev/null 2>&1; then backend="kroki"
  fi
fi
if [ -z "$backend" ]; then
  echo "no validation backend (need mmdc, npx, or curl+network for Kroki)"; exit 1
fi
echo "backend: $backend"

kroki_compile() { # $1 = .mmd -> 0 ok / 1 fail
  command -v curl >/dev/null 2>&1 || return 1
  local code
  code=$(curl -s -o "$TMP/err" -w '%{http_code}' --max-time 30 -X POST "$KROKI_URL/mermaid/svg" \
         --data-binary @"$1" -H 'Content-Type: text/plain') && [ "$code" = "200" ]
}

compile() { # $1 = .mmd file -> 0 ok / 1 fail (stderr in $TMP/err)
  case "$backend" in
    mmdc) mmdc -i "$1" -o "$TMP/out.svg" >/dev/null 2>"$TMP/err" && return 0 ;;
    npx)  npx -p @mermaid-js/mermaid-cli mmdc -i "$1" -o "$TMP/out.svg" >/dev/null 2>"$TMP/err" && return 0 ;;
    kroki) kroki_compile "$1"; return $? ;;
  esac
  # Browser backend failed (e.g. missing Chromium libs). Latch to Kroki and retry.
  if [ "$backend" != "kroki" ] && command -v curl >/dev/null 2>&1; then
    echo "note: $backend backend failed to run; falling back to Kroki for the rest" >&2
    backend="kroki"
    kroki_compile "$1"; return $?
  fi
  return 1
}

fails=0; total=0
check_file() {
  local md="$1" i=0
  awk -v dir="$TMP" '
    /^```+[ ]*mermaid[ ]*$/ {inb=1; i++; fn=dir"/blk_"i".mmd"; next}
    inb && /^```/ {inb=0; next}
    inb {print > fn}
  ' "$md"
  for f in "$TMP"/blk_*.mmd; do
    [ -e "$f" ] || continue
    total=$((total+1))
    if compile "$f"; then
      echo "  OK    $md  (block $(basename "$f" .mmd | tr -d 'blk_'))"
    else
      echo "  FAIL  $md  (block $(basename "$f" .mmd | tr -d 'blk_')):"
      sed 's/^/        /' "$TMP/err" | head -6
      fails=$((fails+1))
    fi
  done
  rm -f "$TMP"/blk_*.mmd
}

for arg in "$@"; do
  if [ -d "$arg" ]; then
    while IFS= read -r md; do check_file "$md"; done < <(find "$arg" -type f -name '*.md')
  elif [ -f "$arg" ]; then
    check_file "$arg"
  fi
done

echo "----"
echo "diagrams: $total   failed: $fails"
[ "$fails" -eq 0 ]

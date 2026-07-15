#!/usr/bin/env bash
# Vendor the Google agents-cli skills into cabral-skills at a PINNED upstream tag.
#
# Upstream: https://github.com/google/agents-cli  (Apache-2.0)
# These skills are THIRD-PARTY and vendored — do not hand-edit skills/google-agents-cli-*;
# re-run this script against a newer tag to update, then review the diff and re-tag/release.
#
# Usage:
#   scripts/vendor-agents-cli.sh <tag>        # e.g. scripts/vendor-agents-cli.sh v1.1.0
#
# Requires: curl, unzip, python3. Uses `gh` to record the exact commit if available.

set -euo pipefail

REPO="google/agents-cli"
LICENSE="Apache-2.0"
TAG="${1:-}"
if [ -z "$TAG" ]; then
  echo "usage: $0 <upstream-tag>   (e.g. v1.1.0)" >&2
  exit 2
fi

# The exact set of upstream skills we redistribute.
SKILLS=(
  google-agents-cli-adk-code
  google-agents-cli-deploy
  google-agents-cli-eval
  google-agents-cli-observability
  google-agents-cli-publish
  google-agents-cli-scaffold
  google-agents-cli-workflow
)

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "[vendor] Downloading ${REPO}@${TAG} ..."
curl -fsSL -o "$TMP/src.zip" "https://github.com/${REPO}/archive/refs/tags/${TAG}.zip"
unzip -q -o "$TMP/src.zip" -d "$TMP"
SRC="$(find "$TMP" -maxdepth 1 -type d -name 'agents-cli-*' | head -n1)"
if [ -z "$SRC" ] || [ ! -d "$SRC/skills" ]; then
  echo "[vendor] ERROR: ${REPO}@${TAG} has no skills/ directory." >&2
  exit 1
fi

echo "[vendor] Copying ${#SKILLS[@]} skills into skills/ ..."
for s in "${SKILLS[@]}"; do
  if [ ! -d "$SRC/skills/$s" ]; then
    echo "[vendor] ERROR: upstream skill '$s' not found at ${TAG}." >&2
    exit 1
  fi
  rm -rf "${ROOT:?}/skills/$s"
  cp -R "$SRC/skills/$s" "$ROOT/skills/$s"
  echo "         - $s"
done

# Record exact commit for provenance (best-effort via gh; else leave the tag only).
COMMIT="$(gh api "repos/${REPO}/git/ref/tags/${TAG}" --jq '.object.sha' 2>/dev/null || echo "")"

echo "[vendor] Writing provenance manifest vendored.json ..."
REPO="$REPO" TAG="$TAG" COMMIT="$COMMIT" LICENSE="$LICENSE" \
SKILLS_JSON="$(printf '%s\n' "${SKILLS[@]}" | python3 -c 'import sys,json;print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')" \
python3 - "$ROOT/vendored.json" <<'PY'
import json, os, sys, datetime
path = sys.argv[1]
data = {}
if os.path.exists(path):
    data = json.load(open(path))
data["google-agents-cli"] = {
    "repo": os.environ["REPO"],
    "tag": os.environ["TAG"],
    "commit": os.environ.get("COMMIT") or None,
    "license": os.environ["LICENSE"],
    "synced": datetime.date.today().isoformat(),
    "note": "Third-party vendored skills. Do not hand-edit; re-run scripts/vendor-agents-cli.sh.",
    "skills": json.loads(os.environ["SKILLS_JSON"]),
}
with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY

echo "[vendor] Done. ${REPO}@${TAG} (${COMMIT:-no-commit-recorded}) vendored."
echo "[vendor] Review the diff, update the README, then commit and cut a cabral-skills release tag."

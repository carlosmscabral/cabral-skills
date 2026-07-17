#!/usr/bin/env bash
# Vendor the Google agents-cli skills into cabral-skills at a PINNED upstream tag.
#
# Upstream: https://github.com/google/agents-cli  (Apache-2.0)
# These skills are THIRD-PARTY and vendored into plugins/adk-developer/skills/ — do not hand-edit them;
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

DEST_SKILLS="$ROOT/plugins/adk-developer/skills"
mkdir -p "$DEST_SKILLS"
echo "[vendor] Copying ${#SKILLS[@]} skills into plugins/adk-developer/skills/ ..."
for s in "${SKILLS[@]}"; do
  if [ ! -d "$SRC/skills/$s" ]; then
    echo "[vendor] ERROR: upstream skill '$s' not found at ${TAG}." >&2
    exit 1
  fi
  rm -rf "${DEST_SKILLS:?}/$s"
  cp -R "$SRC/skills/$s" "$DEST_SKILLS/$s"
  echo "         - $s"
done

# Apply post-sync patches if scripts/patches/google-agents-cli/ exists
PATCH_DIR="$ROOT/scripts/patches/google-agents-cli"
if [ -d "$PATCH_DIR" ]; then
  shopt -s nullglob
  PATCHES=("$PATCH_DIR"/*.patch)
  shopt -u nullglob
  if [ ${#PATCHES[@]} -gt 0 ]; then
    echo "[vendor] Applying ${#PATCHES[@]} patch(es) from scripts/patches/google-agents-cli/ ..."
    for p in "${PATCHES[@]}"; do
      echo "         - Applying $(basename "$p")"
      patch -p1 --batch --no-backup-if-mismatch -d "$DEST_SKILLS" < "$p"
    done
  fi
fi

# Record exact commit for provenance (best-effort via gh; else leave the tag only).
COMMIT="$(gh api "repos/${REPO}/git/ref/tags/${TAG}" --jq '.object.sha' 2>/dev/null || echo "")"

echo "[vendor] Writing provenance manifest vendored.json ..."
PYTHONDONTWRITEBYTECODE=1 REPO="$REPO" TAG="$TAG" COMMIT="$COMMIT" LICENSE="$LICENSE" DEST_SKILLS="$DEST_SKILLS" ROOT="$ROOT" \
SKILLS_JSON="$(printf '%s\n' "${SKILLS[@]}" | python3 -c 'import sys,json;print(json.dumps([l.strip() for l in sys.stdin if l.strip()]))')" \
PYTHONDONTWRITEBYTECODE=1 python3 - "$ROOT/vendored.json" <<'PY'
import datetime
import json
import os
import sys

# Import shared digest calculation function from validate_repo
repo_root = os.environ["ROOT"]
sys.path.insert(0, os.path.join(repo_root, "scripts"))
from validate_repo import calculate_tree_digest

path = sys.argv[1]
dest_skills = os.environ["DEST_SKILLS"]
skills = json.loads(os.environ["SKILLS_JSON"])

digests = {}
for s in skills:
    skill_dir = os.path.join(dest_skills, s)
    if os.path.exists(skill_dir):
        digests[s] = calculate_tree_digest(skill_dir)

data = {}
if os.path.exists(path):
    with open(path, "r") as f:
        data = json.load(f)

data["google-agents-cli"] = {
    "repo": os.environ["REPO"],
    "tag": os.environ["TAG"],
    "commit": os.environ.get("COMMIT") or None,
    "license": os.environ["LICENSE"],
    "synced": datetime.date.today().isoformat(),
    "note": "Third-party vendored skills. Do not hand-edit; re-run scripts/vendor-agents-cli.sh.",
    "skills": skills,
    "digests": digests,
}

with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY

echo "[vendor] Done. ${REPO}@${TAG} (${COMMIT:-no-commit-recorded}) vendored."
echo "[vendor] Review the diff, update the README, then commit and cut a cabral-skills release tag."

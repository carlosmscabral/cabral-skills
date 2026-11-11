#!/usr/bin/env bash
# Vendor the duboc/agy-skills `cloud-architecture-diagram` skill into cabral-skills at a PINNED commit.
#
# Upstream: https://github.com/duboc/agy-skills  (Apache-2.0)
# Role: this script is the only writer of plugins/architecture-walkthrough/skills/<vendored skill>.
# Do not hand-edit the vendored directory. Change upstream, or add a patch file, then run this script.
#
# Why a commit and not a tag: the upstream repository publishes no tags and no releases.
# The script resolves the given ref to a full commit SHA and records that SHA as the pin.
#
# Why a patch: the upstream description triggers on every "architecture diagram" request.
# That trigger collides with the Dendrite plugin. The patch narrows the trigger to HTML walkthroughs.
#
# Usage:
#   scripts/vendor-agy-skills.sh <commit-sha|branch>     # e.g. scripts/vendor-agy-skills.sh main
#
# Requires: curl, unzip, patch, python3. Uses `gh` to resolve a branch name to a commit SHA.

set -euo pipefail

REPO="duboc/agy-skills"
LICENSE="Apache-2.0"
KEY="duboc-agy-skills"
PLUGIN="architecture-walkthrough"
REF="${1:-}"
if [ -z "$REF" ]; then
  echo "usage: $0 <commit-sha|branch>   (e.g. main)" >&2
  exit 2
fi

# The exact set of upstream skills that this repository redistributes.
SKILLS=(
  cloud-architecture-diagram
)

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# The script pins a full SHA. If `gh` cannot resolve the ref, the script accepts only a 40-char SHA.
COMMIT="$(gh api "repos/${REPO}/commits/${REF}" --jq '.sha' 2>/dev/null || echo "")"
if [ -z "$COMMIT" ]; then
  if [[ "$REF" =~ ^[0-9a-f]{40}$ ]]; then
    COMMIT="$REF"
  else
    echo "[vendor] ERROR: cannot resolve '${REF}' to a commit. Pass a full 40-char SHA." >&2
    exit 1
  fi
fi

echo "[vendor] Downloading ${REPO}@${COMMIT} ..."
curl -fsSL -o "$TMP/src.zip" "https://github.com/${REPO}/archive/${COMMIT}.zip"
unzip -q -o "$TMP/src.zip" -d "$TMP"
SRC="$(find "$TMP" -maxdepth 1 -type d -name 'agy-skills-*' | head -n1)"
if [ -z "$SRC" ] || [ ! -d "$SRC/skills" ]; then
  echo "[vendor] ERROR: ${REPO}@${COMMIT} has no skills/ directory." >&2
  exit 1
fi

DEST_SKILLS="$ROOT/plugins/$PLUGIN/skills"
mkdir -p "$DEST_SKILLS"
echo "[vendor] Copying ${#SKILLS[@]} skill(s) into plugins/$PLUGIN/skills/ ..."
for s in "${SKILLS[@]}"; do
  if [ ! -d "$SRC/skills/$s" ]; then
    echo "[vendor] ERROR: upstream skill '$s' not found at ${COMMIT}." >&2
    exit 1
  fi
  rm -rf "${DEST_SKILLS:?}/$s"
  cp -R "$SRC/skills/$s" "$DEST_SKILLS/$s"
  echo "         - $s"
done

# The patches carry the local deltas. A patch that does not apply stops the sync (set -e).
PATCH_DIR="$ROOT/scripts/patches/$KEY"
if [ -d "$PATCH_DIR" ]; then
  shopt -s nullglob
  PATCHES=("$PATCH_DIR"/*.patch)
  shopt -u nullglob
  for p in "${PATCHES[@]}"; do
    echo "[vendor] Applying $(basename "$p")"
    patch -p1 --batch --no-backup-if-mismatch -d "$DEST_SKILLS" < "$p"
  done
fi

echo "[vendor] Writing provenance manifest vendored.json ..."
PYTHONDONTWRITEBYTECODE=1 ROOT="$ROOT" KEY="$KEY" REPO="$REPO" COMMIT="$COMMIT" LICENSE="$LICENSE" \
DEST_SKILLS="$DEST_SKILLS" SKILLS_CSV="$(IFS=,; echo "${SKILLS[*]}")" \
python3 - "$ROOT/vendored.json" <<'PY'
import datetime
import json
import os
import sys

# The digest function lives in validate_repo so that the sync and the CI check agree.
sys.path.insert(0, os.path.join(os.environ["ROOT"], "scripts"))
from validate_repo import calculate_tree_digest

path = sys.argv[1]
dest_skills = os.environ["DEST_SKILLS"]
skills = [s for s in os.environ["SKILLS_CSV"].split(",") if s]

data = {}
if os.path.exists(path):
    with open(path, "r") as f:
        data = json.load(f)

data[os.environ["KEY"]] = {
    "repo": os.environ["REPO"],
    # Upstream has no tags. The commit SHA is the pin.
    "tag": None,
    "commit": os.environ["COMMIT"],
    "license": os.environ["LICENSE"],
    "synced": datetime.date.today().isoformat(),
    "note": "Third-party vendored skill, patched by scripts/patches/duboc-agy-skills/. "
            "Do not hand-edit; re-run scripts/vendor-agy-skills.sh.",
    "skills": skills,
    "digests": {s: calculate_tree_digest(os.path.join(dest_skills, s)) for s in skills},
}

with open(path, "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")
PY

echo "[vendor] Done. ${REPO}@${COMMIT} vendored into plugins/$PLUGIN/."
echo "[vendor] Review the diff, bump plugins/$PLUGIN/plugin.json, validate, then commit."

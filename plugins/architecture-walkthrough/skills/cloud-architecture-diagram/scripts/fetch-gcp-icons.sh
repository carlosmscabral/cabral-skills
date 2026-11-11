#!/usr/bin/env bash
# Fetch Google Cloud product icons and emit the ICONS object.
#
# The icons come from the Iconify `gcp` collection, which mirrors Google Cloud's
# product icons and returns each icon's path data through a JSON API, so nothing
# here has to parse SVG. It is the only route a script can take: Google ships the
# set as a ZIP for people, and cloud.google.com/icons answers a program with a
# page shell rather than the files.
#
# The mirror carries 214 icons and Google's own set carries 226, so a product it
# does not have comes from cloud.google.com/icons by hand. The marks stay
# Google's: Iconify's Apache 2.0 label is the wrong frame for a trademark, and
# Google's terms are a permission to reference their technology accurately,
# under their brand guidelines.
#
# Usage:
#   ./fetch-gcp-icons.sh cloud-run firestore cloud-storage > icons.js
#   ./fetch-gcp-icons.sh --list | less        # every name in the set
#
# The output is one `const ICONS = {...}` declaration, where each entry is
# {vb, d}: the viewBox to scale from, and the markup to drop inside a <g>.
# Splice it into the template with build-diagram.sh.
#
# Names that are not in the `gcp` set are looked up in `logos` instead, which
# is where the plain Google Cloud wordmark lives.

set -euo pipefail

API="https://api.iconify.design"

die() { printf '%s\n' "$*" >&2; exit 1; }

command -v curl >/dev/null 2>&1 || die "fetch-gcp-icons.sh needs curl"

# python3 on macOS and Linux. Set PY to override.
if [ -z "${PY:-}" ]; then
  if command -v python3 >/dev/null 2>&1; then PY=python3
  elif command -v python >/dev/null 2>&1; then PY=python
  else die "fetch-gcp-icons.sh needs python3"; fi
fi

if [ "$#" -eq 0 ]; then
  die "usage: fetch-gcp-icons.sh <icon-name> [icon-name ...]
       fetch-gcp-icons.sh --list"
fi

if [ "$1" = "--list" ]; then
  curl -fsS "$API/collection?prefix=gcp" \
    | "$PY" -c 'import json,sys
d = json.load(sys.stdin)
names = sorted({n for group in d.get("categories", {}).values() for n in group} | set(d.get("uncategorized", [])))
print("\n".join(names))
print("\n%d icons in the gcp set" % len(names), file=sys.stderr)'
  exit 0
fi

# Comma-separated list for one round trip, plus the wordmark from `logos`.
WANTED=$(printf '%s,' "$@" | sed 's/,$//')

GCP_JSON=$(curl -fsS "$API/gcp.json?icons=$WANTED") || die "could not reach $API"
LOGO_JSON=$(curl -fsS "$API/logos.json?icons=google-cloud") || LOGO_JSON='{}'

printf '%s\n%s\n' "$GCP_JSON" "$LOGO_JSON" | "$PY" -c '
import json, sys

wanted = sys.argv[1].split(",")
docs = [json.loads(line) for line in sys.stdin if line.strip()]

icons = {}
missing = list(wanted)
for doc in docs:
    w, h = doc.get("width", 24), doc.get("height", 24)
    for name, body in doc.get("icons", {}).items():
        icons[name] = {
            "vb": "0 0 %s %s" % (body.get("width", w), body.get("height", h)),
            "d": body["body"],
        }
        if name in missing:
            missing.remove(name)

if missing:
    print("not in the gcp set: %s" % ", ".join(missing), file=sys.stderr)
    print("run with --list to see every name", file=sys.stderr)

print("/* Google Cloud product icons, from the Iconify gcp mirror. */")
print("/* The marks belong to Google. Follow cloud.google.com/icons when publishing. */")
print("const ICONS = %s;" % json.dumps(icons, separators=(",", ":"), ensure_ascii=False))
print("%d icons written" % len(icons), file=sys.stderr)
' "$WANTED"

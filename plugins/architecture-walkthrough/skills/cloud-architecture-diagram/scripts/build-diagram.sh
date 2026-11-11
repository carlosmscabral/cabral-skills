#!/usr/bin/env bash
# Splice the icons and the diagram data into the template.
#
# Usage:
#   ./build-diagram.sh icons.js my-diagram.js > architecture.html
#   ./build-diagram.sh icons.js my-diagram.js --template other.html > out.html
#
# The template carries two marker lines, `/*__ICONS__*/` and `/*__DATA__*/`.
# Each is replaced by the whole of the matching file. The result is one
# self-contained document with no imports and no build step, which is the
# point: it has to render from a file:// URL, an email attachment and a
# locked-down venue network.
#
# Rebuild after every edit to the data, then run the audit in
# references/layout-rules.md. An empty result is the passing result.

set -euo pipefail

die() { printf '%s\n' "$*" >&2; exit 1; }

HERE=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TEMPLATE="$HERE/../assets/diagram-template.html"

[ "$#" -ge 2 ] || die "usage: build-diagram.sh <icons.js> <data.js> [--template <file>]"

ICONS=$1
DATA=$2
shift 2

while [ "$#" -gt 0 ]; do
  case $1 in
    --template) [ "$#" -ge 2 ] || die "--template needs a file"; TEMPLATE=$2; shift 2 ;;
    *) die "unknown argument: $1" ;;
  esac
done

for f in "$ICONS" "$DATA" "$TEMPLATE"; do
  [ -f "$f" ] || die "no such file: $f"
done

grep -q '__ICONS__' "$TEMPLATE" || die "template has no /*__ICONS__*/ marker: $TEMPLATE"
grep -q '__DATA__' "$TEMPLATE" || die "template has no /*__DATA__*/ marker: $TEMPLATE"

awk -v icons="$ICONS" -v data="$DATA" '
  /__ICONS__/ { while ((getline line < icons) > 0) print line; close(icons); next }
  /__DATA__/  { while ((getline line < data) > 0) print line; close(data); next }
  { print }
' "$TEMPLATE"

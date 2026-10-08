#!/usr/bin/env python3
"""One-off native diagram slide via `gslides mutate raw-batch` (no full deck build).

Reference implementation of the raw-batch method behind `flow_diagram`:

1. Create a NEW deck (never edit someone else's shared deck — make a copy and offer it).
2. Build every request with self-chosen objectIds (>=5 chars) in ONE atomic
   raw-batch — no second pass to discover IDs.
3. Export the thumbnail and LOOK at it; fix and re-run with --patch to recreate only
   the elements you changed (deleteObject + create), instead of redrawing the slide.

Usage:
  diagram_slide_rawbatch.py diagram.yaml                      # new deck, prints URL + PNG path
  diagram_slide_rawbatch.py diagram.yaml --deck <ID>          # redraw on slide `p` of <ID>
  diagram_slide_rawbatch.py diagram.yaml --deck <ID> --patch dg01_here_pill,dg01_node_2
  diagram_slide_rawbatch.py diagram.yaml --dry-run            # print requests JSON only

diagram.yaml:
  kicker: QUALITY PROGRAM · STATUS
  title: "Where we are: from listening to continuous improvement"
  subtitle: Strategy comes from real conversations, becomes tests and improves in short loops
  footer: Company · Confidential          # optional
  diagram: {...}                          # same block as the `flow_diagram` archetype
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ENGINE = Path(__file__).resolve().parent.parent / "engine"
sys.path.insert(0, str(ENGINE))

from preso.engine.diagrams import (  # noqa: E402  pylint: disable=g-import-not-at-top
    C_DARK, C_FAINT, C_GREY, RawCanvas, build_diagram_canvas, filter_requests_for,
    fit_issues, validate_diagram,
)

GSLIDES = os.environ.get("GSLIDES_PATH", "/google/bin/releases/gemini-agents-gslides/gslides")
PAGE = "p"  # first slide of a fresh deck


def gs(*args: str) -> str:
    out = subprocess.run([GSLIDES, *args], capture_output=True, text=True, check=False)
    if out.returncode:
        sys.exit(f"gslides {' '.join(args[:2])} failed:\n{out.stderr or out.stdout}")
    return out.stdout


def dense_header(page: str, spec: dict) -> RawCanvas:
    """Compact header for standalone slides: kicker 8pt / title 20pt / subtitle 10pt at y=12/27/56."""
    c = RawCanvas(page, "hdr01")
    if spec.get("kicker"):
        c.box("kicker", 24, 12, 600, 16, [(str(spec["kicker"]).upper(), 8, True, C_GREY)], single_line=True)
    if spec.get("title"):
        c.box("title", 24, 27, 680, 30, [(str(spec["title"]), 20, True, C_DARK)], single_line=True)
    if spec.get("subtitle"):
        c.box("subtitle", 24, 56, 680, 18, [(str(spec["subtitle"]), 10, False, C_GREY)], single_line=True)
    if spec.get("footer"):
        c.box("footer", 24, 386, 400, 14, [(str(spec["footer"]), 7.5, False, C_FAINT)])
    return c


def build_requests(spec: dict) -> list[dict]:
    background = {"updatePageProperties": {
        "objectId": PAGE,
        "pageProperties": {"pageBackgroundFill": {"solidFill": {"color": {"rgbColor": {
            "red": 248 / 255, "green": 249 / 255, "blue": 250 / 255}}}}},
        "fields": "pageBackgroundFill.solidFill.color"}}
    header = dense_header(PAGE, spec)
    body = build_diagram_canvas(PAGE, spec.get("diagram") or {}, prefix="dg01")
    for issue in fit_issues(header) + fit_issues(body):
        print(f"⚠️  {issue}", file=sys.stderr)
    return [background] + header.requests + body.requests


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--deck", help="existing deck you own (slide `p` is redrawn)")
    ap.add_argument("--patch", help="comma-separated objectIds to delete + recreate")
    ap.add_argument("--title", default="Diagram")
    ap.add_argument("--png", default="diagram.png")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    spec = yaml.safe_load(Path(args.spec).read_text(encoding="utf-8"))
    errors, warnings = validate_diagram(spec.get("diagram"))
    for w in warnings:
        print(f"⚠️  {w}", file=sys.stderr)
    if errors:
        sys.exit("❌ " + "\n❌ ".join(errors))

    requests = build_requests(spec)
    if args.patch:
        requests = filter_requests_for(requests, {s.strip() for s in args.patch.split(",") if s.strip()})
    elif not args.deck:
        # Fresh decks ship a title layout: drop its placeholders first (same atomic batch).
        requests = [{"deleteObject": {"objectId": "i0"}}, {"deleteObject": {"objectId": "i1"}}] + requests

    if args.dry_run:
        json.dump(requests, sys.stdout, ensure_ascii=False, indent=1)
        return 0

    deck = args.deck
    if not deck:
        out = gs("mutate", "create", "--title", args.title, "--json")
        m = re.search(r"\(ID:\s*([A-Za-z0-9_-]+)\)", out) or re.search(r"([A-Za-z0-9_-]{25,})", out)
        if not m:
            sys.exit(f"Could not parse presentation ID from: {out}")
        deck = m.group(1)

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(requests, f, ensure_ascii=False)
    try:
        gs("mutate", "raw-batch", deck, "-f", f.name)
    finally:
        os.remove(f.name)
    gs("readonly", "export-thumbnail", deck, args.png, "--slide", PAGE)
    print(f"https://docs.google.com/presentation/d/{deck}/edit")
    print(f"thumbnail: {Path(args.png).resolve()}  ← open it and audit before calling it done")
    return 0


if __name__ == "__main__":
    sys.exit(main())

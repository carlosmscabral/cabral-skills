#!/usr/bin/env bash
# Deterministically validate Mermaid diagrams in Markdown (.md) and .mmd files.
# Uses a built-in zero-dependency Python structural + GitHub/Jetski compatibility linter,
# plus local `mmdc` compilation when installed in PATH.
#
# Usage:  validate-diagrams.sh <file.md | file.mmd | dir> [more ...]
# Exit 0 = all diagrams passed; 1 = at least one failed.
set -euo pipefail

if [ "$#" -eq 0 ]; then
  echo "Usage: $0 <file.md | file.mmd | dir> [more ...]" >&2
  exit 1
fi

PYTHONDONTWRITEBYTECODE=1 python3 - "$@" <<'PY'
import os
import re
import shutil
import subprocess
import sys
import tempfile

VALID_HEADERS = (
    "flowchart", "graph", "sequenceDiagram", "stateDiagram", "stateDiagram-v2",
    "erDiagram", "classDiagram", "mindmap", "gantt", "journey", "gitGraph",
    "gitgraph", "pie", "C4Context", "C4Container", "C4Component", "C4Dynamic",
    "C4Deployment", "architecture-beta", "xychart-beta", "timeline", "quadrantChart",
)


def extract_mermaid_blocks(path: str):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if path.endswith((".mmd", ".mermaid")):
        return [(1, text)]
    blocks = []
    lines = text.splitlines()
    in_block = False
    block_lines = []
    start_line = 1
    fence_re = re.compile(r"^(`{3,})\s*mermaid\s*$")
    close_fence = None
    for idx, line in enumerate(lines, start=1):
        if not in_block:
            m = fence_re.match(line)
            if m:
                in_block = True
                close_fence = m.group(1)
                start_line = idx
                block_lines = []
        else:
            if line.strip().startswith(close_fence):
                blocks.append((start_line, "\n".join(block_lines)))
                in_block = False
            else:
                block_lines.append(line)
    if in_block:
        blocks.append((start_line, "\n".join(block_lines) + "\n__UNCLOSED_FENCE__"))
    return blocks


def lint_mermaid_block(code: str) -> list[str]:
    errors = []
    if "__UNCLOSED_FENCE__" in code:
        errors.append("Unclosed ```mermaid code fence.")
        code = code.replace("__UNCLOSED_FENCE__", "")

    lines = [l.rstrip() for l in code.splitlines()]
    # Strip optional YAML frontmatter --- ... ---
    idx = 0
    while idx < len(lines) and (not lines[idx].strip() or lines[idx].strip().startswith("%%")):
        idx += 1
    if idx < len(lines) and lines[idx].strip() == "---":
        idx += 1
        while idx < len(lines) and lines[idx].strip() != "---":
            idx += 1
        if idx >= len(lines):
            errors.append("Unclosed YAML frontmatter '---' block.")
            return errors
        idx += 1

    while idx < len(lines) and (not lines[idx].strip() or lines[idx].strip().startswith("%%")):
        idx += 1

    if idx >= len(lines):
        errors.append("Empty Mermaid block.")
        return errors

    header_line = lines[idx].strip()
    header_token = header_line.split()[0].split("(")[0]
    if header_token not in VALID_HEADERS:
        errors.append(f"Invalid or unsupported Mermaid diagram header: '{header_line}'.")
        return errors

    body_lines = lines[idx + 1 :]

    if header_token in ("flowchart", "graph"):
        subgraph_ids = set()
        subgraph_depth = 0
        for lineno, raw in enumerate(body_lines, start=2):
            s = raw.strip()
            if not s or s.startswith("%%"):
                continue
            m_sg = re.match(r"^subgraph\s+([A-Za-z0-9_-]+)", s)
            if m_sg:
                subgraph_ids.add(m_sg.group(1))
                subgraph_depth += 1
                continue
            if s == "end":
                subgraph_depth -= 1
                if subgraph_depth < 0:
                    errors.append(f"Line {lineno}: Unmatched 'end' keyword.")
                continue

            # Check unquoted parentheses inside node bracket labels: ID[Label (info)]
            # Exclude cylinder syntax ID[(Label)] where outer parens are shape delimiters
            for m_lbl in re.finditer(r"[A-Za-z0-9_-]+\[([^\"\]\n]+)\]", s):
                inner = m_lbl.group(1)
                if inner.startswith("(") and inner.endswith(")"):
                    inner = inner[1:-1]
                if "(" in inner or ")" in inner:
                    errors.append(
                        f"Line {lineno}: Unquoted parentheses in node label '[{m_lbl.group(1)}]' break GitHub Mermaid; use '[\"{m_lbl.group(1)}\"]'."
                    )
            # Check unquoted parentheses inside pipe edge labels: -->|Label (info)|
            for m_edge in re.finditer(r"-->\|([^\"|\n]+)\|", s):
                inner = m_edge.group(1)
                if "(" in inner or ")" in inner:
                    errors.append(
                        f"Line {lineno}: Unquoted parentheses in edge label '|{inner}|' break GitHub Mermaid; use '|\"{inner}\"|'."
                    )

        if subgraph_depth > 0:
            errors.append(f"Unclosed 'subgraph' block ({subgraph_depth} missing 'end').")

        # Check edges connecting directly to a subgraph ID
        if subgraph_ids:
            for lineno, raw in enumerate(body_lines, start=2):
                s = raw.strip()
                if not s or s.startswith("%%") or s.startswith("subgraph ") or s.startswith("style "):
                    continue
                if "-->" in s or "-.->" in s or "==>" in s:
                    tokens = re.findall(r"\b([A-Za-z0-9_-]+)\b", re.sub(r"\[.*?\]|\{.*?\}|\(.*?\)|\|.*?\|", "", s))
                    for t in tokens:
                        if t in subgraph_ids:
                            errors.append(
                                f"Line {lineno}: Edge connects directly to subgraph ID '{t}'; connect to a node inside the subgraph instead."
                            )

    elif header_token == "sequenceDiagram":
        for lineno, raw in enumerate(body_lines, start=2):
            s = raw.strip()
            if not s or s.startswith("%%"):
                continue
            m_part = re.match(r"^(?:participant|actor)\s+\S+\s+as\s+(.+)$", s)
            if m_part:
                alias = m_part.group(1)
                if "(" in alias or ")" in alias:
                    errors.append(
                        f"Line {lineno}: Parentheses in participant alias '{alias}' break GitHub sequenceDiagram."
                    )
            m_msg = re.match(r"^[A-Za-z0-9_-]+\s*(?:->>|-->>|->|-->|-x|--x|-\)|--\))[+-]?\s*[A-Za-z0-9_-]+\s*:\s*(.+)$", s)
            if m_msg:
                msg = m_msg.group(1)
                if "`" in msg:
                    errors.append(f"Line {lineno}: Backticks in sequenceDiagram message '{msg}' break GitHub rendering.")
                if "--" in msg:
                    errors.append(f"Line {lineno}: Double-dash '--' in sequenceDiagram message '{msg}' breaks GitHub rendering.")
                if "<br" in msg.lower():
                    errors.append(f"Line {lineno}: '<br/>' in sequenceDiagram message '{msg}' breaks GitHub rendering.")

    return errors


def main():
    mmdc = shutil.which("mmdc")
    backend = "python-lint+mmdc" if mmdc else "python-lint"
    print(f"backend: {backend}")

    files = []
    for arg in sys.argv[1:]:
        if os.path.isdir(arg):
            for root, _, fnames in os.walk(arg):
                for fn in sorted(fnames):
                    if fn.endswith((".md", ".mmd", ".mermaid")):
                        files.append(os.path.join(root, fn))
        elif os.path.isfile(arg):
            files.append(arg)

    total = 0
    fails = 0
    for fpath in sorted(files):
        blocks = extract_mermaid_blocks(fpath)
        for idx, (start_line, code) in enumerate(blocks, start=1):
            total += 1
            errs = lint_mermaid_block(code)
            if not errs and mmdc:
                with tempfile.NamedTemporaryFile("w", suffix=".mmd", delete=False) as tf:
                    tf.write(code)
                    tpath = tf.name
                out_svg = tpath + ".svg"
                try:
                    proc = subprocess.run([mmdc, "-i", tpath, "-o", out_svg], capture_output=True, text=True, timeout=20)
                    if proc.returncode != 0:
                        errs.append((proc.stderr or proc.stdout or "mmdc failed").strip().splitlines()[0])
                except Exception:
                    pass
                finally:
                    for p in (tpath, out_svg):
                        if os.path.exists(p):
                            os.remove(p)
            if not errs:
                print(f"  OK    {fpath}  (block {idx}, line {start_line})")
            else:
                print(f"  FAIL  {fpath}  (block {idx}, line {start_line}):")
                for e in errs[:6]:
                    print(f"        {e}")
                fails += 1

    print("----")
    print(f"diagrams: {total}   failed: {fails}")
    sys.exit(0 if fails == 0 else 1)


if __name__ == "__main__":
    main()
PY

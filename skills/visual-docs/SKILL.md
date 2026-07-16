---
name: visual-docs
description: >
  Use when documenting anything visually and didactically — explaining a system,
  a flow, a protocol, or code so a reader learns it. Covers flow/sequence/state
  diagrams, ASCII packet & byte walks, and annotated code explanation, plus a
  deterministic compile-to-validate step so diagrams actually render. Triggers:
  "diagram this", "add an architecture diagram", "make a visual explainer",
  "explain this code visually", "walk me through the request/flow", "packet walk",
  "step-by-step diagram", "teach / onboard with docs". (For data charts/plots use
  the `dataviz` skill instead.)
---

# Visual documentation that teaches — and actually renders

Goal: visual docs that make a reader **understand**, not just diagrams that exist.
Two properties, always together:

1. **Didactic** — every diagram is chosen to teach one idea, narrated in prose, and
   built for progressive understanding (big picture → detail).
2. **Correct** — diagram-as-code is deterministic, so it's **validated by compiling,
   not by eyeballing**. A diagram that doesn't parse is a bug.

**This skill covers:** teaching-oriented flow, sequence, and state diagrams; ASCII
packet/byte/memory walks; annotated code explanation (call graphs, execution traces);
choosing the right diagram *type* for a concept; the Mermaid + ASCII authoring rules;
and the deterministic validation loop. It also covers architecture diagrams (C4).

**This skill does NOT cover:** data charts/plots (bar/line/scatter/dashboards) → use
the **`dataviz`** skill. Auto-generating a whole codebase's architecture doc end to
end → use the **`visual-explainer`** agent (it reuses this skill for the mechanics).

## 1. Didactic strategy — the spine

Pick and shape every diagram to *teach*. Core principles (full playbook and worked
recipes in [`references/didactic-strategy.md`](./references/didactic-strategy.md)):

- **Progressive disclosure.** Lead with the smallest big-picture view; add detail in
  later, zoomed-in diagrams. Never open with the 40-node diagram.
- **One concept per diagram.** If a diagram needs two paragraphs to excuse its
  complexity, split it.
- **Always narrate.** Every diagram is paired with prose that says *what to look at
  and why it matters* — the diagram shows structure, the words carry the lesson.
- **Give a legend/key.** Define shapes, colors, arrow meanings, and actors once.
- **Number the steps.** Ordered flows and walks get explicit `1,2,3…` so the reader
  can follow the sequence and you can reference steps in the prose.
- **Calibrate to the audience.** New hire vs. reviewer vs. on-caller need different
  altitudes; state the intended reader.

## 2. Pick the diagram *type* by the concept you're teaching

Match the concept to the form before you pick the tool. Snippets (validated Mermaid +
ASCII equivalent) for each are in
[`references/diagram-type-guide.md`](./references/diagram-type-guide.md).

| You're explaining… | Use | Notes |
|---|---|---|
| Control flow, decisions, branching logic | **Flowchart** (`flowchart`) | Diamonds = decisions; label every branch |
| Interaction over time, request/response, handshakes | **Sequence** (`sequenceDiagram`) | Best for "who calls whom, in what order" |
| A lifecycle / status machine | **State** (`stateDiagram-v2`) | Nodes = states, edges = transitions/events |
| A wire format, packet, byte/bit or memory layout | **ASCII packet walk** | See [`references/packet-walks.md`](./references/packet-walks.md) |
| Data shape & relationships | **ER diagram** (`erDiagram`) | Entities + cardinality |
| System/architecture layers | **C4** | See [`references/architecture-c4.md`](./references/architecture-c4.md) |
| How a piece of code executes | **Annotated code + call graph/trace** | See [`references/code-explanation.md`](./references/code-explanation.md) |

## 3. Pick the format & author cleanly

| Need | Use | Why |
|---|---|---|
| Default, GitHub-native | **Mermaid** | Renders inline on GitHub; no build step |
| Wire formats, bytes, memory, terminal/diff-friendly | **ASCII** | Renders everywhere, diffs cleanly, teaches layout |
| Nicer layout/aesthetics | **D2** (d2lang.com) | Deterministic compile (build step) |
| Multi-view architecture that must not drift | **C4 / Structurizr** | One model → many views |

**Always keep an ASCII fallback** alongside complex diagrams for plain-text/terminal
readability — and prefer ASCII outright for packets/bytes/memory (it teaches the
layout better than a box-and-arrow diagram).

**Mermaid gotchas (GitHub-targeted).** In `sequenceDiagram`, message text must be
plain ASCII — **no backticks, no `--`, no `<br/>`, no unicode arrows** — and **no `()`
in `participant ... as` aliases**. Each breaks GitHub rendering. Flowchart labels are
more permissive; quote labels with special chars. (Also: never leave a bare `~` before
a value in prose — a pair becomes strikethrough. Use `≈`.)

## 4. Validate deterministically (the important part)

**Compile every diagram before committing.** Run the co-located validator:

```bash
# from the repo root; validates all Mermaid blocks, exit!=0 on any failure
skills/visual-docs/scripts/validate-diagrams.sh skills/visual-docs/examples/ skills/visual-docs/references/
```

Backends (auto-detected, in order): local **`mmdc`** → **`npx` mmdc** → **Kroki HTTP**
(`curl`, zero-install; set `KROKI_URL` to self-host for private content). On a FAIL,
read the compiler error, fix the source, re-run until `failed: 0`.

Caveats (verified): source→syntax is deterministic but **pixel** output varies by
renderer — validate structure, not byte-identical images. And **"compiles" ≠ "GitHub
will render it"**: Kroki/some `mmdc` versions accept diagrams GitHub rejects, so the §3
token rules are the GitHub-targeted guard and the compile step catches broader
structural errors — use **both**. ASCII diagrams need no compiler; keep them in fenced
code blocks so spacing is preserved.

## 5. Available Resources

- [`references/didactic-strategy.md`](./references/didactic-strategy.md) — load when
  planning *how* to explain something: progressive disclosure, narration patterns,
  legends, audience calibration, "explain-this" recipes.
- [`references/diagram-type-guide.md`](./references/diagram-type-guide.md) — load to
  pick a diagram type; has a copy-paste Mermaid + ASCII snippet for each.
- [`references/packet-walks.md`](./references/packet-walks.md) — load for wire
  formats/protocols: RFC-style header boxes, offset rulers, byte/bit layouts,
  step-by-step walks.
- [`references/code-explanation.md`](./references/code-explanation.md) — load to
  explain code: annotated blocks, call graphs, execution traces, data pipelines.
- [`references/architecture-c4.md`](./references/architecture-c4.md) — load for
  multi-view architecture with guaranteed consistency (Structurizr/C4, MCP).
- [`examples/`](./examples/) — four validated, narrated worked examples (request flow,
  auth sequence, TCP packet walk, code explainer). Read `examples/README.md` first.

## 6. Workflow

1. State the **reader** and the **one thing** each diagram should teach (§1).
2. Map concept → diagram **type** (§2), then → **format** (§3).
3. Author it: narration + legend + numbered steps + an **ASCII fallback** for complex
   Mermaid (or ASCII outright for packets/bytes).
4. **Validate** (§4); fix on failure; re-run until clean.
5. Keep component names **canonical** across diagrams; for multi-view architecture,
   drive it from a C4 model (§ `architecture-c4.md`) so views can't drift.

---
name: visual-docs
description: >
  Use when documenting code, protocols, or flows didactically in Markdown — explaining a
  request flow, sequence handshake, state lifecycle, wire protocol, or code module so a
  reader learns it. Covers Mermaid flow/sequence/state/ER diagrams, ASCII packet & byte
  walks, and annotated code explanation with a deterministic local validator. Triggers:
  "explain this code visually", "walk me through the request/flow", "packet walk",
  "step-by-step diagram", "teach / onboard with docs". Don't use for standalone cloud or
  system architecture diagrams, C4 models, interactive architecture studios, or
  Draw.io (.drawio) exports (use `dendrite` or a dedicated architecture diagramming
  tool instead), or for data charts/plots (use `dataviz`).
---

# Visual documentation that teaches — and actually renders

Goal: visual docs that make a reader **understand**, not just diagrams that exist.
Two properties, always together:

1. **Didactic** — every diagram is chosen to teach one idea, narrated in prose, and
   built for progressive understanding (big picture → detail).
2. **Correct** — diagram-as-code is deterministic, so it's **validated deterministically,
   not by eyeballing**. A diagram that fails GitHub or Markdown rendering is a bug.

**This skill covers:** teaching-oriented flow, sequence, state, and ER diagrams in
Markdown; ASCII packet/byte/memory walks; annotated code explanation (call graphs,
execution traces); choosing the right diagram *type* for a concept; the Mermaid + ASCII
authoring rules; and the deterministic validation loop.

**This skill does NOT cover:**
- Standalone cloud, system, or agent architecture diagrams, interactive Bento matrices,
  or SVG / Draw.io (`.drawio`) exports → use **`dendrite`** (or your active architecture
  diagramming plugin).
- Data charts/plots (bar/line/scatter/dashboards) → use the **`dataviz`** skill.

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
| How a piece of code executes | **Annotated code + call graph/trace** | See [`references/code-explanation.md`](./references/code-explanation.md) |
| Cloud / system architecture, Bento, or Draw.io export | **`dendrite` skill** | Produces 16:9 Bento SVG, interactive studio widget, and `.drawio` |

### Architectural Purity Rule (Applies to `dendrite` and Technical Diagrams)
- **Technical entities only:** Nodes (`[Card]`) MUST represent real deployable runtimes, cloud/network services, AI models, data stores, client apps/modules, actors, or database tables/entities (when drawing `sequence`, `dataflow`, or `ER`/schema diagrams). Zones (`Zone`) MUST represent real technical boundaries (cloud project, region, VPC/subnet, client vs. backend, security perimeter, or technical runtime layer).
- **Omit ambient support plumbing unless it is the diagram's focus:** Do NOT draw standalone cards or fake data-plane hops for default infrastructure plumbing attached to a compute service — such as `IAM Service Accounts`, `Secret Manager`, passive `Cloud Logging` (`stdout`), `Artifact Registry` / `Cloud Build`, or `Cloud DNS` / `Cloud NAT` — unless the diagram is specifically about IAM/Zero-Trust security, SIEM/observability, CI/CD pipelines, or hybrid networking. When helpful, note an identity or config briefly in `subLabel` or `description`.
- **Protocol & state edges:** Connectors and `animation` packet walks MUST show real protocols, endpoints, data payloads, auth tokens, or explicit allow/deny network behaviors (e.g., `WSS PCM 16kHz`, `HTTPS POST :search`, `HTTP 403`). Sparse technical callouts (`shape: "callout"`, 1–2 max) are allowed only for inline wire gates/blocks.
- **Never mix product slides into architecture diagrams:** NEVER create zones or cards for implementation phases/timelines (`Wave 1/2`, `Short/Medium Term`), qualitative value-props/guarantees (`Zero Quota Contention`), benchmark KPIs (`-92% Tokens`), "Why we chose X" rationales, or loose UI/prompt features disguised as microservices. Route timelines, features, comparisons, and KPIs to slides (`preso-builder`) or Markdown tables.

## 3. Pick the format & author cleanly

| Need | Use | Why |
|---|---|---|
| Default in Markdown / PRs | **Mermaid** | Renders inline on GitHub and Markdown viewers; no build step |
| Wire formats, bytes, memory, terminal/diff-friendly | **ASCII** | Renders everywhere, diffs cleanly, teaches layout |

**Always keep an ASCII fallback** alongside complex diagrams for plain-text/terminal
readability — and prefer ASCII outright for packets/bytes/memory (it teaches the
layout better than a box-and-arrow diagram).

**Mermaid gotchas (GitHub & Chat UI targeted):**
- Always wrap node labels containing special characters or parentheses in double quotes:
  `A["API Gateway (v2)"]` (unquoted `[API (v2)]` breaks GitHub's parser).
- Always quote pipe edge labels that contain parentheses or special characters:
  `A -->|"POST /orders (JSON)"| B`.
- Never link directly to or from a `subgraph` ID (`NodeA --> SubgraphID` fails in
  standard parsers); always connect node-to-node inside the subgraph.
- In `sequenceDiagram`, message text must be plain ASCII — **no backticks, no `--`,
  no `;`, no `<br/>`, no unicode arrows** — and **no `()` in `participant ... as`
  aliases**. Each breaks GitHub rendering.
- Never leave a bare `~` before a value in prose — a pair becomes strikethrough. Use `≈`.

## 4. Validate deterministically (the important part)

**Validate every diagram before committing.** Run the co-located zero-dependency validator:

```bash
# from the repo root; validates all Mermaid blocks in Markdown/mmd files, exit!=0 on any failure
skills/visual-docs/scripts/validate-diagrams.sh skills/visual-docs/examples/ skills/visual-docs/references/
```

The validator runs an offline Python structural & GitHub-compatibility linter on every
fenced `mermaid` block (catching unquoted parentheses, invalid `sequenceDiagram` tokens,
subgraph-ID edge links, and unbalanced brackets), plus local `mmdc` compilation when
installed. On a FAIL, read the diagnostic line, fix the source, and re-run until
`failed: 0`.

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
- [`examples/`](./examples/) — four validated, narrated worked examples (request flow,
  auth sequence, TCP packet walk, code explainer). Read `examples/README.md` first.

## 6. Workflow

1. State the **reader** and the **one thing** each diagram should teach (§1).
2. Map concept → diagram **type** (§2), then → **format** (§3).
3. Author it: narration + legend + numbered steps + an **ASCII fallback** for complex
   Mermaid (or ASCII outright for packets/bytes).
4. **Validate** (§4); fix on failure; re-run until clean.
5. Keep component names **canonical** across diagrams. If the user asks for an
   editorial cloud/system architecture diagram, C4 model, interactive architecture studio, or
   Draw.io export, switch to the `dendrite` skill.

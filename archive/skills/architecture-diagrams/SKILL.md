---
name: architecture-diagrams
description: >
  Produce editorial-quality cloud, system, C4, and agent architecture diagrams as
  standalone vector SVG, interactive Archify-style HTML explorers (with walkthrough
  chapters, node inspection, zoom/pan, and light/dark themes), native editable Draw.io
  (.drawio) XML, and dual-mode .drawio.svg files (plus 2x Retina PNG) using official
  4-color Google Cloud and multi-cloud vector icons and a 15-point mechanical geometry
  verifier. Triggers: "architecture diagram", "draw GCP/cloud architecture", "export to
  draw.io", "convert Mermaid to architecture diagram", "C4 diagram", "agent architecture
  diagram". Don't use for ASCII packet/byte walks or annotated code explainers in
  Markdown (use `visual-docs`), or for multi-agent Well-Architected trade-off research
  (use `architecture-research-blueprint`).
---

# Architecture Diagrams Studio — Editorial SVG, Interactive HTML & Draw.io

Goal: produce **publication-grade, mechanically verified architecture diagrams** that look
crafted by a Principal Architect AND remain 100% editable in Draw.io (`go/draw-io` /
`diagrams.net`) and explorable in the browser.

Instead of hand-coding raw SVG or `mxGraphModel` coordinates from memory (which causes
overlapping boxes, garbled icons, and diagonal lines slicing through labels), author a
declarative **`model.json`** (or pass an existing `.mmd` Mermaid file) and compile it
with the bundled zero-dependency engine:
[`scripts/arch_engine.py`](./scripts/arch_engine.py).

---

## 1. Strict Fact Grounding & Sufficiency Gate (Non-Negotiable)

1. **Zero Hallucinated Infrastructure**: Draw and label ONLY services, boundaries,
   protocols, and data stores supported by context (prompt, codebase, Terraform/IaC, or
   design doc). Never invent unmentioned components (e.g., do not inject Cloud Armor,
   Secret Manager, Cloud NAT, or VPC Service Controls unless present in context).
2. **Information Sufficiency Gate**: If the user asks to draw an architecture from
   scratch and the prompt lacks core components or flows, **stop and ask targeted
   clarifying questions** before generating deliverables.
3. **Verbatim Official Icons Only**: All 47 official 4-color Google Cloud, multi-cloud
   (AWS, Azure, SharePoint), and generic vector `<symbol>` icons live in
   [`references/icons_catalog.json`](./references/icons_catalog.json). Never freehand or
   approximate SVG paths.

---

## 2. Choose the Archetype, Theme & Routing

Full schema and spatial laws are in
[`references/model-schema-and-bento-laws.md`](./references/model-schema-and-bento-laws.md).

| Architecture Scenario | `layout` value | Structure |
|---|---|---|
| **Left-to-Right Cloud / Multi-Cloud Pipeline** (Default) | `"pipeline-lr"` | Columns ordered by tier (`actor` → `ingress` → `bridge`/`wif` → `compute` → `ai` → `data` → `external`), max 3 cards per column |
| **4-Zone Enterprise / Governance Platform** | `"bento-sandwich"` | Top ingress/perimeter row, middle execution & governance row, bottom data/tools foundation row |
| **Agent / ADK / CES Orchestrator Topology** | `"hub-spoke-agent"` | Central focal Agent Orchestrator surrounded by ingress (left), models/guardrails (top), session memory (bottom), and MCP/OpenAPI tools (right) |
| **Multi-Level C4 Model (L1 / L2 / L3 Tabs)** | Multi-page (`"pages": [...]`) | Generates a multi-tab `.drawio` and multi-tab `.html` explorer (`Page 1: System Context`, `Page 2: Container`, `Page 3: Component`). See [`references/drawio-and-c4-guide.md`](./references/drawio-and-c4-guide.md) |

### Visual Themes & Connector Routing
- **Themes (`--theme`)**:
  - `editorial-light` *(default)*: Google Cloud executive style — light `#f8fafd` dot-grid
    canvas, white `#ffffff` cards, and **Focal Node Rule** (only 1–2 primary nodes set
    `"focal": true` to get `#1a73e8` blue stroke and `#e8f0fe` tint; all other cards stay
    clean neutral white).
  - `blueprint-dark`: Dark technical grid (`#020617` slate-950 canvas, `#0f172a` cards with
    cyan/emerald/amber semantic accents).
- **Routing (`--routing`)**:
  - `orthogonal` *(default)*: Right-angle corridors with `r=8px` rounded corners, automatic
    port separation (`0.3` / `0.5` / `0.7`), obstacle bypass, and opaque `<rect>` label masks.
  - `s-curve`: Figma-style cubic Bézier curves for diagonal connections, terminated with
    explicit perpendicular `<polygon>` arrowheads (preventing tilted SVG `<marker>` tips).

---

## 3. One-Command Build & Mechanical Verification Workflow

### Step 1: Author `<name>.json` (or use an existing `.mmd` file)
Write the declarative JSON model following
[`references/model-schema-and-bento-laws.md`](./references/model-schema-and-bento-laws.md)
(see worked examples in [`examples/gcp-agentic-platform.json`](./examples/gcp-agentic-platform.json)
and [`examples/c4-multipage-example.json`](./examples/c4-multipage-example.json)).

### Step 2: Run `arch_engine.py build`
```bash
python3 skills/architecture-diagrams/scripts/arch_engine.py build <model.json> \
  --out-dir <output_dir> \
  --name <diagram-slug> \
  --png
```
*(Or convert a Mermaid flowchart directly via `--from-mermaid path/to/diagram.mmd`.)*

This single command plans the non-overlapping geometry, renders all deliverables, and
automatically runs the **15-point mechanical checker (`check`)**:

1. **`<slug>.html`** — Self-contained **Interactive Architecture Explorer** (`archify`
   style): Zoom/Pan, **Light/Dark theme toggle**, **Guided Walkthrough Chapters** bar,
   click-any-node **Path Tracer & Metadata Inspector**, multi-page tabs, executive summary
   cards, and offline download buttons for `.drawio` and `.drawio.svg`.
2. **`<slug>.drawio.svg`** — **Dual-Mode Vector SVG + Draw.io**: renders as a 100% crisp
   vector SVG in browsers, GitHub, and Markdown, AND embeds the `<mxfile>` XML inside the
   root `<svg content="...">` attribute so opening it in `draw.io` / `go/draw-io` / Google
   Drive launches the editable diagram directly!
3. **`<slug>.drawio`** — Native `mxGraphModel` XML with editable boundary containers,
   cards, attached 4-color vector icons (`data:image/svg+xml,<BASE64>` without the
   `;base64` semicolon bug), and orthogonal connectors.
4. **`<slug>.svg`** — Clean standalone vector SVG with embedded JSON model island.
5. **`<slug>.png`** — High-DPI `2x` Retina PNG rendered via headless Chrome (when `--png`
   is passed).

### Step 3: Verify & Inspect
If `arch_engine.py check` reports any `[FAIL]`, fix the model and re-run until it exits
`0`. When `--png` is generated, view the `.png` once to confirm overall visual balance.

### Utility: Convert Any Existing `.svg` into Dual-Mode `.drawio.svg`
```bash
python3 skills/architecture-diagrams/scripts/arch_engine.py svg2drawio input.svg -o output.drawio.svg
```

---

## 4. Available Resources

- [`references/model-schema-and-bento-laws.md`](./references/model-schema-and-bento-laws.md)
  — Complete `model.json` schema, 16:9 Bento Grid laws, WIF multi-cloud bridge pattern,
  executive copywriting rules, and available icon keys.
- [`references/drawio-and-c4-guide.md`](./references/drawio-and-c4-guide.md) — Multi-page
  C4 (L1 Context, L2 Container, L3 Component) rules, Draw.io XML invariants, and when to
  use external `Agents365-ai/drawio-skill` for raw Terraform/K8s/SQL repository scraping.
- [`references/icons_catalog.json`](./references/icons_catalog.json) — 47 verbatim vector
  `<symbol>` definitions and 75 product aliases.
- [`examples/gcp-agentic-platform.json`](./examples/gcp-agentic-platform.json) &
  [`examples/c4-multipage-example.json`](./examples/c4-multipage-example.json) —
  Validated reference models.

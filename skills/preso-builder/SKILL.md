---
name: preso-builder
description: >-
  Builds Google Slides decks in clean Google Cloud Editorial visual style from a YAML
  spec (preso_spec.yaml), ingesting codebases, existing decks, or markdown docs, with
  18 slide archetypes, native editable diagrams (cycle, timeline, funnel, layered_cake,
  swimlanes with glued connectors), geometry-aware text-fit checks, WCAG AA contrast
  validation, duration tiers, and a render-audit loop on real thumbnails. Agnostic of
  topic or narrative structure — focused strictly on visual design and layout geometry.
  Use when asked to create, restyle, or QA a Google Slides deck, convert a repo or doc
  into slides, draw a roadmap / process / layered / swimlane diagram slide, cut a
  5/15/45-minute version of a deck, or redesign a single slide.
---

# preso-builder: Google Cloud Editorial slide design engine

A spec-first visual layout engine: you author `preso_spec.yaml` in any structure or
storyline your topic needs (from a single status slide to a multi-section deck). The
engine (bundled in [`engine/`](engine/README.md) next to this file) validates geometry
and WCAG contrast, compiles one atomic `gslides batch`, builds a clean blank Google
Slides deck (or clones `--template-id` when requested), prunes the default blank slide
`p`, and exports thumbnails so you can audit what actually rendered.

## When to use

- Design clean Google Cloud Editorial slides (`#FFFFFF` white, `#F8F9FA` soft diagram/card canvases, `#202124` charcoal, and `#1A73E8` blue canvases, top mini 4-color bar, Zen *Ma* adaptive negative space, `ROUND_RECTANGLE` hairline cards, and `Google Sans` Regular titles) for any domain, audience, or deck structure.
- Restyle an existing Google Slides deck (`ingest --slides <deck_id>`).
- Cut one deck to several talk lengths (`--duration 5|15|45|full`).
- Redesign one slide, or visually QA/audit a built deck.
- Draw a native process or architecture diagram slide (`cycle`, `timeline`, `funnel`, `layered_cake`, `swimlanes`) that stays
  editable in Slides (`flow_diagram`).

Not for: data charts or telemetry plots (`dataviz`), dense technical/architecture diagrams
(render Dendrite/Mermaid/draw.io to PNG and place them with `image_split`), Docs/Sheets authoring.

## Setup

```bash
SKILL_DIR=<directory containing this SKILL.md>
pip install -e "$SKILL_DIR/engine"         # gives you the `preso` command
# or, without installing:
alias preso="python3 $SKILL_DIR/engine/preso.py"
test -x /google/bin/releases/gemini-agents-gslides/gslides && echo "live build OK"
```

Without `gslides`, the engine still validates, previews (`preview.html`), and emits
the batch JSON (`build --dry-run --output-batch ops.json`).

## Workflow

### 1. Intake gate (ask first, only what is missing)

Before writing a spec, make sure you know what is missing in **one** `ask_question` call
(never ask what the user already told you):

| Parameter | Why it matters for design |
|---|---|
| Slide count / duration (`1 slide`, `5 / 15 / 45 min`, `full`) | Density and tier filtering (`--duration`) |
| Language (`PT-BR` / `EN` / `ES` …) | Visible text and labels |
| Audience & density (executive scan vs. technical detail) | Archetype choice and text conciseness |
| Source material (repo, doc, existing deck, or direct prompt) | `ingest` vs authoring `preso_spec.yaml` directly |

### 2. Map information shape to visual archetypes

The skill imposes **no narrative arc or fixed slide order** — organize slides around whatever
structure fits the user's goal. Pick each slide's archetype purely from the **shape of the
information**:

| Information shape | Best archetype(s) |
|---|---|
| Opening title / optional evolution pills (`A → B → [C]`) | `cover` |
| Section break inside a longer deck | `chapter_divider` (`include_divider: false` on chapters that don't need one) |
| High-contrast single statement, key thesis, or provocation | `statement_pivot` (`variant: blue` `#1A73E8` or `variant: dark` `#202124`) |
| 2–3 side-by-side cards (optionally under a connected `flow_steps` strip or above a `foundation` bar) | `split_cards` |
| 4 (`2×2`) or 6 (`2×3`) numbered pillars / summary cards | `executive_grid` |
| Rows × columns option evaluation / heat-matrix | `capability_matrix` |
| 1 hero KPI on the left + 2–4 leading indicators on the right | `kpi_spotlight` |
| 2–3 peer headline stats side by side | `hero_metrics` |
| 3–4 sequential horizontal steps | `ladder_hierarchy` |
| 2–4 ascending maturity horizons (`Agora (Curto Prazo)` → `Médio Prazo` → `Longo Prazo (Futuro)`) | `horizon_staircase` |
| Do vs. Don't comparison | `dodont_checklist` |
| Code / config snippet in dark monospace frame | `code_terminal` |
| Live demo transition + "watch for" chips | `demo_pivot` |
| Principles + right-hand roadmap card, or dark multi-column decisions | `actionable_takeaways` or `closing_ask` |
| Editable native loop, milestone row, funnel, bottom-up layered cake, or horizontal swimlanes | `flow_diagram` (`cycle` / `timeline` / `funnel` / `layered_cake` / `swimlanes`) |
| Per-initiative / workstream catalogue card (left visual + right KPIs, risks vs. strengths, actions) | `workstream_card` |
| External diagram PNG / screenshot (split with bullets or full-bleed) | `image_split` |

### 3. Draft the spec (Visual & Layout Rules)

```bash
preso ingest --repo <dir> | --markdown <doc.md> | --slides <deck_id> --output preso_spec.yaml
preso spec --preset minimal --title "<Title>" --output preso_spec.yaml   # minimal starter skeleton
```

Visual authoring rules:

- **Zen Editorial headers & optional kickers.** Keep `title` to a crisp single-line `Google Sans` Regular headline (`<= 45` chars renders at `26.5pt`, `46–62` chars at `23.5pt`) and `subtitle` (optional) to a single supporting line (`13.5pt`, `<= 90` chars). Omit `kicker` on standard content slides when you want pure Zen breathing room below the mini 4-color bar; use `kicker` (`<= 20` chars) selectively on pivots or multi-section decks.
- **Adaptive *Ma* negative space.** Sparse slides (`executive_grid`, concise `split_cards`, `horizon_staircase`, `kpi_spotlight`, `closing_ask`) automatically anchor content lower on the canvas to preserve generous whitespace above; keep card bullets short (2–3 concise lines) so this breathing room stays intact.
- **Visual variety.** Avoid more than 2 consecutive slides with the exact same archetype (the validator warns so the deck doesn't look repetitive; intentional catalogues like `workstream_card` series are fine when requested).
- **Tier slides when building multi-length decks:** `core` (always shown), `explain` (15 min+), `detail` (45 min+), or `appendix` (built but hidden via `skip-slide`). Use `skip: true` to hide an individual slide.
- **Native diagrams (`flow_diagram`):** Choose `layered_cake` for bottom-up stacked architectures (foundation at base → platforms → top tier), `swimlanes` for top-to-bottom horizontal bands, `cycle` for continuous loops, `timeline` for milestone cards, and `funnel` for stage-by-stage chevrons.
- **Self-explanatory horizon labels (never `H1/H2/H3`).** Whenever a slide shows time horizons, write `Agora (Curto Prazo)`, `Médio Prazo`, `Longo Prazo (Futuro)` instead of ambiguous `H1/H2/H3`.
- **Fast image & placeholder workflow.** Pass `image: {placeholder: "Descrição..."}` on `workstream_card` or `image_split` for an instant grey drop-zone with zero upload calls. When embedding vector architecture diagrams (such as Dendrite `.svg` exports) into `image_split`, rasterize them via [`scripts/svg_to_slide_png.py`](scripts/svg_to_slide_png.py) (`<slug>.slide.png`, calibrated at `<=1999px` Skia width so Google Slides' `=s2048` server cap never downscales/blurs text) and prefer `image_layout: full`. Keep embedded `Dendrite` diagrams strictly **100% technical architecture** (cloud services, runtimes, models, network boundaries, protocols, packet walks); express implementation phases/horizons (`horizon_staircase`, `timeline`), qualitative benefits/KPIs (`kpi_spotlight`, `split_cards`, `dodont_checklist`), and architectural rationale in native slide archetypes or side callouts — never as fake "benefit/wave" zones inside the technical diagram.
- **Optional speaker notes.** Include `speaker_notes` only when requested; nothing is invented or flagged when omitted.
- **Clean visible text.** Strip any leftover citation markers (`[cite: 3]`, `[1]`, `【4】`); the validator warns on them.

Archetypes are documented in [references/archetypes.md](references/archetypes.md), and the full
YAML schema is in [references/spec_schema.md](references/spec_schema.md).

### 4. Validate and fit (Checker)

```bash
preso inspect --spec preso_spec.yaml          # outline, tiers, per-slide notes word count
preso budgets                                 # per-slot capacity from real geometry
preso qa --spec preso_spec.yaml -o dist/qa    # full offline QA + preview.html
```

`preso build` runs the validator's **geometry pass**. It compiles the spec and
reports each overflowing box as `Geometry fit in '<element>' … (cut ~N chars;
capacity ~M)`. Cut exactly that much and don't guess. Geometry numbers are authoritative
over the flat per-field budgets. Roughly: a 3-card title holds about 19 chars, a 2-card
title about 32, the one-line subtitle about 94, and a hero value about 5 (3 metrics) or 9 (2 metrics). Check with `preso budgets`.
For `flow_diagram`, the validator lays the diagram out offline and warns when a card or node
overflows, or when a pill, chip, or label would wrap onto a second line.

### 5. Build

```bash
preso build --spec preso_spec.yaml [--duration 15] [--deck-id <existing>] [--template-id <master>] [--audit-slides 1,2,10] [--no-thumbnails]
```

- By default, `preso build` creates a clean blank presentation, runs the batch, atomically prunes the initial default slide `p` via `deleteObject` raw-batch, uploads any
  local `image_split` / `workstream_card` images in parallel (`ThreadPoolExecutor`), draws `flow_diagram` bodies in one atomic `mutate raw-batch`,
  exports **fresh** thumbnails (with automatic backoff on HTTP 429), and writes `dist/qa/audit_checklist.md`. Pass `--template-id <id>` (or set `metadata.template_id` in the spec) when cloning a master template instead.
- `--deck-id` rebuilds in place. Previous slides are pruned atomically after the new ones are
  added.
- `--audit-slides 1,2,10` exports thumbnails only for the listed 1-based slides (ideal when slides 3–9 share the same `workstream_card` template, avoiding the 300 req/min Slides API quota). Use `--no-thumbnails` on intermediate rebuilds when you only need offline geometry/contrast QA.

### 6. Render audit (look at the pixels)

The heuristics can't see the rendered slide, so you have to. Open **every** PNG listed in
`dist/qa/audit_checklist.md` (use `view_file` on the path) and check each one against the rubric:
overflow/clipping, padding/alignment, the bottom-left footer zone, collisions,
contrast, leftover template shapes, and clean visual hierarchy.
On diagram slides also check: pills/chips on one line, connectors not crossing text or the
marker pill, arrowheads landing on the right node, nothing invisible (emoji, same-colour text).

- Fix issues in the spec and rebuild.
- **Stop after 2 fix rounds.** Show the user the deck URL, the remaining issues,
  and the thumbnails. Don't loop forever.
- To re-audit a deck without rebuilding:
  `preso audit --deck-id <ID> --spec preso_spec.yaml -o dist/qa`.

### 7. Deliver

Return the Slides URL, the tier/duration you built, and any open audit items.

## Single-slide redesign: offer 3 options

When the user wants to improve **one** slide, don't jump straight to an edit. Propose
**3 distinct directions**, each with a different archetype or structure (for example
`split_cards` → `hero_metrics` → `image_split` with a diagram). Give a one-line
rationale for each and show them as spec snippets or a quick `preview.html`. Build
only the one they pick.

## Escape hatch (when the archetypes don't fit)

Try these in order:

1. **Pathway A (use an archetype).** Almost everything fits one of the 18 archetypes, including
   `flow_diagram` for native loops, roadmaps, funnels, layered cakes, and swimlanes. Rephrase the content before you
   reach for anything else. For a one-off diagram slide outside a deck build, use
   [examples/diagram_slide_rawbatch.py](examples/diagram_slide_rawbatch.py) (new deck,
   one raw-batch, thumbnail, `--patch` to redo single elements).
2. **Pathway B (render an architecture diagram).** Generate a 16:9 Bento `.svg` with `dendrite`
   (omit root `title`/`subtitle` or use `@Ghost` on the root zone so it doesn't duplicate the
   slide's header, and keep `<=4` columns), then rasterize at `<=1999px` width via
   `python3 <skill-dir>/scripts/svg_to_slide_png.py diagrams/<slug>.svg` to produce
   `diagrams/<slug>.slide.png` without Google Slides `=s2048` downscale blur. Place it with
   `image_split`:
   ```yaml
   - archetype: image_split
     title: Request path
     subtitle: One gateway fronts all three regional backends
     image: {path: diagrams/request_path.slide.png, alt: "Gateway → 3 regions", caption: "Figure 2"}
     image_layout: full       # or split (with bullets on left/right)
     callout:                 # optional step-walkthrough bar under full-bleed architecture diagrams
       step: 1
       title: "Unified API Ingress"
       description: "Apigee enforces mTLS, quota, and schema contracts before routing to regional Cloud Run."
       pill: "mTLS + IAM"
   ```
   Relative paths resolve against the spec file. URLs go through batch `add-image`.
   Local files are uploaded after the batch.
3. **Pathway C (surgical edit).** For a tweak on a built deck, use `gslides` batch or
   mutate commands directly on the element IDs (`gslides read-all <deck>`). Then
   re-run `preso audit`. Remember that the next `preso build` overwrites the change, so
   put durable changes back into the spec.

## Gotchas

- Run commands as `preso …` only if the package is installed. Otherwise use
  `python3 <skill-dir>/engine/preso.py …`.
- `--clean-placeholders` returns **400** on the Blueprint template because it has no `i0`/`i1`.
  Leave it off, since template slides are pruned automatically.
- Hero metric values overflow at 54pt beyond about 5 chars with 3 metrics, or about 9 with 2. Move the qualifier into `unit`.
- Avoid emoji outside the Basic Multilingual Plane (😀, 📍 and similar) in visible text. They render
  unreliably (📍 vanishes on a red pill) and shift UTF-16 ranges; `flow_diagram` strips them and
  the validator warns. BMP symbols like `▶ ✓ ✗ → ↻ ●` are fine.
- Raw Slides requests (diagrams): objectIds need ≥5 chars and the batch is atomic; a fresh deck's
  slide `p` carries placeholders `i0`/`i1` to delete; `mutate create --json` prints plain text
  (parse `(ID: …)`). Details in [references/batch_operations.md](references/batch_operations.md) §7.
- Never edit someone else's shared deck. Build into a new deck and offer the copy.
- In raw `gslides` batch edits (Pathway C), note these quirks: `style-text` ignores `line_spacing`,
  `resize-element` takes a scale factor rather than points, `move-element` resets scale,
  `skip-slide`/`unskip-slide` exist even though `--help` doesn't list them, and
  `--json` returns `resolved_ids` (placeholder → real object ID). Always pass `"content_alignment": "MIDDLE"`
  with matching `y`/`height` on compact chip, pill, and circular-badge textboxes (`TEXT_BOX` defaults to
  `"TOP"` with ~`7.2pt` top inset, which shifts single-line labels visibly downward; `QAVerifier` flags this via
  `chip_vertical_alignment`).
- The chapter divider and `cover` are **pure white (`#FFFFFF`)**, not dark. Dark pivots (`demo_pivot`, `statement_pivot` with `variant: dark`, and `closing_ask`) use **Google Charcoal (`#202124`)**; `statement_pivot` with `variant: blue` uses **Google Blue (`#1A73E8`)**.
- The validator blocks the build on errors (unknown archetype or tier, missing
  required content, budget overruns in strict mode). Everything else is a warning. Use
  `--force` only when you understand the warning.

## References

- [references/archetypes.md](references/archetypes.md): the 18 archetypes, fields, and capacities
- [references/diagram_tokens.yaml](references/diagram_tokens.yaml): palette, type scale, and grid for native diagrams
- [examples/flow_diagram_spec.yaml](examples/flow_diagram_spec.yaml): one slide per diagram layout
- [references/spec_schema.md](references/spec_schema.md): the `preso_spec.yaml` schema, tiers, and images
- [references/design_tokens.md](references/design_tokens.md): canvas, palette, and type scale
- [references/batch_operations.md](references/batch_operations.md): batch ops, IDs, and gslides quirks
- [scripts/validate_spec.py](scripts/validate_spec.py): standalone validator wrapper

---
name: preso-builder
description: >-
  Builds executive-ready Google Slides decks in "The AI Factory Blueprint" visual
  style from a YAML spec (preso_spec.yaml), ingesting codebases, existing decks, or
  markdown docs, with native editable diagrams (cycle, timeline, funnel with glued
  connectors), geometry-aware text-fit checks, duration tiers, and a render-audit loop
  on real thumbnails. Use when asked to create, restyle, or QA a Blueprint-style slide
  deck, convert a repo or doc into slides, draw a "where we are" / roadmap / process
  diagram slide, cut a 5/15/45-minute version of a deck, or redesign a single slide.
---

# preso-builder: The AI Factory Blueprint deck builder

A spec-first engine: you author `preso_spec.yaml`. The engine (bundled in
[`engine/`](engine/README.md) next to this file) validates it, compiles it into one atomic `gslides batch`, builds the deck from the
Blueprint template (`1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U`), then exports
thumbnails so you can audit what actually rendered.

## When to use

- Build a Blueprint-style executive deck from docs, RFCs, notes, or a repo.
- Restyle an existing Google Slides deck (`ingest --slides <deck_id>`).
- Cut one deck to several talk lengths (`--duration 5|15|45|full`).
- Redesign one slide, or QA/audit a built deck.
- Draw a native process diagram slide (loop, roadmap, funnel, "where we are") that stays
  editable in Slides (`flow_diagram`).

Not for: data charts or telemetry plots (`dataviz`), dense technical/architecture diagrams
(render Mermaid/draw.io to PNG and place them with `image_split`), Docs/Sheets authoring.

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

Before writing a spec, make sure you know these five things. If the user did not
say, ask in **one** `ask_question` call. Do not ask about anything they already
told you.

| Question | Why it matters |
|---|---|
| Audience (execs / engineers / customer / mixed) | Density, jargon, which archetypes |
| Talk length (5 / 15 / 45 min) | Slide count and tiers (`--duration`) |
| Language (EN / PT-BR / ES …) | All visible text and notes |
| Tone (executive, technical deep-dive, workshop) | Titles, verbs, demo slides |
| Source of truth (repo, doc, deck, or "from scratch") | `ingest` vs `spec` |

Rough sizing: about 1 slide per minute for 5–15 minute talks, and about 0.7 per minute for 45 minutes.

### 2. Content contract (before any layout)

Decks look designed when the content was decided first. For every slide that carries the
story (especially diagrams), write a two-line brief before picking an archetype:

- **What must this slide prove?** One sentence. It becomes the subtitle.
- **Where does the story go from → to, and where is "we are here"?** That decides the
  layout (`cycle` for a loop, `timeline` for milestones, `funnel` for a staged journey) and
  the `marker`.

Then **check every claim against the evidence** (data, gap analysis, status docs) before
drawing it. If something isn't done, say so: status chips (`done`/`active`/`next`) and the
honesty `note` ("Today: X mature · Y in progress") exist for that. Use executive language
without jargon on the slide; method and caveats go in the notes when there are notes.

### 3. Draft the spec (Maker)

```bash
preso ingest --repo <dir> | --markdown <doc.md> | --slides <deck_id> --output preso_spec.yaml
preso spec --preset ai_factory --title "<Title>" --output preso_spec.yaml   # from scratch
```

Authoring rules:

- **Titles are short labels, and the subtitle is the takeaway sentence.** Every
  content slide needs a subtitle of at least 4 words that states the point
  ("Agents cut review time from 2 days to 3 hours"), not a topic ("Review time").
  The validator warns when it's missing.
- **Vary the layout.** Don't use more than 2 slides in a row with the same archetype. The
  validator warns. Rotate `split_cards` with `hero_metrics`, `ladder_hierarchy`,
  `executive_grid`, and `image_split`.
- **Tier every slide** for length variants: `core` (always shown), `explain` (15 min and up),
  `detail` (45 min and up), or `appendix` (built but hidden). Use `skip: true` to hide one slide.
- **Mark the demo.** Put a `demo_pivot` slide before any live demo, with up to 3
  `watch_for` chips that tell the audience what to notice.
- **Draw flows natively.** Loops, roadmaps, staged journeys and "where we are" slides use
  `flow_diagram` (`cycle` / `timeline` / `funnel`): editable shapes, curved connectors,
  status chips, a red marker pill. Use images only for diagrams no layout covers.
- **Speaker notes are optional.** Write them only when the user wants them and you
  have real content. Nothing is generated, placeholdered, or flagged when a slide
  has none. Never pad notes with filler. When you do write them, lead with the slide's
  main message, then one line per block (card, node, step).
- **No research residue.** Remove citation markers like `[cite: 3]`, `[1]`, and `【4】`.
  The validator flags them.

Archetypes are listed in [references/archetypes.md](references/archetypes.md), and the full
schema is in [references/spec_schema.md](references/spec_schema.md).

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
preso build --spec preso_spec.yaml [--duration 15] [--deck-id <existing>]
```

- The build copies the template, runs the batch, prunes the template's own slides, uploads any
  local `image_split` images, draws `flow_diagram` bodies in one atomic `mutate raw-batch`,
  exports **fresh** thumbnails (stale ones are deleted), and writes `dist/qa/audit_checklist.md`.
- `--deck-id` rebuilds in place. Previous slides are pruned after the new ones are
  added.

### 6. Render audit (look at the pixels)

The heuristics can't see the rendered slide, so you have to. Open **every** PNG listed in
`dist/qa/audit_checklist.md` (use `view_file` on the path) and check each one against the rubric:
overflow/clipping, padding/alignment, the bottom-left footer zone, collisions,
contrast, leftover template shapes, and whether the subtitle lands as a takeaway.
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

1. **Pathway A (use an archetype).** Almost everything fits one of the 11 archetypes, including
   `flow_diagram` for native loops, roadmaps and funnels. Rephrase the content before you
   reach for anything else. For a one-off diagram slide outside a deck build, use
   [examples/diagram_slide_rawbatch.py](examples/diagram_slide_rawbatch.py) (new deck,
   one raw-batch, thumbnail, `--patch` to redo single elements).
2. **Pathway B (render a diagram).** Author Mermaid (`mmdc -i d.mmd -o d.png -w 1600 -b white`)
   or draw.io (the `drawio-skill`, export PNG), or take a screenshot. Place it with
   `image_split`:
   ```yaml
   - archetype: image_split
     title: Request path
     subtitle: One gateway fronts all three regional backends
     image: {path: diagrams/request_path.png, alt: "Gateway → 3 regions", caption: "Figure 2"}
     bullets: [Single ingress policy, Regional failover, mTLS end to end]
     image_side: right        # or left
     image_layout: split      # or full (no bullets)
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
  `--json` returns `resolved_ids` (placeholder → real object ID).
- The chapter divider is **white** with a rainbow bar, not navy. `demo_pivot` is the
  navy slide.
- The validator blocks the build on errors (unknown archetype or tier, missing
  required content, budget overruns in strict mode). Everything else is a warning. Use
  `--force` only when you understand the warning.

## References

- [references/archetypes.md](references/archetypes.md): the 11 archetypes, fields, and capacities
- [references/diagram_tokens.yaml](references/diagram_tokens.yaml): palette, type scale, and grid for native diagrams
- [examples/flow_diagram_spec.yaml](examples/flow_diagram_spec.yaml): one slide per diagram layout
- [references/spec_schema.md](references/spec_schema.md): the `preso_spec.yaml` schema, tiers, and images
- [references/design_tokens.md](references/design_tokens.md): canvas, palette, and type scale
- [references/batch_operations.md](references/batch_operations.md): batch ops, IDs, and gslides quirks
- [references/narrative_framework.md](references/narrative_framework.md): the 5-act storyline
- [scripts/validate_spec.py](scripts/validate_spec.py): standalone validator wrapper

---
name: preso-builder
description: >
  Generates executive-ready Google Slides presentations matching "The AI Factory
  Blueprint" visual style. Ingests codebases, existing slide decks, or markdown
  docs into structured specs with automated visual QA and interactive HTML previews.
---

# The AI Factory Blueprint Presentation Builder Skill (`preso-builder`)

The `preso-builder` skill enables AI agents to generate executive-ready, pixel-perfect Google Slides presentations matching the visual style guide, coordinate geometry, typography scales, color tokens, and layout archetypes of **"The AI Factory Blueprint"** (master template: `1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U`).

---

## When to Use This Skill

### Positive Triggers
- **Build executive Google Slides decks** from technical materials, architecture docs, or RFCs.
- **Convert a codebase / GitHub repository** into an executive architectural briefing deck.
- **Ingest an existing slide deck** (via Google Slides `deck_id` or export) and restyle it into the AI Factory Blueprint aesthetic.
- **Convert Markdown documents or raw engineering notes** into structured slide presentations.
- **Scaffold or validate a presentation manifest** (`preso_spec.yaml`).
- **Run automated multimodal visual QA** (geometry clamping, text overflow checks, WCAG 2.1 AA/AAA contrast calculations, and HTML preview gallery generation).

### Negative Triggers (When NOT to Use)
- For data charts, numeric plots, or telemetry dashboards $\rightarrow$ use the **`dataviz`** skill.
- For didactic technical documentation, sequence/flow diagrams, or ASCII packet walks $\rightarrow$ use the **`visual-docs`** skill.
- For authoring or editing Google Docs or Google Sheets.

---

## Prerequisites & Dual-Mode Environment Matrix

| Capability | Cloudtop / Corp Linux | Non-Cloudtop / Portable |
|---|---|---|
| Ingest codebase / markdown / notes | ✅ Full Support | ✅ Full Support |
| Spec Validation & Multimodal Visual QA | ✅ Full Support | ✅ Full Support |
| Interactive HTML Preview Gallery (`preview.html`) | ✅ Full Support | ✅ Full Support |
| Direct Google Slides Compilation (`preso build`) | ✅ Full (`gslides` binary) | ⚠️ Emits batch JSON payload |

### Setup & Installation
1. **Python 3.10+** with `pyyaml`:
   ```bash
   pip install -e ~/preso-builder
   # Or install directly from git:
   # pip install git+https://github.com/carlosmscabral/preso-builder.git
   ```
2. **Slides CLI (Cloudtop Mode)**:
   Verify the Slides CLI binary exists on your Cloudtop:
   ```bash
   test -x /google/bin/releases/gemini-agents-gslides/gslides && echo "Cloudtop Slides CLI ready"
   ```
   *Note: On non-Cloudtop environments where `gslides` is not installed, the tool gracefully falls back to generating interactive visual previews (`preview.html`) and compiling offline Google Slides API batch update payloads (`--dry-run --output-batch`).*

---

## Dual-Agent Maker-Checker Protocol & Sub-Agent Orchestration

To guarantee zero visual defects, zero text truncation, and strict adherence to executive standards, presentation creation workflows follow a **Dual-Agent Maker-Checker Protocol**:

```
 ┌─────────────────────────────────────────────────────────────┐
 │                       MAKER AGENT                           │
 │  1. Ingests source material (codebase / slides / markdown)  │
 │  2. Scaffolds & populates `preso_spec.yaml`                 │
 │  3. Selects optimal archetypes for each slide topic         │
 │  4. Drafts concise copy and substantial speaker notes       │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                      CHECKER AGENT                          │
 │  (Adversarial Auditor - Independent Verification)           │
 │  1. Validates spec schema & strict character length budgets │
 │  2. Verifies WCAG 2.1 AA/AAA contrast on all text elements  │
 │  3. Verifies canvas containment (720x405 pt) & safe margins │
 │  4. Inspects rendered `preview.html` and `qa_report.md`     │
 │  5. Blocks build on any violation; requests Maker revision  │
 └──────────────────────────────┬──────────────────────────────┘
                                │ Approved
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                   COMPILATION & DELIVERY                    │
 │  `preso build` -> Google Slides API / Batch Update          │
 └─────────────────────────────────────────────────────────────┘
```

### Maker Responsibilities:
1. **Source Discovery**: Scan the input codebase AST, markdown notes, or slide deck.
2. **Archetype Selection**: Map each topic to the most effective of the 8 Blueprint archetypes.
3. **Spec Manifest Authoring**: Generate `preso_spec.yaml` adhering to character count guidelines.
4. **Speaker Notes Generation**: Write high-context speaker notes for every slide (minimum 15 characters, ideally 2-3 substantive sentences providing narrative context).

### Checker Responsibilities:
1. **Schema & Rule Enforcement**: Execute `preso qa --spec <spec_file>` or `python3 [validate_spec.py](scripts/validate_spec.py) <spec_file>` to verify all fields.
2. **Text Overflow Verification**: Ensure card titles (< 40 chars), bullet points (< 100 chars, max 3-4 bullets), and code snippets (< 12 lines) do not overflow bounding boxes.
3. **Contrast Compliance**: Ensure all text elements meet WCAG 2.1 AA (contrast ratio $\ge 4.5:1$ for body text, $\ge 3.0:1$ for large headings).
4. **Speaker Notes Audit**: Reject any slide missing speaker notes or containing generic placeholder text.

---

## CLI Reference & Subcommands

The presentation engine is executed via the `preso` CLI command (or `python3 -m preso`):

```bash
preso <subcommand> [options]
```

### Subcommand Matrix

| Command | Purpose | Key Arguments | Example |
|---|---|---|---|
| `preso spec` | Scaffold a new `preso_spec.yaml` skeleton | `--preset [minimal\|codebase\|economics\|full]`, `--title`, `--output` | `preso spec --preset full --title "Project Falcon" --output preso_spec.yaml` |
| `preso ingest` | Ingest multi-modal source into spec | `--repo <path>`, `--slides <deck_id\|file>`, `--markdown <doc_path>`, `--output <path>` | `preso ingest --repo . --output preso_spec.yaml` |
| `preso preview` | Compile spec into interactive HTML preview gallery | `--spec <file>`, `--output <file>` | `preso preview --spec preso_spec.yaml --output preview.html` |
| `preso qa` | Run complete multimodal visual QA verification | `--spec <file>`, `--deck-id <id>`, `--output-dir <dir>` | `preso qa --spec preso_spec.yaml --output-dir ./qa_artifacts` |
| `preso build` | Compile spec into Google Slides deck | `--spec <file>`, `--template-id <id>`, `--dry-run`, `--output-batch <file>` | `preso build --spec preso_spec.yaml` |
| `preso inspect` | Print structural outline of spec or deck | `--spec <file>`, `--deck-id <id>` | `preso inspect --spec preso_spec.yaml` |

---

## Progressive Disclosure Reference Guides

Deep specifications, coordinate formulas, and design system tokens are modularized across reference documents:

* **[Layout Archetypes Guide](references/archetypes.md)**: Visual bounding boxes, parameters, and character capacity limits for all 8 layout archetypes (`chapter_divider`, `split_cards`, `code_terminal`, `hero_metrics`, `ladder_hierarchy`, `executive_grid`, `dodont_checklist`, `actionable_takeaways`).
* **[Design Tokens & Canvas Geometry](references/design_tokens.md)**: Standard widescreen dimensions (720x405 pt, 16:9), safe margin clamping, core color palette tokens, and WCAG 2.1 AA/AAA contrast ratios.
* **[Specification Manifest Schema](references/spec_schema.md)**: Complete `preso_spec.yaml` structure, archetype field mappings, and schema validation rules.
* **[Narrative Framework & Storyline](references/narrative_framework.md)**: The 5-Act storyline arc for executive technical briefings (Context $\rightarrow$ Mental Model $\rightarrow$ Mechanics $\rightarrow$ Economics $\rightarrow$ Actionable Principles).
* **[Google Slides Batch Operations](references/batch_operations.md)**: Single-pass atomic batch update compilation architecture and shape/connector definitions.

---

## Automated Multimodal QA Verification

Execute automated visual QA before compiling any presentation:

```bash
preso qa --spec preso_spec.yaml --output-dir ./qa_artifacts
```

### Verification Checks Enforced:
1. **Geometry Clamping**: Asserts every bounding box fits strictly inside $(36, 28) \dots (684, 375)$ pt.
2. **Collision & Overlap Detection**: Verifies no two non-nested shape bounding boxes collide.
3. **WCAG 2.1 AA/AAA Contrast Verification**: Relative luminance calculations for foreground/background colors (Pass threshold: $\ge 4.5:1$ for body text, $\ge 3.0:1$ for large headings).
4. **Text Truncation Prevention**: Card titles < 40 chars, bullet points < 100 chars (max 3-4 bullets), code snippets < 12 lines.
5. **Speaker Notes Completeness**: Mandatory 100% slide coverage with contextual notes.
6. **Report & Preview Generation**: Emits `qa_report.md` (Markdown compliance audit) and `preview.html` (interactive visual gallery).

---

## Step-by-Step AI Agent Execution Playbook

```
[Phase 1: Discovery & Scaffolding]
  1. Determine intent: codebase ingestion, doc conversion, or fresh deck.
  2. If ingesting codebase/doc: `preso ingest --repo <dir> --output preso_spec.yaml`
     If starting fresh: `preso spec --preset full --title "<Title>" --output preso_spec.yaml`

[Phase 2: Spec Refinement (Maker Role)]
  3. Consult references/archetypes.md to select archetypes matching the narrative.
  4. Author punchy titles, concise bullet points, and real code snippets in `preso_spec.yaml`.
  5. Write high-context speaker notes for every slide (2-3 sentences per slide).

[Phase 3: Adversarial Validation (Checker Role)]
  6. Run `preso qa --spec preso_spec.yaml --output-dir ./qa_artifacts`.
  7. Run `preso preview --spec preso_spec.yaml --output preview.html`.
  8. Inspect `qa_artifacts/qa_report.md`. If any violation occurs, correct `preso_spec.yaml` immediately.

[Phase 4: Compilation & Delivery]
  9. If Cloudtop (`gslides` available):
       `preso build --spec preso_spec.yaml`
       Return Google Slides URL to user.
     If portable mode (non-Cloudtop):
       `preso build --spec preso_spec.yaml --dry-run --output-batch slides_batch.json`
       Provide `preview.html` and `slides_batch.json` to user.
```

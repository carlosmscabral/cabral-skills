# The AI Factory Blueprint Presentation Builder (`preso-builder`)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Style: AI Factory Blueprint](https://img.shields.io/badge/style-AI_Factory_Blueprint-1E2761.svg)](https://github.com/)
[![WCAG 2.1 AA Compliant](https://img.shields.io/badge/accessibility-WCAG_2.1_AA-1E8E3E.svg)](https://www.w3.org/WAI/standards-guidelines/wcag/)
[![Tests: Passing](https://img.shields.io/badge/tests-passing-brightgreen.svg)](tests/)

An automated, executive-grade Google Slides builder and agent skill engine that ingests heterogeneous technical sources (codebases, AST structures, existing slide decks, markdown docs, and engineering notes) and compiles them into pixel-perfect presentations matching the exact visual style, typography, color palette, and layout geometry of **"The AI Factory Blueprint"** (Master Template ID: `1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U`).

> 📖 **Looking for a comprehensive walkthrough?** Check out the [User Guide](USER_GUIDE.md) for activation prerequisites, sample inputs, CLI cookbook, YAML schemas, and best practices.

---

## Architecture Flow

```
                          [ Input Sources ]
             ┌────────────────────┼────────────────────┐
             ▼                    ▼                    ▼
     [ Codebase AST ]     [ Existing Slides ]    [ Markdown Docs ]
     (Tree/Symbols/Doc)   (gslides read-all)     (Headings/Lists/Code)
             │                    │                    │
             └────────────────────┼────────────────────┘
                                  ▼
                   [ Multi-Modal Ingestion Pipeline ]
                     (preso/ingest/ - AST/Slides/MD)
                                  │
                                  ▼
                    [ preso_spec.yaml Manifest ]
                   (Declarative Spec & Structure)
                                  │
                                  ▼
             [ Specification Parser & Schema Validator ]
                    (preso/spec/ - Budgets/Rules)
                                  │
                                  ▼
             [ 8-Archetype Blueprint Coordinate Engine ]
                 (preso/engine/ - 720x405pt Geometry)
                                  │
                                  ▼
              [ gslides Atomic Single-Pass Batch Gen ]
                   (preso/compiler/ - Batch Ops)
                                  │
                                  ▼
                [ gslides CLI (copy / create / batch) ]
              (/google/bin/releases/gemini-agents-gslides)
                                  │
                                  ▼
                 [ Rendered Google Slides Deck ]
                                  │
                                  ▼
             [ Multimodal QA & Visual Verification Loop ]
            (preso/qa/ - WCAG AA/AAA, Overflows, Clamping)
                                  │
             ┌────────────────────┴────────────────────┐
             ▼                                         ▼
      [ qa_report.md ]                          [ preview.html ]
   (Markdown Audit Tables)                   (Interactive Gallery)
```

---

## Key Features

- **Strict Blueprint Design System**: Standard 720x405 pt canvas (16:9 widescreen), custom typography (`Google Sans`, `Google Sans Text`, `Roboto Mono`), and official color palette (`#1E2761` Navy, `#1A73E8` Blue, `#1E8E3E` Green, `#D93025` Red).
- **10 Standardized Layout Archetypes**: Mathematical coordinate generation for Chapter Dividers, Split Comparisons, Code Terminals, Hero Metrics, Ladder Flows, Executive 2x2 Grids, Do/Don't Checklists, Actionable Takeaways, Demo Pivots, and Image Splits (the escape hatch for rendered diagrams/screenshots).
- **Duration tiers**: tag slides `core` / `explain` / `detail` / `appendix` (or `skip: true`) and build 5/15/45-minute cuts of one deck with `--duration`; hidden slides stay in the deck via `skip-slide`.
- **Geometry-aware fit checks**: one shared `text_fit` heuristic powers the validator (`cut ~N chars` warnings), the QA verifier, and `preso budgets`.
- **Render audit loop**: every live build exports fresh thumbnails and writes `audit_checklist.md` (rubric + predicted hotspots, max 2 fix rounds).
- **Optional speaker notes**: authored notes are passed through verbatim; nothing is generated, placeholdered, or flagged when a slide has none.
- **Atomic Single-Pass Batch Compiler**: Emits deterministic `gslides batch` payloads with placeholder IDs (`SLIDE_01`, `CARD_1`), removing default template artifacts and binding authored speaker notes when present.
- **Multi-Modal Ingestion Engine**:
  - **Codebase Ingestion**: AST-level symbol extraction (Python, TypeScript, Go, Java, Rust) and file-tree parsing.
  - **Google Slides Ingestion**: Ingests existing decks via `gslides read-all <deck_id>` and classifies content into Blueprint archetypes.
  - **Markdown Ingestion**: Parses headings, lists, code fences, and tables into structured presentation specifications.
- **Automated Multimodal Visual QA**: Validates canvas bounding box clamping, detects improper overlaps, calculates WCAG 2.1 AA/AAA contrast ratios, checks text overflow budgets, and generates `qa_report.md` + `preview.html`.
- **Dual-Agent Maker-Checker Protocol**: Enforces automated separation of concerns between creative specification authoring and adversarial QA auditing.
- **Agent Skill Integration**: this engine ships inside the [`preso-builder` skill](../SKILL.md) in [carlosmscabral/cabral-skills](https://github.com/carlosmscabral/cabral-skills/tree/main/skills/preso-builder).

---

## The 10 Blueprint Slide Archetypes

| # | Archetype Identifier | Visual Description & Layout | Typical Use Cases |
|---|---|---|---|
| 1 | `chapter_divider` | White background, 4-colour Google rainbow bar across the top, 56pt 2-digit chapter number, adaptive 56/46/38pt title, Google Blue subtitle. | Section transitions, agenda framing, thematic boundaries. |
| 2 | `split_cards` (`card_split_2` / `card_split_3`) | 2 or 3 high-contrast white cards, category pills (`#E8F0FE`), 16pt bold headers, safe-bounded bullet points. | Architecture comparisons, before vs. after, alternative trade-offs. |
| 3 | `code_terminal` | Slate dark terminal window (`#202124`), macOS traffic light dots, filename header, Roboto Mono syntax text, `✓ Do` / `✗ Don't` status badges. | Pre-commit hooks, ratchets, configuration manifests, code samples. |
| 4 | `hero_metrics` (`hero_metric`) | Massive 54pt bold stat display, unit label, delta percentage pills (`+10x`, `-85%`), horizontal divider, context description. | ROI economics, benchmark performance, token cost savings. |
| 5 | `ladder_hierarchy` (`ladder_flow`) | 4-step horizontal rung pipeline with directional chevron connectors (`→`), sequential step numbers, rung titles, and descriptions. | Maturity models, sequential engineering disciplines, phased roadmaps. |
| 6 | `executive_grid` (`exec_grid_2x2`) | 2x2 numbered summary quadrant cards, vertical Google Blue accent bar (4pt), bold 1-liner takeaway headers and narratives. | Executive 1-line summaries, core operational pillars, strategic themes. |
| 7 | `dodont_checklist` (`do_dont_checklist`) | Side-by-side anti-pattern (Red `#D93025`) vs. blueprint standard (Green `#1E8E3E`) cards, check/cross bullets, synthesis footer pill. | Best practices, adoption guidelines, governance policies. |
| 8 | `actionable_takeaways` | Asymmetric split: 3 numbered action principles on left (58%), Dark Navy roadmap card + Blue CTA button on right (42%). | Closing summaries, 30-day execution roadmaps, leadership calls to action. |
| 9 | `demo_pivot` (`demo`) | Dark Navy slide, red `▶ LIVE DEMO` pill, large white title, optional subtitle, up to 3 "watch for" chips. | Switching to a live demo; telling the audience what to notice. |
| 10 | `image_split` (`image`, `diagram`) | Header + bullets card (≤4) beside a framed image, or `image_layout: full`. Local PNGs are uploaded after the batch; URLs go through `add-image`. | Mermaid/draw.io diagrams rendered to PNG, product screenshots, charts. |

---

## Design Tokens & Visual Standards

### Canvas Geometry (16:9 Widescreen)
- **Canvas Width**: `720.0 pt` ($9,144,000\text{ EMU}$)
- **Canvas Height**: `405.0 pt` ($5,143,500\text{ EMU}$)
- **Conversion Factor**: $1\text{ pt} = 12,700\text{ EMU}$
- **Margins**: Left `36.0 pt`, Right `36.0 pt`, Top `28.0 pt`, Bottom `30.0 pt`
- **Usable Width**: `648.0 pt`
- **Usable Height**: `275.0 pt` (Content Top: `100.0 pt`, Header Baseline: `92.0 pt`)

### Master Color Palette
| Token Name | Hex Code | Visual Swatch | Purpose |
|---|---|---|---|
| `COLOR_NAVY_PRIMARY` | `#1E2761` | Navy Primary | Chapter divider background, Takeaways roadmap card |
| `COLOR_NAVY_SURFACE` | `#2D3A8C` | Navy Surface | Elevated cards on dark backgrounds |
| `COLOR_SLATE_DARK` | `#202124` | Slate Dark | Monospace code terminal container |
| `COLOR_SLATE_HEADER` | `#2D3035` | Slate Header | Code terminal window header bar |
| `COLOR_BG_LIGHT` | `#F8F9FA` | Light Gray | Standard slide canvas background |
| `COLOR_CARD_WHITE` | `#FFFFFF` | Card White | High-contrast card surface fill |
| `COLOR_CARD_BORDER` | `#DADCE0` | Card Border | Subtle card stroke/outline |
| `COLOR_BLUE_ACCENT` | `#1A73E8` | Google Blue | Primary accent, pills, divider lines, CTA button |
| `COLOR_BLUE_LIGHT` | `#E8F0FE` | Light Blue | Category pill fill, takeaway footer banner fill |
| `COLOR_BLUE_SUBTITLE` | `#CADCFC` | Subtitle Blue | Subtitle text on navy backgrounds |
| `COLOR_GREEN_DO` | `#1E8E3E` | Green Do | Positive delta pill, DO badge fill |
| `COLOR_GREEN_LIGHT` | `#E6F4EA` | Light Green | Positive card banner fill, DO badge container |
| `COLOR_RED_DONT` | `#D93025` | Red Don't | Negative delta pill, DON'T badge fill |
| `COLOR_RED_LIGHT` | `#FCE8E6` | Light Red | Negative card banner fill, DON'T badge container |
| `COLOR_AMBER_WARN` | `#F9AB00` | Amber Warn | Caution pill fill, warning indicators |

### High-Contrast WCAG 2.1 AA Compliant Text Tokens
- **`COLOR_BLUE_TEXT` (`#174EA6`)**: Google Blue 800 (Contrast Ratio $> 5.5:1$ on `#E8F0FE`)
- **`COLOR_GREEN_TEXT` (`#137333`)**: Google Green 800 (Contrast Ratio $> 4.8:1$ on `#E6F4EA`)
- **`COLOR_RED_TEXT` (`#C5221F`)**: Google Red 800 (Contrast Ratio $> 4.8:1$ on `#FCE8E6`)
- **`COLOR_AMBER_TEXT` (`#7A4100`)**: Google Amber 900 (Contrast Ratio $> 5.0:1$ on `#FEF7E0`)

### Typography Scale
- **Headings**: `Google Sans` (Bold, Regular)
- **Body & Captions**: `Google Sans Text` (Regular, Medium)
- **Code & Monospace**: `Roboto Mono` (Regular, Bold)
- **Scale**: Chapter Number (`84pt`), Chapter Title (`36pt`), Slide Title (`24pt`), Card Header (`16pt`), Slide Subtitle (`13pt`), Card Body (`12pt`), Hero Stat (`54pt`), Terminal Code (`10.5pt`), Badges (`10.5pt`), Footers (`9.5pt`).

---

## Installation & Prerequisites

### Prerequisites
- Python 3.10 or higher
- Google Slides CLI: `/google/bin/releases/gemini-agents-gslides/gslides` (for live Google Slides creation)
- Python packages: `pyyaml`, `requests`

### Setup
```bash
# From the skill directory (skills/preso-builder/engine in cabral-skills)
cd skills/preso-builder/engine
pip install -e .        # optional: installs the `preso` command

# Verify python environment
python3 --version

# Run all unit and stress tests
python3 -m unittest discover -s tests -p "test_*.py" -v
```

---

## Quickstart & CLI Reference

The unified CLI entrypoint is `preso.py`.

### 1. Scaffold a Presentation Specification (`spec`)
Generate a new `preso_spec.yaml` skeleton with pre-configured archetypes:

```bash
# Available presets: minimal, codebase, economics, full
python3 preso.py spec --preset full --title "The AI Factory Blueprint" --output preso_spec.yaml
```

### 2. Ingest Source Material (`ingest`)
Extract structured slides directly from codebases, Google Slides decks, or markdown files:

```bash
# Ingest local codebase AST
python3 preso.py ingest --repo /path/to/repo --output preso_spec.yaml

# Ingest an existing Google Slides presentation
python3 preso.py ingest --slides 1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U --output preso_spec.yaml

# Ingest Markdown engineering notes
python3 preso.py ingest --markdown docs/architecture.md --output preso_spec.yaml
```

### 3. Build & Publish to Google Slides (`build`)
Compile the specification manifest into a live Google Slides presentation:

```bash
# Dry-run compilation (validates batch JSON without calling Google Slides API)
python3 preso.py build --spec preso_spec.yaml --dry-run

# Live compilation with automatic template cloning
python3 preso.py build --spec preso_spec.yaml --template-id 1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U

# Export batch payload for inspection
python3 preso.py build --spec preso_spec.yaml --dry-run --output-batch batch_ops.json

# 15-minute cut: core + explain tiers visible, detail/appendix hidden (skip-slide)
python3 preso.py build --spec preso_spec.yaml --duration 15
```

### 4. Inspect Presentation Structure (`inspect`)
Print a structured outline of a spec manifest or live Google Slides deck:

```bash
# Inspect local spec manifest
python3 preso.py inspect --spec preso_spec.yaml

# Inspect live Google Slides deck
python3 preso.py inspect --deck-id 1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U
```

### 5. Generate Visual Preview Gallery (`preview`)
Generate an interactive HTML/CSS gallery rendering accurate mockups of all slides:

```bash
python3 preso.py preview --spec preso_spec.yaml --output preview.html
```

### 6. Run Automated Multimodal Visual QA (`qa`)
Execute complete multimodal verification, checking bounding boxes, contrast, and overflows:

```bash
python3 preso.py qa --spec preso_spec.yaml --output-dir ./qa_artifacts
```

### 7. Render Audit of a Live Deck (`audit`)
Export fresh thumbnails (stale ones are cleared) and write `audit_checklist.md`:

```bash
python3 preso.py audit --deck-id <DECK_ID> --spec preso_spec.yaml --output-dir dist/qa
```

### 8. Text Budgets & Geometry Capacities (`budgets`)
Print the validator's per-field budgets plus capacities derived from real slot geometry:

```bash
python3 preso.py budgets          # or --json
```

---

## Multi-Modal Ingestion Pipelines

```
 ┌─────────────────────────────────────────────────────────────┐
 │                  MULTI-MODAL INGESTION                      │
 ├──────────────────────────────┬──────────────────────────────┤
 │ Codebase Ingestion           │ Markdown Ingestion           │
 │ • File tree scanning         │ • Heading hierarchy analysis │
 │ • VCS/binary filtering       │ • List & card extraction     │
 │ • AST symbol extraction      │ • Fenced code block parsing  │
 │ • README/doc synthesis       │ • Table metric translation   │
 ├──────────────────────────────┴──────────────────────────────┤
 │ Google Slides Ingestion                                     │
 │ • `gslides read-all <deck_id>` API payload parsing          │
 │ • Text frame, shape, and card classification               │
 │ • Automatic mapping to 8 Blueprint archetypes               │
 └─────────────────────────────────────────────────────────────┘
```

1. **Codebase AST Ingestion** (`preso.ingest.CodebaseIngestor`):
   - Recursively walks directory trees, ignoring hidden/build folders (`.git`, `node_modules`, `build`, `__pycache__`).
   - Generates compact ASCII directory trees.
   - Parses AST symbols (classes, methods, routes, schemas) across Python, TypeScript, Go, Java, and Rust.
   - Generates a complete 3-chapter presentation spec with real code snippets.

2. **Google Slides Ingestion** (`preso.ingest.SlidesIngestor`):
   - Calls `gslides read-all` to extract raw slide elements, tables, and notes.
   - Evaluates slide content to match the closest Blueprint archetype.
   - Cleans formatting and maps text into structured slide manifests.

3. **Markdown Ingestion** (`preso.ingest.MarkdownIngestor`):
   - Parses markdown document sections into chapters and slides.
   - Automatically maps subsections into cards, code fences into terminal boxes, and comparison tables into metrics or split cards.

---

## Specification Manifest (`preso_spec.yaml`)

```yaml
version: "1.0"

metadata:
  title: "The AI Factory Blueprint"
  subtitle: "Deterministic Engineering for the Agentic Era"
  template_id: "1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U"
  target_audience: "Executive Leadership & Senior Staff Engineers"
  core_thesis: "Move from manual hand-prompting to deterministic agentic manufacturing pipelines."
  theme:
    palette: "blueprint"
    primary_color: "#1E2761"
    accent_color: "#1A73E8"

chapters:
  - chapter_number: 1
    title: "Foundation & Architecture"
    subtitle: "From isolated prompts to systematic engineering"
    speaker_notes: "Welcome everyone. Today we explore the paradigm shift to deterministic AI pipelines."
    slides:
      - archetype: "chapter_divider"
        title: "Foundation & Architecture"
        subtitle: "From isolated prompts to systematic engineering"
        kicker: "CHAPTER"
        chapter_number: 1
        speaker_notes: "Welcome everyone. Today we explore the paradigm shift to deterministic AI pipelines."

      - archetype: "split_cards"
        title: "Two Paradigms of Agent Development"
        subtitle: "Comparing ad-hoc prompting with deterministic pipelines"
        kicker: "PARADIGM COMPARISON"
        cards:
          - title: "Ad-Hoc Prompting"
            category_pill: "TRADITIONAL"
            bullets:
              - "Manual copy-pasting of context into web chat"
              - "Unpredictable outputs and silent regressions"
              - "Zero test harness or automated verification"
            theme: "#1A73E8"
          - title: "Deterministic Harness"
            category_pill: "AI FACTORY"
            bullets:
              - "Automated context injection via file mounts"
              - "Enforcing hooks that block commits on failure"
              - "Adversarial evaluator sub-agents grade runs"
            theme: "#1E8E3E"
        speaker_notes: "On the left is manual trial and error. On the right is the AI Factory model."
```

---

## Automated Multimodal Visual QA Verifier

The QA verifier (`preso.qa.QAVerifier`) executes automated checks across all presentation slides:

```
┌─────────────────────────────────────────────────────────────┐
│                 QA VERIFICATION SUITE                       │
├─────────────────────────────────────────────────────────────┤
│ ✓ Geometry Clamping: All elements within 720x405 pt canvas  │
│ ✓ Collision Detection: Zero non-nested element collisions   │
│ ✓ WCAG 2.1 AA/AAA: 100% text elements pass contrast >= 4.5:1 │
│ ✓ Text Overflow Budget: Titles, bullets, code lines clamped │
│ ℹ Speaker Notes: coverage reported (optional, not scored)   │
└─────────────────────────────────────────────────────────────┘
```

Outputs generated:
- `qa_report.md`: Complete Markdown report with per-slide check statuses, WCAG contrast calculations, and geometry validation.
- `preview.html`: Standalone interactive HTML gallery rendering CSS-accurate visual representations of all 8 Blueprint slide archetypes.

---

## Dual-Agent Maker-Checker Verification Protocol

The development and execution of presentations uses a strict **Dual-Agent Maker-Checker Protocol**:

```
 ┌─────────────────────────────────────────────────────────────┐
 │                       MAKER AGENT                           │
 │  • Gathers context from codebase / docs / existing decks    │
 │  • Scaffolds & edits `preso_spec.yaml`                      │
 │  • Selects archetypes (speaker notes optional)              │
 └──────────────────────────────┬──────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                      CHECKER AGENT                          │
 │  (Adversarial Auditor - Independent Verification)           │
 │  • Executes `preso.py qa` verification suite                │
 │  • Inspects `qa_report.md` and `preview.html`               │
 │  • Checks character limits and contrast ratios              │
 │  • Blocks build on any failure with actionable feedback     │
 └──────────────────────────────┬──────────────────────────────┘
                                │ Pass
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                   COMPILATION & DELIVERY                    │
 │  • Runs `preso.py build` to generate live Google Slides deck│
 └─────────────────────────────────────────────────────────────┘
```

---

## Running the Test Suite

The test suite covers unit tests, stress geometry fuzzing, compiler batch generation, spec validation, multi-modal ingestion, and CLI commands:

```bash
# Run the entire test suite
python3 -m unittest discover -s tests -p "test_*.py" -v

# Run specific test modules
python3 -m unittest tests/test_design_tokens.py -v
python3 -m unittest tests/test_coordinates.py -v
python3 -m unittest tests/test_archetypes.py -v
python3 -m unittest tests/test_batch_generator.py -v
python3 -m unittest tests/test_spec_validator.py -v
python3 -m unittest tests/test_ingest_codebase.py -v
python3 -m unittest tests/test_ingest_slides.py -v
python3 -m unittest tests/test_ingest_markdown.py -v
python3 -m unittest tests/test_stress_m1_geometry.py -v
```

---

## Agent Skill Integration

The agent skill is defined in [`../SKILL.md`](../SKILL.md); this engine lives in its `engine/` directory.
Install it with `npx skills add carlosmscabral/cabral-skills --skill preso-builder`.

Once installed, your coding agent:
- generates, ingests, and visually QAs presentations conversationally;
- discovers the skill for queries about Google Slides, AI Factory Blueprint decks, codebase-to-slide conversions, and slide visual verification.

---

## License & Credits
Authored for **The AI Factory Blueprint** presentation automation initiative.
Reference Template: `1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U`
Canvas: 720x405 pt Widescreen | Fonts: Google Sans, Google Sans Text, Roboto Mono

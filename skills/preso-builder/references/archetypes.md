# Google Cloud Editorial Layout Archetypes Reference Guide

This document provides visual diagrams, coordinate bounding box formulas, field parameters, and character capacity limits for all **18 standardized presentation layout archetypes** in the **Google Cloud Editorial** design system.

---

### Archetype 1: `chapter_divider`

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Y=36pt  [██████ RED ██████][████ YELLOW ████][████ GREEN ████][████ BLUE ████]│ (5pt Rainbow Bar)
│                                                                             │
│ Y=52pt  03                                                                  │ (56pt Google Sans Bold, #202124)
│ Y=118pt Context Engineering                                                 │ (56/46/38pt adaptive, #202124)
│                                                                             │
│ Y=196pt Models degrade as their context fills. Manage what the agent        │ (16/15/14.5pt, #1A73E8)
│         holds in mind — or watch quality and budget collapse together.      │
│                                                                             │
│ Y=375pt Google Cloud                                       Proprietary & 14 │ (Master Layout Footer)
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Bounding Box & Coordinates
* **Canvas Fill**: `#FFFFFF` (Pure white canvas)
* **Google Rainbow Progress Bar**: `X=36pt`, `Y=36pt`, `W=648pt`, `H=5pt` (4 segments: `#EA4335` Red, `#FBBC04` Yellow, `#34A853` Green, `#4285F4` Blue)
* **Chapter Counter**: `X=36pt`, `Y=52pt`, `W=648pt`, `H=56pt` (56pt Bold Black `#202124`)
* **Chapter Title** (adaptive by length, from the engine):
  * 22 chars or fewer: 56pt, `Y=118pt`, `H=65pt` (one line). Subtitle 16pt at `Y=196pt`.
  * 23–42 chars: 46pt, `Y=116pt`, `H=112pt` (two lines). Subtitle 15pt at `Y=240pt`.
  * More than 42 chars: 38pt, `Y=114pt`, `H=126pt`. Subtitle 14.5pt at `Y=250pt`.
* **Subtitle / Aphorism**: `X=36pt`, `W=648pt`, Google Blue `#1A73E8`, line spacing `125%`
* **Not navy.** The dark navy slide is `demo_pivot`.

#### Character Capacity & Budget
* `title`: 22 chars or fewer keeps it on one line at 56pt. The practical max is about 45.
* `subtitle`: Max 120 characters.
* `speaker_notes`: Optional (nothing is written when absent). Chapter-level `speaker_notes` feed the auto divider.

---

### Archetype 2: `split_cards` (`card_split_2` & `card_split_3`)

```
Y=28pt ┌─────────────────────────────────────────────────────────────┐
       │ [KICKER] 10pt Google Sans Bold (#1A73E8)                    │
Y=40pt │ SLIDE TITLE: 24pt Google Sans Bold (#202124)                │
Y=68pt │ Subtitle / Framing: 13pt Google Sans Text (#5F6368)         │
Y=100pt├──────────────────────────────┬──────────────────────────────┤
       │ ┌──────────────────────────┐ │ ┌──────────────────────────┐ │
       │ │ [CATEGORY PILL]          │ │ │ [CATEGORY PILL]          │ │
       │ │ Card Title (16pt Bold)   │ │ │ Card Title (16pt Bold)   │ │
       │ │ ──────────────────────── │ │ │ ──────────────────────── │ │
       │ │ • First bullet point...  │ │ │ • First bullet point...  │ │
       │ │ • Second bullet point... │ │ │ • Second bullet point... │ │
       │ │ • Third bullet point...  │ │ │ • Third bullet point...  │ │
       │ └──────────────────────────┘ │ └──────────────────────────┘ │
Y=375pt└──────────────────────────────┴──────────────────────────────┘
```

#### Bounding Box & Coordinates
* **Optional Top Process Strip (`flow_steps` / `process_strip`)**: 2–5 horizontal `ROUND_RECTANGLE` step boxes (`Y=100pt`, `H=44pt`) connected by `FILL_ARROW` lines (`highlight: true` tints a step `#E8F0FE`); shifts the cards below down to `Y=156pt` (`H=219pt`).
* **Optional Bottom Banner (`foundation`)**: Full-width baseline card at `Y=335pt` (`H=40pt`); shortens cards above to `H=225pt`.
* **2-Card Layout**:
  * Card 1: `X=36pt`, `Y=100pt`, `W=312pt`, `H=275pt` (`ROUND_RECTANGLE`, `#FFFFFF` fill, `1pt #DADCE0` border)
  * Card 2: `X=372pt`, `Y=100pt`, `W=312pt`, `H=275pt` (Gutter: `24pt`)
* **3-Card Layout**:
  * Card 1: `X=36pt`, `Y=100pt`, `W=202pt`, `H=275pt`
  * Card 2: `X=254pt`, `Y=100pt`, `W=202pt`, `H=275pt`
  * Card 3: `X=472pt`, `Y=100pt`, `W=202pt`, `H=275pt` (Gutter: `16pt`)
* **Card Interior Geometry**:
  * Top Accent Stripe: `Height=3pt`, 4-color Google cycle (`#1A73E8`, `#EA4335`, `#FBBC04`, `#34A853`) or custom card theme
  * Pill Badge: `X=CardX+16pt`, `Y=116pt`, `W=Auto`, `H=18pt`, tinted fill + WCAG AA text
  * Card Header: `X=CardX+16pt`, `Y=142pt`, `W=CardW-32pt`, `H=24pt`
  * Divider Rule: `X=CardX+16pt`, `Y=172pt`, `W=CardW-32pt`, `H=1pt`, Fill: `#DADCE0`
  * Bullets Box: `X=CardX+16pt`, `Y=182pt`, `W=CardW-32pt`, `H=180pt`

#### Character Capacity & Budget
* `card.title`: Max 35 characters (2-card), Max 25 characters (3-card).
* `card.bullets`: Strictly 3 to 4 bullet points. Max 90 chars per bullet (2-card), Max 65 chars per bullet (3-card).

---

### Archetype 3: `code_terminal`

```
Y=28pt ┌─────────────────────────────────────────────────────────────┐
       │ [KICKER] 10pt Google Sans Bold                              │
Y=40pt │ SLIDE TITLE: 24pt Google Sans Bold                          │
Y=100pt├──────────────────────────────┬──────────────────────────────┤
       │ LEFT COLUMN (Concepts)       │ RIGHT COLUMN (Terminal Box)  │
       │                              │ ┌──────────────────────────┐ │
       │ [WHAT YOU BUILD] (Pill)      │ │ ● ● ●  .agent/hooks/pre  │ │
       │                              │ │ ──────────────────────── │ │
       │ • Deterministic Hooks        │ │ #!/bin/sh                │ │
       │   Block commit on failure    │ │ typecheck && lint        │ │
       │                              │ │ test --bail || exit 1    │ │
       │ • Adversarial Evaluator      │ │                          │ │
       │   Independent subagent       │ │                          │ │
       │                              │ └──────────────────────────┘ │
       │                              │ [✓ DO: RATCHETED]            │
Y=375pt└──────────────────────────────┴──────────────────────────────┘
```

#### Bounding Box & Coordinates
* **Left Column (Context/Bullets)**: `X=36pt`, `Y=100pt`, `W=260pt`, `H=275pt`
* **Right Column (Terminal Box)**: `X=316pt`, `Y=100pt`, `W=368pt`, `H=235pt`
  * Window Top Bar: `X=316pt`, `Y=100pt`, `W=368pt`, `H=24pt`, Fill: `#2D3035`
  * Traffic Light Dots: Red (`#EA4335`), Yellow (`#FBBC04`), Green (`#34A853`) at `X=326pt`, `Y=108pt`
  * Filename Header: `X=360pt`, `Y=104pt`, Font: `Roboto Mono 11pt`, Color: `#BDC1C6`
  * Terminal Body: `X=316pt`, `Y=124pt`, `W=368pt`, `H=211pt`, Fill: `#202124`
  * Monospace Code: `X=328pt`, `Y=134pt`, `W=344pt`, `H=190pt`, Font: `Roboto Mono 10.5pt`
* **Status Badges (Below Terminal)**: `X=316pt`, `Y=344pt`, `W=368pt`, `H=30pt`
  * Do Badge: Fill: `#E6F4EA`, Text: `#137333` (`✓ DO: RATCHETED`)
  * Don't Badge: Fill: `#FCE8E6`, Text: `#C5221F` (`✗ DON'T: HOPE-BASED`)

#### Character Capacity & Budget
* `code`: Max 12 lines of code; max 50 characters per line.
* `left_content.bullets`: 2-3 items with bold lead-ins.

---

### Archetype 4: `hero_metrics` (`hero_metric`)

```
Y=28pt ┌─────────────────────────────────────────────────────────────┐
       │ [KICKER] 10pt Google Sans Bold                              │
Y=40pt │ SLIDE TITLE: 24pt Google Sans Bold                          │
Y=100pt├──────────────────────────────┬──────────────────────────────┤
       │ ┌──────────────────────────┐ │ ┌──────────────────────────┐ │
       │ │ [PILL: SOLO MODEL]       │ │ │ [PILL: FULL HARNESS]     │ │
       │ │ $9                       │ │ │ $200                     │ │
       │ │ · 20 min execution time  │ │ │ · 6 hours execution time │ │
       │ │ ──────────────────────── │ │ │ ──────────────────────── │ │
       │ │ Broken mechanics, failed │ │ │ Functional game engine,  │ │
       │ │ UI. A toy you throw away.│ │ │ rich editors. Shippable. │ │
       │ └──────────────────────────┘ │ └──────────────────────────┘ │
Y=375pt└──────────────────────────────┴──────────────────────────────┘
```

#### Bounding Box & Coordinates
* **Metric Card 1**: `X=36pt`, `Y=100pt`, `W=312pt`, `H=275pt`
* **Metric Card 2**: `X=372pt`, `Y=100pt`, `W=312pt`, `H=275pt`
* **Metric Value**: `X=CardX+20pt`, `Y=140pt`, `W=CardW-40pt`, `H=60pt`, Font: `Google Sans 54pt Bold`
* **Delta Pill**: `X=CardX+20pt`, `Y=116pt`, `W=Auto`, `H=18pt`
* **Divider**: `X=CardX+20pt`, `Y=220pt`, `W=CardW-40pt`, `H=1pt`, Fill: `#DADCE0`
* **Description**: `X=CardX+20pt`, `Y=232pt`, `W=CardW-40pt`, `H=130pt`, Font: `Google Sans Text 12pt`

---

### Archetype 5: `ladder_hierarchy` (`ladder_flow`)

```
Y=28pt ┌─────────────────────────────────────────────────────────────┐
       │ [KICKER] 10pt Google Sans Bold                              │
Y=40pt │ SLIDE TITLE: 24pt Google Sans Bold                          │
Y=100pt├──────────────┬──────────────┬──────────────┬────────────────┤
       │ ┌──────────┐ │ ┌──────────┐ │ ┌──────────┐ │ ┌────────────┐ │
       │ │ [RUNG 1] │→│ │ [RUNG 2] │→│ │ [RUNG 3] │→│ │ [RUNG 4]   │ │
       │ │ Prompt   │ │ │ Context  │ │ │ Harness  │ │ │ Loop       │ │
       │ │ ──────── │ │ │ ──────── │ │ │ ──────── │ │ │ ────────── │ │
       │ │ GCCD     │ │ │ Curate & │ │ │ Tools,   │ │ │ Autonomous │ │
       │ │ specs    │ │ │ compact  │ │ │ hooks    │ │ │ review seat│ │
       │ └──────────┘ │ └──────────┘ │ └──────────┘ │ └────────────┘ │
Y=375pt└──────────────┴──────────────┴──────────────┴────────────────┘
```

#### Bounding Box & Coordinates
* **4 Rungs** across `648pt` usable width (Card Width: `146pt`, Gutter: `21pt`):
  * Rung 1: `X=36pt`, `Y=100pt`, `W=146pt`, `H=275pt`
  * Arrow 1: `X=187pt`, `Y=220pt`, `W=16pt`, `H=20pt`, Text: `→`
  * Rung 2: `X=203pt`, `Y=100pt`, `W=146pt`, `H=275pt`
  * Arrow 2: `X=354pt`, `Y=220pt`, `W=16pt`, `H=20pt`, Text: `→`
  * Rung 3: `X=370pt`, `Y=100pt`, `W=146pt`, `H=275pt`
  * Arrow 3: `X=521pt`, `Y=220pt`, `W=16pt`, `H=20pt`, Text: `→`
  * Rung 4: `X=537pt`, `Y=100pt`, `W=146pt`, `H=275pt`

---

### Archetype 6: `executive_grid` (`exec_grid_2x2` & `exec_grid_2x3`)

```
Y=22pt ┌─────────────────────────────────────────────────────────────┐
       │ [MINI 4-COLOR BAR]  [KICKER]                                │
Y=40pt │ Slide Title: 22pt Google Sans Regular (#202124)             │
Y=100pt├───────────────────┬───────────────────┬─────────────────────┤
       │ ┌───────────────┐ │ ┌───────────────┐ │ ┌─────────────────┐ │
       │ │▀▀▀ [01]       │ │ │▀▀▀ [02]       │ │ │▀▀▀ [03]         │ │
       │ │ Pillar 1      │ │ │ Pillar 2      │ │ │ Pillar 3        │ │
       │ └───────────────┘ │ └───────────────┘ │ └─────────────────┘ │
       │ ┌───────────────┐ │ ┌───────────────┐ │ ┌─────────────────┐ │
       │ │▀▀▀ [04]       │ │ │▀▀▀ [05]       │ │ │▀▀▀ [06]         │ │
       │ │ Pillar 4      │ │ │ Pillar 5      │ │ │ Pillar 6        │ │
       │ └───────────────┘ │ └───────────────┘ │ └─────────────────┘ │
Y=375pt└───────────────────┴───────────────────┴─────────────────────┘
```

#### Bounding Box & Coordinates
* **`2×2` Layout (4 items)**: `W=316pt`, `H=129pt` (`X=36, 368`, `Y=100, 245`)
* **`2×3` Layout (6 items)**: `W=205.3pt`, `H=129pt` (`X=36, 257.3, 478.7`, `Y=100, 245`)
* **Card Styling**: `ROUND_RECTANGLE` white card with `1pt #DADCE0` border, top `3pt` 4-color cycling bar (`#1A73E8`, `#EA4335`, `#FBBC04`, `#34A853`), and matching tinted `01..06` pill badge.

---

### Archetype 7: `dodont_checklist` (`do_dont_checklist`)

```
Y=28pt ┌─────────────────────────────────────────────────────────────┐
       │ [KICKER] 10pt Google Sans Bold                              │
Y=40pt │ SLIDE TITLE: 24pt Google Sans Bold                          │
Y=100pt├──────────────────────────────┬──────────────────────────────┤
       │ ┌──────────────────────────┐ │ ┌──────────────────────────┐ │
       │ │ [✗ DON'T / ANTI-PATTERN] │ │ │ [✓ DO / BLUEPRINT]       │ │
       │ │ • Syntax memorization    │ │ │ • Problem decomposition  │ │
       │ │ • Typing speed           │ │ │ • Architecture judgment  │ │
       │ │ • Hand-written boiler    │ │ │ • Specification clarity  │ │
       │ └──────────────────────────┘ │ └──────────────────────────┘ │
Y=335pt├─────────────────────────────────────────────────────────────┤
Y=345pt│ [SYNTHESIS PILL: Learn the rung first. Let tool automate.]  │
Y=375pt└─────────────────────────────────────────────────────────────┘
```

#### Bounding Box & Coordinates
* **Don't Card (Left)**: `X=36pt`, `Y=100pt`, `W=312pt`, `H=230pt`, Top Header Banner Fill: `#FCE8E6` (`#C5221F` Text)
* **Do Card (Right)**: `X=372pt`, `Y=100pt`, `W=312pt`, `H=230pt`, Top Header Banner Fill: `#E6F4EA` (`#137333` Text)
* **Synthesis Footer Banner**: `X=36pt`, `Y=342pt`, `W=648pt`, `H=32pt`, Fill: `#E8F0FE`, Text: `#174EA6 12pt Bold`

---

### Archetype 8: `actionable_takeaways`

```
Y=28pt ┌─────────────────────────────────────────────────────────────┐
       │ [KICKER] 10pt Google Sans Bold                              │
Y=40pt │ SLIDE TITLE: 24pt Google Sans Bold                          │
Y=100pt├──────────────────────────────────┬──────────────────────────┤
       │ LEFT COLUMN (Action Principles)  │ RIGHT COLUMN (Roadmap)   │
       │                                  │ ┌──────────────────────┐ │
       │ 01 Master Intent First           │ │ [ROADMAP: 30 DAYS]   │ │
       │    Write verifiable done-when.   │ │ 1. Install pre-commit│ │
       │                                  │ │ 2. Shard context     │ │
       │ 02 Build Enforcing Ratchets      │ │ 3. Maker-checker pair│ │
       │    Block regressions in hooks.   │ │ 4. Loop scheduler    │ │
       │                                  │ │ ──────────────────── │ │
       │ 03 Keep Humans in Review Seat    │ │ [START BLUEPRINT]    │ │
       │    Review PRs, not prompts.      │ └──────────────────────┘ │
Y=375pt└──────────────────────────────────┴──────────────────────────┘
```

#### Bounding Box & Coordinates
* **Left Column (Principles)**: `X=36pt`, `Y=100pt`, `W=360pt`, `H=275pt`
  * Principle Item 1: `Y=104pt`, `H=50pt`
  * Principle Item 2: `Y=164pt`, `H=50pt`
  * Principle Item 3: `Y=224pt`, `H=50pt`
* **Right Column (Roadmap Container)**: `X=412pt`, `Y=100pt`, `W=272pt`, `H=275pt`, Fill: `#1E2761`, Rounded Corners (8pt)
  * Roadmap Title: `X=428pt`, `Y=116pt`, Font: `Google Sans 14pt Bold`, Color: `#FFFFFF`
  * 4 Milestone Steps: `Y=146pt, 176pt, 206pt, 236pt`, Font: `Google Sans Text 11pt`, Color: `#CADCFC`
  * CTA Button: `X=428pt`, `Y=316pt`, `W=240pt`, `H=36pt`, Fill: `#1A73E8`, Text: `#FFFFFF 13pt Bold`

---

### Archetype 9: `demo_pivot` (alias `demo`)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ (Navy #1E2761 background)                                                   │
│ Y=92pt  [▶ LIVE DEMO]            (12pt bold white on #C5221F, 150×26)        │
│ Y=130pt Agents fix a bug end to end        (40/32/26pt bold white)          │
│ Y=230pt From ticket to merged PR in four minutes   (16pt #CADCFC)           │
│ Y=288pt WATCH FOR                                   (10pt bold #CADCFC)     │
│ Y=308pt [ Plan step ]  [ Test run ]  [ PR link ]    (3 chips, #2D3A8C)      │
└─────────────────────────────────────────────────────────────────────────────┘
```

* **Use it** right before switching to a live demo. It resets attention and tells the
  audience what to look for.
* `title` of 30 chars or fewer renders at 40pt. 31–55 chars renders at 32pt, and longer text at 26pt.
* `watch_for`: up to 3 chips (208pt wide each), 28 chars or fewer each.
* Exempt from the assertion-subtitle lint.

---

### Archetype 10: `image_split` (aliases `image`, `diagram`)

```
Y=28pt ┌─────────────────────────────────────────────────────────────┐
       │ [KICKER] / TITLE / takeaway subtitle (standard header)       │
Y=100pt├──────────────────────┬──────────────────────────────────────┤
       │ ▌ bullets card       │ ┌──────────────────────────────────┐ │
       │ • Single ingress     │ │                                  │ │
       │ • Regional failover  │ │        diagram / screenshot      │ │
       │ • mTLS end to end    │ │     (aspect ratio preserved)     │ │
       │                      │ │           Figure 2 (caption)     │ │
       │  W=256pt             │ └──────── W=368pt ─────────────────┘ │
Y=375pt└──────────────────────┴──────────────────────────────────────┘
```

* **The escape hatch.** Use it for Mermaid or draw.io diagrams rendered to PNG, product
  screenshots, and charts that no archetype can express.
* `image_layout: split` puts the bullets card (256pt, 4 bullets or fewer) next to a framed image
  panel (368pt) with 8pt padding. `image_side: left|right` controls which side the image is on.
* `image_layout: full` frames the image across the whole content area (648×275pt).
* `image.caption` is optional. It takes a 22pt italic strip inside the frame.
* `image.url` goes through batch `add-image`. `image.path` is uploaded after the batch with
  `gslides mutate insert-image-from-file` and targets the resolved slide ID.
* Export diagrams at about 2× (for example 1600px wide) on a white background so they stay crisp.

---

### Archetype 11: `flow_diagram` (aliases `cycle`, `timeline`, `funnel`, `flow`)

Native, **editable** process diagrams drawn with raw Slides API requests: multi-run
styled text, connector lines glued to shapes (`startConnection`/`endConnection`),
dashed outlines. Use it instead of a PNG when the story is a flow, a loop, or
a "where we are" status, and you want the audience (or the next editor) to be able to
change the shapes.

```
cycle (with 2 foundation stages)                 timeline                     funnel
┌────┐ ┌────┐ ┌──────────────────────────────┐   [WE ARE HERE]                ▶BOAS▶ FIT ▶OFERTA▶ FECH ▶
│▀▀▀▀│ │▀▀▀▀│ │ 03 · LOOP          ┌──────┐  │   ┌───┐ ┌───┐ ┌───┐ ┌───┐       ┌───┐ ┌───┐ ┌───┐ ┌───┐
│kick│→│kick│→│[WE ARE HERE]  ↗    │ node │↘ │   │▀▀▀│→│▀▀▀│→│▀▀▀│→│▀▀▀│       │▀▀▀│ │▀▀▀│ │███│ │▀▀▀│
│titl│ │titl│ │┌─────┐→┌────┐  ↻  ┌────┐   │   │ … │ │ … │ │ … │ │ … │       │ … │ │ … │ │ … │ │ … │
│lead│ │lead│ ││entry│ │node│ text │node│   │   │✓ D│ │● P│ │○ N│ │○ N│       └───┘ └───┘ └───┘ └───┘
│body│ │body│ │└─────┘ └────┘↖    └────┘↙  │   └───┘ └───┘ └───┘ └───┘
│✓ OK│ │✓ OK│ │┆feeder┆      ┌──────┐      │                 note →                         note →
└────┘ └────┘ └──────────────────── note ──┘
```

| Layout | Content | Limits |
|---|---|---|
| `timeline` | `stages[]` → cards (colour bar, kicker, title, lead, body, status chip) joined by arrows | 2–5 stages |
| `cycle` | `cycle.nodes[]` clockwise from the left (left → top → right → bottom), curved connectors, `center` caption, optional `entry` (solid blue) + dashed `feeder`; optional `stages[]` on the left | 3–4 nodes, ≤2 stages |
| `funnel` | `steps[]` → chevron strip (`label`) + a card per step (`title`, `lead`, `body`); `active: N` colours one chevron and tints the rest | 3–6 steps |
| `layered_cake` | `layers[]` (bottom-to-top: `layers[0]` full-width base foundation, `layers[1]` 2–4 middle pillars, `layers[2]` 1–3 top frontier boxes) or `base` / `middle` / `top` keys | 2–4 layers |
| `swimlanes` | `lanes[]` (top-to-bottom horizontal capability bands: left lane label header + 2–5 horizontal rounded cards inside each lane; supports `highlight: true` for `#E37400` co-build outline) | 2–4 lanes, 1–5 cards/lane |

Shared: `marker: {text, at: entry | stage:N | node:N | step:N}` (red pill),
`note` (honesty line, e.g. "Today: X mature · Y in progress"), `label` (section label),
`status: done | active | next | risk` per stage/step, `status_labels` to localise chips,
`color: red | yellow | blue | green | grey` per stage/step (default order red → yellow → blue → green).

* The slide uses the **standard deck header** (kicker/title/subtitle), so it sits in the deck
  like any other archetype. The diagram body occupies y=100–376pt.
* Cards size to their content (top-anchored). Keep each card to kicker + ≤4-word title +
  one lead line + ≤2 body lines; node bodies ≤~35 chars.
* The validator lays out the diagram offline and warns on overflow, pills/chips/labels that
  would wrap, and emoji (stripped at render). `marker.text` ≤ ~30 chars for the cycle entry pill.
* Design tokens: [diagram_tokens.yaml](diagram_tokens.yaml). Raw-request recipe and gotchas:
  [batch_operations.md §7](batch_operations.md#7-native-diagrams-raw-batch).

---

### Archetype 12: `workstream_card` (aliases `initiative_card`, `frente_card`, `workstream`)

```
Y=28pt ┌─────────────────────────────────────────────────────────────────────────┐
       │ [KICKER] / TITLE / takeaway subtitle (standard header)                  │
Y=106pt├───────────────────────────┬─────────────────────┬───────────────────────┤
       │ ┌───────────────────────┐ │ [TEMPO / MATURIDADE]│ [POTENCIAL DE RECEITA]│
       │ │                       │ ├─────────────────────┼───────────────────────┤
       │ │  ESPAÇO PARA IMAGEM   │ │ ▀▀▀▀ (Red #EA4335)  │ ▀▀▀▀ (Green #34A853)  │
       │ │     / DIAGRAMA        │ │ RISCOS & DESAFIOS   │ DIFERENCIAIS GOOGLE   │
       │ │  (ou imagem real)     │ │ • Bullet 1          │ • Bullet 1            │
       │ │                       │ │ • Bullet 2          │ • Bullet 2            │
       │ │                       │ ├─────────────────────┴───────────────────────┤
       │ │                       │ │ ▀▀▀▀▀▀▀▀▀▀▀▀ (Yellow #FBBC04)               │
       │ │       W=220pt         │ │ AÇÕES / O QUE FAZER? (PLANO & EM ABERTO)    │
       │ └───────────────────────┘ │ • Ação 1  • Ação 2  • [Em aberto] Decisão X │
Y=370pt└───────────────────────────┴─────────────────────────────────────────────┘
```

* **Use it** for executive initiative/workstream deep-dive slides where each workstream needs:
  * **Left (`X=36, Y=106, W=220, H=264`):** A framed image (`image: {path | url}`) or a clean grey drop-zone (`image: {placeholder: "Inserir diagrama..."}`).
  * **Right Top (`X=270..684, Y=106, H=40`):** Two KPI pills side by side (`tempo` / `horizon` and `receita` / `revenue`).
  * **Right Middle (`X=270..684, Y=154, H=114`):** Side-by-side comparison of `desafios` (`challenges` / `risks`) vs. `diferenciais` (`differentiators` / `strengths`), up to 3–4 short bullets each.
  * **Right Bottom (`X=270..684, Y=276, H=94`):** Full-width yellow action card (`acoes` / `actions` / `next_steps`) for concrete actions and open questions (`[Em aberto]`).

---

### Archetype 13: `cover` (aliases `title_cover`, `opening`)

* **Canvas Fill**: `#FFFFFF` with top mini 4-color bar (`X=36pt, Y=36pt, W=88pt, H=4pt`).
* **Evolution Breadcrumbs (`breadcrumbs`)**: Optional horizontal pill trail `A → B → [C]` at `Y=104pt`, with the final destination pill highlighted in `#E8F0FE` (`#174EA6` bold text).
* **Editorial Title**: `36–44pt` `Google Sans` Regular (`#202124`) at `Y=144pt`, followed by `15pt` `#5F6368` `subtitle` and bottom-left `date` / confidentiality metadata at `Y=354pt`.
* Exempt from the 4-word assertion-subtitle lint.

---

### Archetype 14: `statement_pivot` (aliases `thesis`, `short_answer`, `provocation`)

* **`variant: "blue"` (default)**: Full-bleed Google Blue (`#1A73E8`) canvas, white-first mini 4-color bar, `#FFFFFF` uppercase kicker, large `28–36pt` white statement headline, and `#E8F0FE` supporting subtitle.
* **`variant: "dark"`**: Full-bleed Google Charcoal (`#202124`) canvas, standard mini 4-color bar, `#FBBC04` uppercase kicker, large `28–36pt` white provocation/question, and `#BDC1C6` subtitle.
* Exempt from the 4-word assertion-subtitle lint.

---

### Archetype 15: `capability_matrix` (aliases `matrix`, `comparison_matrix`)

* **Columns (`columns[]`, 2–4)**: Column headers across `X=216..684pt`, with optional `highlight: "outline"` (`2pt #1A73E8` frame) or `highlight: "solid"` (`#1A73E8` header).
* **Rows (`rows[]`, 2–6)**: Left capability label (`X=36..208pt`) + `ROUND_RECTANGLE` semantic status cells:
  * `native` / `done` (`#E6F4EA` fill, `#137333` text)
  * `partial` / `warn` (`#FEF7E0` fill, `#945200` text)
  * `gap` / `plugin` / `risk` (`#FCE8E6` fill, `#C5221F` text)
  * `building_blocks` / `blocks` / `platform` (`#E8F0FE` fill, `#174EA6` text)
  * Optional `highlight: true` on any cell adds a `1.5pt #E37400` co-build accent border.
* **Footnote (`footnote`)**: Optional bottom synthesis line (`Y=362pt`).

---

### Archetype 16: `kpi_spotlight` (aliases `big_number`, `pilot_spotlight`)

* **Left Spotlight (`X=36..308pt`)**: Rounded `#F8F9FA` spotlight panel with huge `60pt` `#1A73E8` `stat_value`, bold `stat_label`, muted `stat_description`, and optional green `status_pill` (`#E6F4EA` / `#137333`).
* **Right Measurements (`X=336..684pt`)**: Uppercase `measured_by_label` (`MEASURED BY`) + 2–4 leading-indicator rows separated by `1pt #DADCE0` hairline rules, each prefixed with a 4-color `ELLIPSE` dot.

---

### Archetype 17: `horizon_staircase` (aliases `staircase`, `rising_horizons`, `north_star`)

* **2–4 Ascending Cards**: Bottom-aligned at `Y=374pt` with progressively taller heights from left to right (`Agora (Curto Prazo)` → `Médio Prazo` → `Longo Prazo (Futuro)`). Never use ambiguous `H1/H2/H3` labels.
* **North Star Highlight**: Final (or `highlight: true`) horizon uses `#E8F0FE` tint fill with `#AECBFA` border; each card carries a cycling 4-color top bar, horizon pill, title, bullets, and optional bottom human-governance `footer` strip.

---

### Archetype 18: `closing_ask` (aliases `dark_closing`, `the_ask`, `executive_ask`)

* **Canvas Fill**: `#202124` Google Charcoal with top mini 4-color bar, large `28pt` white takeaway `title`, optional `#BDC1C6` `subtitle`, and `#FBBC04` `section_kicker` (`THE ASK` / `DECISÕES`).
* **Decision Columns (`asks[]` / `columns[]`, 2–4)**: Borderless dark columns (`Y=224..365pt`) topped by crisp `2.5pt` colored rules (`#1A73E8`, `#EA4335`, `#FBBC04`, `#34A853`) with bold white headers and `#E8EAED` descriptions.
* Exempt from the 4-word assertion-subtitle lint.

# Blueprint Layout Archetypes Reference Guide

This document provides visual diagrams, coordinate bounding box formulas, field parameters, and character capacity limits for all 10 standardized presentation layout archetypes in the **AI Factory Blueprint** design system.

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
* **2-Card Layout**:
  * Card 1: `X=36pt`, `Y=100pt`, `W=312pt`, `H=275pt`
  * Card 2: `X=372pt`, `Y=100pt`, `W=312pt`, `H=275pt` (Gutter: `24pt`)
* **3-Card Layout**:
  * Card 1: `X=36pt`, `Y=100pt`, `W=202pt`, `H=275pt`
  * Card 2: `X=254pt`, `Y=100pt`, `W=202pt`, `H=275pt`
  * Card 3: `X=472pt`, `Y=100pt`, `W=202pt`, `H=275pt` (Gutter: `16pt`)
* **Card Interior Geometry**:
  * Top Accent Stripe: `Height=3pt`, Fill: `#1A73E8` or custom card theme
  * Pill Badge: `X=CardX+16pt`, `Y=116pt`, `W=Auto`, `H=18pt`, Fill: `#E8F0FE`, Text: `#174EA6`
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

### Archetype 6: `executive_grid` (`exec_grid_2x2`)

```
Y=28pt ┌─────────────────────────────────────────────────────────────┐
       │ [KICKER] 10pt Google Sans Bold                              │
Y=40pt │ SLIDE TITLE: 24pt Google Sans Bold                          │
Y=100pt├──────────────────────────────┬──────────────────────────────┤
       │ ┌─┌────────────────────────┐ │ ┌─┌────────────────────────┐ │
       │ │▌│ 01 PROMPT              │ │ │▌│ 02 CONTEXT             │ │
       │ │▌│ Guide intent with GCCD │ │ │▌│ Curate the window      │ │
       │ └─└────────────────────────┘ │ └─└────────────────────────┘ │
       │ ┌─┌────────────────────────┐ │ ┌─┌────────────────────────┐ │
       │ │▌│ 03 HARNESS             │ │ │▌│ 04 LOOP                │ │
       │ │▌│ Tools, hooks, ratchets │ │ │▌│ Automate the prompter  │ │
       │ └─└────────────────────────┘ │ └─└────────────────────────┘ │
Y=375pt└──────────────────────────────┴──────────────────────────────┘
```

#### Bounding Box & Coordinates
* Card Top-Left (Q1): `X=36pt`, `Y=100pt`, `W=312pt`, `H=128pt`
* Card Top-Right (Q2): `X=372pt`, `Y=100pt`, `W=312pt`, `H=128pt`
* Card Bottom-Left (Q3): `X=36pt`, `Y=244pt`, `W=312pt`, `H=128pt`
* Card Bottom-Right (Q4): `X=372pt`, `Y=244pt`, `W=312pt`, `H=128pt`
* **Accent Strip**: Vertical bar on left edge of each card: `W=4pt`, `H=128pt`, Fill: `#1A73E8`

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

# preso_spec.yaml Specification Manifest Schema Reference

This document defines the schema, field types, validation rules, and character length budgets for the declarative presentation manifest (`preso_spec.yaml`).

---

### 1. Top-Level Schema Structure

```yaml
version: "1.0"

metadata:
  title: string                  # [Required] Main presentation title
  subtitle: string               # [Optional] Subtitle / thesis statement
  template_id: string            # [Optional] Google Slides Master Deck ID (Default: AI Factory Blueprint)
  target_audience: string        # [Optional] Target audience (e.g. "Senior Engineering Leadership")
  core_thesis: string            # [Optional] Core narrative thesis
  theme:
    palette: string              # [Optional] "blueprint" | "dark" | "light"
    primary_color: string        # [Optional] Hex color code (e.g. "#1E2761")
    accent_color: string         # [Optional] Hex color code (e.g. "#1A73E8")

chapters:
  - chapter_number: integer      # [Required] 1-based chapter index (1..99)
    title: string                # [Required] Chapter name
    subtitle: string             # [Optional] Chapter aphorism or thesis
    speaker_notes: string        # [Optional] Notes for the auto divider (missing -> visible TODO)
    include_divider: bool        # [Optional] Auto-insert a chapter_divider (default: true)
    slides:                      # [Required] List of slides in this chapter
      - archetype: string        # [Required] Archetype identifier (see below)
        title: string            # [Required] Slide headline
        subtitle: string         # [Expected] One-sentence takeaway (>= 4 words; lint warns otherwise)
        kicker: string           # [Optional] Small uppercase category tag
        speaker_notes: string    # [Optional] Authored notes; missing -> "TODO: write speaker notes for this slide."
        tier: string             # [Optional] core (default) | explain | detail | appendix
        skip: bool               # [Optional] Build the slide but hide it (skip-slide)
        # Archetype-specific fields...
```

---

### 2. Supported Archetypes & Field Mappings

#### 1. `chapter_divider`
* `chapter_number`: `integer` (1..99)
* `title`: `string` (Max 45 chars)
* `subtitle`: `string` (Max 80 chars)
* `kicker`: `string` (Default: `"CHAPTER"`)
* `speaker_notes`: `string` (Optional)

#### 2. `split_cards` (`card_split_2` / `card_split_3`)
* `cards`: `list[CardSpec]` (Strictly 2 or 3 items)
  * `title` / `header`: `string` (Card heading, max 35 chars)
  * `category` / `category_pill`: `string` (Top pill text, max 20 chars)
  * `bullets`: `list[string]` (Strictly 3 to 4 items; max 90 chars per bullet for 2-card, max 65 chars for 3-card)
  * `theme`: `string` (Optional hex accent color)

#### 3. `code_terminal`
* `left_content` / `context`:
  * `header` / `pill`: `string` (e.g. `"WHAT YOU BUILD"`)
  * `items` / `bullets`: `list[string]` (2-3 bullet items with bold lead-ins)
* `terminals` / `code_box`:
  * `filename`: `string` (e.g. `".agent/hooks/pre-commit"`)
  * `language`: `string` (e.g. `"bash"`, `"python"`, `"yaml"`)
  * `code`: `string` (Max 12 lines, max 50 chars per line)
  * `badge_text`: `string` (e.g. `"✓ DO: RATCHETED"`)
  * `status`: `string` (`"do"` | `"dont"`)

#### 4. `hero_metrics` (`hero_metric`)
* `metrics` / `cards`: `list[HeroMetricSpec]` (Strictly 2 or 3 items)
  * `title` / `label`: `string` (Metric name or condition, e.g. `"SOLO MODEL"`)
  * `value`: `string` (Stat number, e.g. `"$9"`, `"87%"`, `"-85%"`, max 12 chars)
  * `unit`: `string` (Optional unit or duration, e.g. `"· 20 min execution"`)
  * `delta`: `string` (Optional delta indicator, e.g. `"+10x throughput"`)
  * `description` / `context`: `string` (Explanatory narrative, max 100 chars)

#### 5. `ladder_hierarchy` (`ladder_flow`)
* `rungs` / `steps`: `list[LadderStepSpec]` (Strictly 3 or 4 items)
  * `step_number`: `integer` (1..4)
  * `title`: `string` (Rung name, e.g. `"01 Prompt"`, max 25 chars)
  * `subtitle` / `tagline`: `string` (Short summary, max 40 chars)
  * `bullets` / `details`: `list[string]` (1-2 descriptive points)

#### 6. `executive_grid` (`exec_grid_2x2`)
* `quadrants` / `grid`: `list[QuadrantSpec]` (Strictly 4 items)
  * `quadrant_number`: `integer` (1..4)
  * `kicker`: `string` (e.g. `"01 PROMPT"`)
  * `header` / `title`: `string` (Takeaway summary, max 35 chars)
  * `body` / `description`: `string` (Narrative body, max 110 chars)

#### 7. `dodont_checklist` (`do_dont_checklist`)
* `dont_card` / `anti_pattern`:
  * `title`: `string` (Default: `"DEPRECATED / ANTI-PATTERN"`)
  * `items`: `list[string]` (3-4 negative practices, max 60 chars each)
* `do_card` / `blueprint_standard`:
  * `title`: `string` (Default: `"HIGH-LEVERAGE / BLUEPRINT"`)
  * `items`: `list[string]` (3-4 positive practices, max 60 chars each)
* `synthesis_footer` / `takeaway`: `string` (Full-width summary banner, max 90 chars)

#### 8. `actionable_takeaways`
* `principles` / `action_items`: `list[PrincipleSpec]` (Strictly 3 items)
  * `number`: `integer` (1..3)
  * `title`: `string` (Action principle, max 35 chars)
  * `description`: `string` (How to execute, max 100 chars)
* `roadmap`:
  * `title`: `string` (e.g. `"30-DAY EXECUTION ROADMAP"`)
  * `milestones` / `steps`: `list[string]` (4 weekly milestone items)
  * `cta_button_text`: `string` (e.g. `"START THE FACTORY"`)

#### 9. `demo_pivot` (alias `demo`)
* `title`: `string` (What the demo proves; 30 chars or fewer renders at 40pt, longer text steps down to 32/26pt)
* `subtitle`: `string` (Optional one-liner)
* `kicker`: `string` (Default `"LIVE DEMO"`, rendered as `▶ LIVE DEMO`)
* `watch_for`: `list[string]` (Up to 3 chips, 28 chars or fewer each)

#### 10. `image_split` (aliases `image`, `diagram`)
* `image`: `{path | url, alt, caption}` (Required. `path` resolves relative to the spec file and is uploaded after the batch. `url` goes through batch `add-image`.)
* `bullets`: `list[string]` (Up to 4, used only when `image_layout: split`)
* `image_side`: `left` | `right` (default `right`)
* `image_layout`: `split` (bullets card + image) | `full` (image across the content area)

---

### 3. Tiers & Duration Cuts

| Tier | Visible at `--duration` | Typical content |
| :--- | :--- | :--- |
| `core` (default) | 5, 15, 45, full | The storyline: thesis, key proof, ask |
| `explain` | 15, 45, full | Mechanics, "how it works" |
| `detail` | 45, full | Deep dives, code, edge cases |
| `appendix` | never (always hidden) | Backup slides for Q&A |

Hidden slides are still built, then marked with `skip-slide`, so presenters can
unhide them in Slides. An auto chapter divider is hidden when every slide in its
chapter is hidden.

---

### 4. Fit, Budgets & Lints

- **Geometry is authoritative.** `preso build` (and `SpecValidator.validate(spec, geometry=True)`)
  compiles the spec and reports `Geometry fit in '<element>' … (cut ~N chars; capacity ~M)`.
  Run `preso budgets` for current per-slot capacities. For example, the one-line subtitle
  holds about 94 chars, a 3-card title about 19, a 2-card title about 32, and a hero value about 5 (3 metrics) or 9 (2 metrics).
- **Hard errors (block the build):** unknown archetype or tier, missing required archetype
  content, and per-field budget overruns (strict mode).
- **Warnings:** missing or TODO notes, a subtitle under 4 words, citation artifacts
  (`[cite…]`, `[1]`, `[source]`, `(see doc)`, `【n】`), more than 2 consecutive slides with the same
  archetype, and geometry fit.

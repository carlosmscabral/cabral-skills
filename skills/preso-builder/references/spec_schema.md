# preso_spec.yaml Specification Manifest Schema Reference

This document defines the schema, field types, validation rules, and character length budgets for the declarative presentation manifest (`preso_spec.yaml`).

---

### 1. Top-Level Schema Structure

```yaml
version: "1.0"

metadata:
  title: string                  # [Required] Main presentation title
  subtitle: string               # [Optional] Deck subtitle
  template_id: string            # [Optional] Master Deck ID to clone (Default: "" -> clean blank deck)
  target_audience: string        # [Optional] Target audience (e.g. "Senior Engineering Leadership")
  core_thesis: string            # [Optional] Optional deck summary metadata
  theme:
    palette: string              # [Optional] "google_editorial" (default) | "dark" | "light"
    primary_color: string        # [Optional] Hex color code (default "#202124")
    accent_color: string         # [Optional] Hex color code (default "#1A73E8")

chapters:
  - chapter_number: integer      # [Required] 1-based chapter index (1..99)
    title: string                # [Required] Chapter name
    subtitle: string             # [Optional] Chapter subtitle
    speaker_notes: string        # [Optional] Notes for the auto divider (none written if absent)
    include_divider: bool        # [Optional] Auto-insert a chapter_divider (default: true)
    slides:                      # [Required] List of slides in this chapter
      - archetype: string        # [Required] Archetype identifier (see below)
        title: string            # [Required] Slide headline
        subtitle: string         # [Optional] Supporting subtitle or framing line (<= 94 chars)
        kicker: string           # [Optional] Small uppercase category tag
        speaker_notes: string    # [Optional] Authored notes; none written if absent
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
* `flow_steps` / `process_strip`: `list[{title, subtitle, highlight}]` (Optional; 2–5 horizontal process steps connected by arrows above the cards)
* `foundation`: `string | {category, title, description | bullets}` (Optional; full-width baseline card below the cards)
* `cards`: `list[CardSpec]` (Strictly 2 or 3 items)
  * `title` / `header`: `string` (Card heading, max 35 chars)
  * `category` / `category_pill`: `string` (Top pill text, max 20 chars)
  * `bullets`: `list[string]` (Strictly 2 to 4 items; max 90 chars per bullet for 2-card, max 65 chars per bullet for 3-card)
  * `theme`: `string` (Optional hex accent color; defaults to 4-color Google cycle)

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

#### 6. `executive_grid` (`exec_grid_2x2` / `exec_grid_2x3`)
* `quadrants` / `items` / `pillars` / `grid`: `list[QuadrantSpec]` (Strictly **4** (`2×2`) or **6** (`2×3`) items)
  * `number` / `quadrant_number`: `integer` (1..6)
  * `kicker`: `string` (Optional pill override, e.g. `"01"`)
  * `header` / `title`: `string` (Takeaway summary, max 35 chars)
  * `body` / `description`: `string` (Narrative body, max 110 chars)

#### 7. `dodont_checklist` (`do_dont_checklist`)
* `dont_title`: `string` (Default: `"DEPRECATED / ANTI-PATTERN"`)
* `dont_items`: `list[string]` (3–4 negative practices, max 60 chars each)
* `do_title`: `string` (Default: `"HIGH-LEVERAGE / BLUEPRINT"`)
* `do_items`: `list[string]` (3–4 positive practices, max 60 chars each)
* `takeaway`: `string` (Full-width summary banner, max 90 chars)

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
* `image`: `{path | url | placeholder, alt, caption}` (Required. `path` resolves relative to the spec file and is uploaded in parallel after the batch. `url` goes through batch `add-image`. `placeholder` draws a grey drop-zone rectangle with no external file needed.)
* `bullets`: `list[string]` (Up to 4, used only when `image_layout: split`)
* `image_side`: `left` | `right` (default `right`)
* `image_layout`: `split` (bullets card + image) | `full` (image across the content area)

#### 11. `flow_diagram` (aliases `cycle`, `timeline`, `funnel`, `layered_cake`, `cake`, `swimlanes`, `swimlane`, `layers_swimlane`, `architecture_layers`, `flow`)
* `diagram`: required block.
  * `layout`: `timeline` | `cycle` | `funnel` | `layered_cake` | `swimlanes` (optional; inferred from the alias or from which of `lanes` / `layers` / `base` / `steps` / `cycle` / `stages` is present)
  * `label`: section label above the stages/steps (optional)
  * `stages[]`: `{kicker, title, lead, body (string | list), status, status_label, color}` — timeline cards, or ≤2 foundation cards left of a cycle
  * `cycle`: `{label, entry: {title, body}, feeder: {title, body}, nodes: [{title, body}] (3–4, clockwise from left), center: {icon, text}}`
  * `steps[]`: `{label (chevron), title, lead, body, status, color}`; `active`: 1-based step to highlight
  * `layers[]`: list of 2–4 tiers ordered **bottom-to-top** (`layers[0]` = base foundation, `layers[1]` = middle workstreams, `layers[2]` = top frontier). Each tier is a list of box dicts `[{kicker, title, body, color, fill}]` (or a single box dict). Also accepts top-level `base:`, `middle:`, `top:` keys.
  * `lanes[]`: list of 2–4 horizontal capability swimlanes ordered **top-to-bottom**: `{label, sublabel, color, items: [{title, body, status, highlight}]}` (`highlight: true` draws a `1.5pt #E37400` co-build accent border).
  * `marker`: `{text, at: entry | stage:N | node:N | step:N}` (or a plain string)
  * `note`: one-line honesty note under the diagram
  * `status_labels`: `{done, active, next, risk}` overrides (e.g. `{done: "✓ Concluído"}`)

#### 12. `workstream_card` (aliases `initiative_card`, `frente_card`, `workstream`)
* `image`: `{path | url | placeholder, alt}` (Optional; defaults to a grey drop-zone on the left `X=36, W=220, H=264`)
* `tempo` / `horizon` / `maturity`: `string` (Top-left KPI pill text, e.g. `"Agora (Curto Prazo) · Em Escala"`)
* `receita` / `revenue`: `string` (Top-right KPI pill text, e.g. `"Alto · Expansão de Seats"`)
* `desafios` / `challenges` / `risks`: `list[string]` (3–4 concise bullets for the red-striped middle-left card)
* `diferenciais` / `differentiators` / `strengths`: `list[string]` (3–4 concise bullets for the green-striped middle-right card)
* `acoes` / `actions` / `next_steps`: `list[string]` (3–4 concise bullets for the bottom full-width yellow action & open-questions card)

#### 13. `cover` (aliases `title_cover`, `opening`)
* `kicker`: `string` (Optional, max 30 chars)
* `title`: `string` (Required editorial headline)
* `subtitle`: `string` (Optional framing subtitle)
* `breadcrumbs` / `evolution`: `list[string]` (Optional 2–4 evolution pills rendered as `A → B → [C]`)
* `date` / `context`: `string` (Optional bottom-left metadata line)

#### 14. `statement_pivot` (aliases `thesis`, `short_answer`, `provocation`)
* `variant`: `"blue"` (`#1A73E8`, default) | `"dark"` (`#202124`)
* `kicker`: `string` (Optional uppercase label, max 30 chars)
* `title`: `string` (Required statement or executive question)
* `subtitle`: `string` (Optional supporting sentence)

#### 15. `capability_matrix` (aliases `matrix`, `comparison_matrix`)
* `columns`: `list[string | {title, subtitle, highlight}]` (2–4 columns; `highlight`: `"outline"` | `"solid"`)
* `rows`: `list[{capability, sublabel, cells: list[string | {text, status, highlight}]}]` (2–6 rows; `status`: `native` | `done` | `partial` | `warn` | `gap` | `plugin` | `risk` | `building_blocks` | `blocks` | `platform`; `highlight: true` adds `#E37400` co-build border)
* `footnote`: `string` (Optional bottom synthesis note)

#### 16. `kpi_spotlight` (aliases `big_number`, `pilot_spotlight`)
* `stat_value` / `value`: `string` (Required hero stat, e.g. `"85%"`, `"3.2x"`)
* `stat_label` / `label`: `string` (Bold metric headline)
* `stat_description` / `description`: `string` (Context under hero stat)
* `status_pill`: `string` (Optional green status pill, e.g. `"EM PRODUÇÃO"`)
* `measured_by_label`: `string` (Default `"MEASURED BY"`)
* `measurements` / `items`: `list[{title, description}]` (2–4 right-column measurement rows)

#### 17. `horizon_staircase` (aliases `staircase`, `rising_horizons`, `north_star`)
* `horizons` / `steps`: `list[{horizon, title, bullets: list[string], footer, highlight}]` (2–4 ascending horizons; use self-explanatory labels `Agora (Curto Prazo)`, `Médio Prazo`, `Longo Prazo (Futuro)` — validator warns on ambiguous `H1..H4`)

#### 18. `closing_ask` (aliases `dark_closing`, `the_ask`, `executive_ask`)
* `title`: `string` (Required closing takeaway headline)
* `subtitle`: `string` (Optional supporting line)
* `section_kicker`: `string` (Default `"THE ASK"`)
* `asks` / `columns` / `items`: `list[{title, description}]` (2–4 borderless decision columns under colored rules)

```yaml
- archetype: cycle
  kicker: QUALITY PROGRAM
  title: "Where we are: from listening to continuous improvement"
  subtitle: Strategy comes from real conversations, becomes tests and improves in short loops
  diagram:
    label: Foundation
    stages:
      - {kicker: "01 · DIAGNOSE", title: Reference calls, lead: 800 calls reviewed, body: "Signals, objections, what top agents do.", status: done, color: red}
      - {kicker: "02 · STRATEGY", title: Conversation playbook, lead: Framework + rules, body: "Welcome → Fit → Offer → Close.", status: done, color: yellow}
    cycle:
      label: "03 · Continuous validation loop"
      entry: {title: Write tests, body: "personas, scenarios\nand criteria"}
      feeder: {title: New capability, body: needs new tests}
      nodes:
        - {title: Run tests, body: full suite incl. regression}
        - {title: Analyse results, body: where it fails and why}
        - {title: Adjust the agent, body: instructions · rules · tools}
        - {title: Re-test, body: confirm before moving on}
      center: {text: each turn brings the agent closer to the strategy}
    marker: {text: "WE ARE HERE · first loops", at: entry}
    note: "Today: transactional checks mature · strategy tests in progress"
```

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
- **Warnings:** citation artifacts (`[cite…]`, `[1]`, `[source]`, `(see doc)`, `【n】`), more than 2 consecutive slides with the same archetype, ambiguous horizon labels (`H1..H4`), and geometry fit.

# User Guide: The AI Factory Presentation Builder (`preso-builder`)

An automated tool and agent skill to generate executive-ready, beautifully styled Google Slides presentations from codebases, markdown docs, existing decks, or text prompts.

---

## 1. Prerequisites & Setup

Before running the tool, make sure you have:

1. **Python 3.10+** with `pyyaml` and `requests`:
   ```bash
   pip install pyyaml requests
   ```
2. **Google Slides CLI (`gslides`)**:
   - Location: `/google/bin/releases/gemini-agents-gslides/gslides`
   - Authentication is handled automatically via standard Google SSO/LOAS credentials.

---

## 2. How to Use It

You can use `preso-builder` in two ways: **conversing with your coding agent** or **running the CLI directly**.

### Option A: Conversing with your agent (Simplest)
Just prompt your agent directly. The skill triggers automatically:

- *"Generate an executive slide deck for the repository at `/path/to/my-repo`"*
- *"Convert `docs/architecture.md` into a Google Slides presentation"*
- *"Restyle this Google Slides deck `1FJ4wCMD...` using the AI Factory Blueprint style"*
- *"Create a 5-slide executive briefing on our new caching architecture"*

The agent will ingest your sources, scaffold the presentation spec, verify the layout, and compile the final Google Slides deck for you.

---

### Option B: Using the CLI (`preso.py`)

The standard workflow is 4 simple steps:

```
  1. INGEST / SCAFFOLD        2. PREVIEW LOCALLY          3. BUILD TO GOOGLE SLIDES
┌───────────────────────┐   ┌───────────────────────┐   ┌───────────────────────────┐
│ python3 preso.py      │   │ python3 preso.py      │   │ python3 preso.py          │
│   ingest --repo .     │──▶│   preview             │──▶│   build                   │
│   (generates spec)    │   │   (opens in browser)  │   │   (returns Slides URL)    │
└───────────────────────┘   └───────────────────────┘   └───────────────────────────┘
```

---

## 3. Practical Examples by Use Case

### Example 1: Create a Presentation from a Codebase / Repo
Scans your directory structure, parses key classes, functions, and configuration files, and outputs a structured presentation manifest.

```bash
# 1. Ingest repository into preso_spec.yaml
python3 preso.py ingest --repo /path/to/my-project --output preso_spec.yaml

# 2. Preview the slides locally in your browser
python3 preso.py preview --spec preso_spec.yaml

# 3. Build the Google Slides presentation
python3 preso.py build --spec preso_spec.yaml
```
Output:
```
🎉 Build Complete!
   Presentation ID: 1CQ0dYkyNpTTsqjsrZay0fB0mTCD66IyChkZlbvISO0k
   Google Slides URL: https://docs.google.com/presentation/d/1CQ0dYkyNpTTsqjsrZay0fB0mTCD66IyChkZlbvISO0k/edit
```

---

### Example 2: Create a Presentation from a Markdown Doc or RFC
Converts headings, lists, code fences, and tables from a technical document into slides.

```bash
# 1. Ingest Markdown document
python3 preso.py ingest --markdown docs/design_doc.md --output preso_spec.yaml

# 2. Preview HTML mockups
python3 preso.py preview --spec preso_spec.yaml

# 3. Compile to Google Slides
python3 preso.py build --spec preso_spec.yaml
```

---

### Example 3: Restyle an Existing Google Slides Deck
Ingests slides from an existing deck and restyles them into clean, high-contrast Blueprint layouts.

```bash
# 1. Ingest existing deck by ID
python3 preso.py ingest --slides <EXISTING_DECK_ID> --output preso_spec.yaml

# 2. Review & build the new polished deck
python3 preso.py build --spec preso_spec.yaml
```

---

### Example 4: Scaffold a New Presentation from Scratch
Quickly generate a presentation template from pre-built presets:

```bash
# Choose from: executive_briefing, product_launch, ai_factory, or minimal
python3 preso.py spec --preset executive_briefing --title "Q3 Platform Strategy" --output preso_spec.yaml

# Or use interactive mode to enter title and details
python3 preso.py spec --interactive

# Preview and build
python3 preso.py preview --spec preso_spec.yaml
python3 preso.py build --spec preso_spec.yaml
```

---

## 4. Slide Types (Archetypes) at a Glance

When editing or creating slides in `preso_spec.yaml`, you can choose from 8 slide layouts:

| Archetype | Best Used For | What It Looks Like |
|---|---|---|
| `chapter_divider` | Section breaks, agenda transitions | Full navy background, large chapter number & title |
| `split_cards` | Architecture comparisons, Before vs. After | 2 or 3 white cards side-by-side with bullets |
| `code_terminal` | Code snippets, configurations, hooks | Dark terminal box with macOS dots & Do/Don't badge |
| `hero_metrics` | Performance stats, ROI, cost savings | Huge 54pt metric numbers with `+10x` / `-85%` delta pills |
| `ladder_hierarchy` | Maturity models, phased roadmaps | 4-step horizontal pipeline connected with chevrons (`→`) |
| `executive_grid` | Core pillars, 4-point executive summary | 2x2 grid of cards with blue accent indicators |
| `dodont_checklist` | Best practices, anti-patterns vs. standards | Side-by-side Red DON'T vs. Green DO checklist |
| `actionable_takeaways` | Closing slide, immediate next steps | 3 key principles on left + dark 30-day roadmap on right |

---

## 5. Sample Presentation Spec (`preso_spec.yaml`)

Here is a short, realistic example of what a `preso_spec.yaml` file looks like:

```yaml
version: "1.0"

metadata:
  title: "Autonomous Testing Platform"
  subtitle: "Accelerating Engineering Velocity"
  target_audience: "Engineering Leadership"
  core_thesis: "Move from manual test runs to automated verification pipelines."

chapters:
  - chapter_number: 1
    title: "Overview & Impact"
    subtitle: "Why automated verification matters"
    slides:
      - archetype: "chapter_divider"
        title: "Overview & Impact"
        subtitle: "Why automated verification matters"
        kicker: "CHAPTER"
        chapter_number: 1
        speaker_notes: "Welcome everyone. Today we are introducing our new testing platform."

      - archetype: "hero_metrics"
        title: "Platform Performance Highlights"
        subtitle: "Impact measured across 50 production microservices"
        kicker: "METRICS"
        hero_metrics:
          - value: "-85%"
            unit: "Defect Rate"
            delta: "-85% bugs"
            delta_type: "positive"
            description: "Automated pre-commit hooks caught regressions before production."
          - value: "10x"
            unit: "Velocity"
            delta: "+10x faster"
            delta_type: "positive"
            description: "Test execution time dropped from 45 minutes to 4.5 minutes."
        speaker_notes: "These two numbers highlight our biggest wins: an 85% drop in defects and a 10x boost in velocity."

      - archetype: "split_cards"
        title: "Traditional vs. Platform Workflow"
        subtitle: "Key differences in developer experience"
        kicker: "COMPARISON"
        cards:
          - title: "Manual Process"
            category_pill: "BEFORE"
            bullets:
              - "Slow, manual regression testing"
              - "Flaky environments blocking releases"
              - "Low confidence during deployments"
          - title: "Automated Platform"
            category_pill: "AFTER"
            bullets:
              - "Single-command verified test runs"
              - "Isolated hermetic test sandboxes"
              - "Continuous automated gating"
        speaker_notes: "On the left is where we were. On the right is the new automated standard."

      - archetype: "actionable_takeaways"
        title: "Rollout Plan & Next Steps"
        subtitle: "Immediate schedule for team onboarding"
        kicker: "NEXT STEPS"
        principles:
          - number: 1
            title: "Enable Pre-Commit Hooks"
            description: "Add automated lint and format checks to all active repositories."
          - number: 2
            title: "Migrate CI Pipelines"
            description: "Switch legacy Jenkins jobs to the new containerized test runners."
          - number: 3
            title: "Monitor Quality Metrics"
            description: "Review automated test health reports during weekly sprint syncs."
        takeaway:
          roadmap_header: "30-Day Roadmap"
          milestones:
            - "Week 1: Pilot with core infrastructure team"
            - "Week 2: Deploy pre-commit hooks repo-wide"
            - "Week 3: Migrate backend service pipelines"
            - "Week 4: Full team onboarding and review"
          cta_text: "GET STARTED →"
        speaker_notes: "Here is our 30-day adoption plan. We will begin rollout with the core infrastructure team next week."
```

---

## 6. Helpful Tips & Flags

- **Test Without Making API Calls (`--dry-run`)**:
  ```bash
  python3 preso.py build --spec preso_spec.yaml --dry-run
  ```
  Validates your entire presentation and compiles the batch JSON without calling Google Slides.

- **Check Outline & Speaker Notes (`inspect`)**:
  ```bash
  python3 preso.py inspect --spec preso_spec.yaml
  ```
  Prints a clean slide-by-slide summary of your deck directly in your terminal.

- **Run Automated Visual QA (`qa`)**:
  ```bash
  python3 preso.py qa --spec preso_spec.yaml
  ```
  Checks that text fits within cards, contrast is sharp, and every slide has speaker notes.

- **Speaker Notes Rule**:
  Every slide must include `speaker_notes:` (at least 15 characters). This ensures presentations are presenter-ready.

- **Keep Text Concise**:
  To look executive and avoid text cramping:
  - Bullet points: 1–2 lines each (max 3–4 bullets per card).
  - Code snippets: 8–12 lines max.
  - Slide titles: Short 1-liners.

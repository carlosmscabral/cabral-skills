"""Comprehensive Unit Tests for Markdown & Raw Notes Ingestion (Milestone M4).

Tests:
1. YAML frontmatter metadata parsing (title, subtitle, core thesis, audience).
2. Document hierarchy mapping (# -> Title, ## -> Chapter, ### -> Slide, #### -> Card).
3. Code fence parsing with syntax and filename header extraction -> Code Terminal archetype.
4. Markdown table parsing -> Split Comparison Cards archetype.
5. Bullet points & subheadings -> Split Comparison Cards (2-Card and 3-Card).
6. Do / Don't sections and best practice markers -> Do/Don't Checklist archetype.
7. 4 sequential numbered steps -> Ladder / Stepped Hierarchy archetype.
8. 4-quadrant pillars -> Executive Grid archetype.
9. Stat numbers & economics -> Hero Metric Comparison archetype.
10. Key principles and closing roadmap -> Actionable Takeaways archetype.
11. Speaker notes extraction (authored notes only; never synthesized).
12. Multi-chapter document ingestion from both string and file paths.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from preso.ingest.markdown import MarkdownIngestor, RawSection
from preso.spec.models import PresentationSpec, SlideSpec


class TestMarkdownIngestion(unittest.TestCase):
    """Test suite for MarkdownIngestor."""

    def test_frontmatter_and_heading_metadata(self) -> None:
        """Verifies YAML frontmatter metadata and top-level header extraction."""
        doc = """---
title: "Building the AI Factory"
subtitle: "A Developer's Playbook for the Agentic Era"
core_thesis: "Move from manual hand-prompting to deterministic agentic manufacturing pipelines."
target_audience: "Executive Leadership & Senior Staff Engineers"
---

# Building the AI Factory

## Chapter 1: Foundation & Architecture

### Two Paradigms of Development
#### Traditional Ad-Hoc
- Manual copy-pasting of context into browser UI
- Silent model regressions with zero test harness
#### AI Factory Harness
- Automated context injection via file mounts
- Enforcing pre-commit gates blocking bad code
"""

        ingestor = MarkdownIngestor()
        spec = ingestor.ingest(doc)

        self.assertIsInstance(spec, PresentationSpec)
        self.assertEqual(spec.metadata.title, "Building the AI Factory")
        self.assertEqual(spec.metadata.subtitle, "A Developer's Playbook for the Agentic Era")
        self.assertEqual(spec.metadata.target_audience, "Executive Leadership & Senior Staff Engineers")
        self.assertIn("deterministic agentic manufacturing", spec.metadata.core_thesis)

        self.assertEqual(len(spec.chapters), 1)
        self.assertEqual(len(spec.chapters[0].slides), 2)
        self.assertEqual(spec.chapters[0].slides[0].archetype, "chapter_divider")
        self.assertEqual(spec.chapters[0].slides[1].archetype, "split_cards")

    def test_comprehensive_8_archetype_markdown_document(self) -> None:
        """Tests parsing a comprehensive Markdown document triggering all 8 Blueprint archetypes."""
        full_doc = """# The AI Factory Blueprint Playbook

## Chapter 1: Architecture & Foundations

### Two Paradigms of Agent Development
#### Traditional Prompting
- Manual copy-pasting of context
- Unpredictable model regressions
- Zero test harness or evaluation loop
#### AI Factory Model
- Automated context injection via mounted trees
- Enforcing hooks that block commits on failure
- Adversarial evaluator sub-agents grade runs
> **Speaker Notes:** On this slide we contrast traditional ad-hoc prompting against deterministic AI factory pipelines. Discipline compounds across iterations.

### The Enforcing Ratchet in Practice
Make failures impossible to repeat with pre-commit hooks
```bash .agent/hooks/pre-commit
#!/bin/sh
typecheck && lint
test --bail || exit 1
```
<!-- Notes: Here is the concrete bash ratchet implementation. The agent cannot commit code unless every typecheck and unit test passes cleanly. -->

### The Economics of Skipping Basics
Harness investment vs token waste in real experiments
- **$9** · 20 min - Solo model prototype with broken physics and wasted UI
- **$200** · 6 hours - Shippable enterprise engine with full test suite
> **Speaker Notes:** Review these economic figures. Spending 9 dollars yields a discarded toy, whereas 200 dollars in a rich harness delivers shippable software.

## Chapter 2: Disciplines & Operational Grid

### The Four Disciplines of Agentic Engineering
Master each rung sequentially before adopting frameworks
1. Prompt Engineering: GCCD framework for intent
2. Context Architecture: Compact, offload, and persist memory
3. Harness & Ratchet: Sandboxes and enforcing pre-commit hooks
4. Loop Engineering: Scheduled prompters with human review gates
*Notes:* We structure engineering into four sequential disciplines: Prompt, Context, Harness, and Loop. Each discipline builds directly upon the previous rung.

### Core Architectural Pillars in One Line Each
Executive summary of the four foundational operating pillars
#### Prompt
Guide intent with Goal, Context, Constraints, and Done-when.
#### Context
Curate the context window: compact, offload, reset, and persist.
#### Harness
Equip sandbox state, execution tools, hooks, and evaluators.
#### Loop
Automate the prompter while keeping human judgment in review.
> **Speaker Notes:** Here is the executive four quadrant summary. Each pillar operates independently with distinct engineering responsibilities.

### Architecture Tradeoff Matrix
| Dimension | Ad-Hoc Prompting | AI Factory Blueprint |
| Verification | Manual inspection | Automated pre-commit hooks |
| Context Management | Ephemeral in-memory | Persistent mounted file trees |
| Regressions | Silent failures recur | Ratcheted rules block repeating mistakes |
| Scalability | Bottlenecked by human | Autonomous parallel sub-agents |

## Chapter 3: Standards & Execution

### Agentic Tool Adoption: Do's and Don'ts
Operationalize what you learned rather than bypassing disciplines
#### DO
- Define verifiable done-when criteria before runs
- Isolate parallel agent tasks in separate worktrees
- Employ independent adversarial checker sub-agents
#### DON'T
- Fanning out vague prompts to 20 models at once
- Letting autonomous loops merge code with no review
- Relying on random retries instead of ratchets
> **Speaker Notes:** Review our checklist of recommended standards against common anti-patterns when adopting agentic tooling across engineering teams.

### Actionable Takeaways & Next Steps
Key takeaways and next steps for engineering leaders
> **Speaker Notes:** To conclude our presentation, we summarize the three core principles and outline the immediate three-phase delivery roadmap.
"""

        ingestor = MarkdownIngestor()
        spec = ingestor.ingest(full_doc)

        self.assertIsInstance(spec, PresentationSpec)
        self.assertEqual(len(spec.chapters), 3)

        all_slides = [s for ch in spec.chapters for s in ch.slides]
        archetypes = [s.archetype for s in all_slides]

        # Verify presence of all 8 archetypes across the presentation
        self.assertIn("chapter_divider", archetypes)
        self.assertIn("split_cards", archetypes)
        self.assertIn("code_terminal", archetypes)
        self.assertIn("hero_metrics", archetypes)
        self.assertIn("ladder_hierarchy", archetypes)
        self.assertIn("executive_grid", archetypes)
        self.assertIn("dodont_checklist", archetypes)
        self.assertIn("actionable_takeaways", archetypes)

        # Authored notes are extracted verbatim; nothing is synthesized for the rest
        all_notes = [slide.notes or slide.speaker_notes or "" for slide in all_slides]
        self.assertTrue(any("deterministic AI factory pipelines" in n for n in all_notes))
        self.assertFalse(any("On this slide focusing on" in n for n in all_notes))

    def test_ingest_from_markdown_file(self) -> None:
        """Verifies ingestion from a temporary Markdown file on disk."""
        content = """# Automated Slide Generator Doc

## Chapter 1: Overview

### System Architecture
#### Ingest Module
- Scans repositories and markdown
- Parses AST symbols and signatures
#### Compiler Module
- Generates single-pass batch JSON
- Enforces deterministic geometry
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            temp_file = f.name

        try:
            ingestor = MarkdownIngestor()
            spec = ingestor.ingest(temp_file)
            self.assertIsInstance(spec, PresentationSpec)
            self.assertEqual(spec.metadata.title, "Automated Slide Generator Doc")
            self.assertEqual(len(spec.chapters), 1)
            self.assertEqual(spec.chapters[0].slides[1].archetype, "split_cards")
        finally:
            Path(temp_file).unlink(missing_ok=True)

    def test_single_section_markdown_generates_valid_spec(self) -> None:
        """Verifies that a simple markdown snippet without chapters produces a valid spec."""
        simple_doc = """# Quick Overview
A concise briefing on system capabilities.

- High performance batch compilation
- WCAG AA color contrast enforcement
- Speaker notes generation
"""
        ingestor = MarkdownIngestor()
        spec = ingestor.ingest(simple_doc)

        self.assertIsInstance(spec, PresentationSpec)
        self.assertEqual(len(spec.chapters), 1)
        self.assertGreaterEqual(len(spec.chapters[0].slides), 2)
        self.assertEqual(spec.chapters[0].slides[0].archetype, "chapter_divider")

    def test_invalid_source_raises_error(self) -> None:
        """Verifies error handling for missing or invalid markdown sources."""
        ingestor = MarkdownIngestor()
        with self.assertRaises(ValueError):
            ingestor.ingest(None)

        with self.assertRaises(TypeError):
            ingestor.ingest(12345)  # type: ignore


if __name__ == "__main__":
    unittest.main()

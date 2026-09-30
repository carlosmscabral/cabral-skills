"""Comprehensive Unit Tests for Google Slides Presentation Ingestion (Milestone M4).

Tests:
1. Parsing raw text output from `gslides read-all <deck_id>`.
2. Parsing JSON structures from `gslides read-all --json` / API representations.
3. Heuristic classification into all 8 AI Factory Blueprint archetypes:
   - Chapter Divider
   - Split Comparison Cards (2-Card and 3-Card)
   - Code / Ratchet Terminal Box
   - Hero Metric / Economics Comparison
   - Ladder / Stepped Hierarchy
   - Executive 1-Liner Grid (2x2)
   - Do / Don't Best Practice Checklist
   - Actionable Takeaways & Closing Roadmap
4. Speaker notes pass-through (optional; never synthesized).
5. PresentationSpec hierarchy and chapter grouping.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from preso.ingest.slides import SlidesIngestor
from preso.spec.models import PresentationSpec, SlideSpec


class TestSlidesIngestion(unittest.TestCase):
    """Test suite for SlidesIngestor."""

    def test_parse_read_all_multi_archetype_deck(self) -> None:
        """Tests parsing a comprehensive gslides read-all text dump covering all 8 archetypes."""
        read_all_text = """
--- Slide 1 (SLIDE_01_INTRO) ---
FOUNDATION
The AI Factory Blueprint
A Developer's Playbook for the Agentic Era
Speaker Notes: Welcome everyone. Today we are presenting the core architectural blueprint for scaling autonomous software engineering factories.

--- Slide 2 (SLIDE_02_SPLIT) ---
PARADIGMS
Two Paradigms of Development
Comparing manual hand-prompting with deterministic pipelines
Traditional:
• Manual copy-pasting of context into web UI
• Unpredictable outputs and silent regressions
• Zero automated verification loops
AI Factory:
• Automated context injection via mounted trees
• Enforcing pre-commit gates blocking bad code
• Adversarial evaluator sub-agents grading runs
Speaker Notes: On this slide we compare ad-hoc prompting against the deterministic harness model. Notice how disciplined engineering compounds over iterations.

--- Slide 3 (SLIDE_03_CODE) ---
ENFORCING RATCHET
The Pre-Commit Gate in Practice
Block invalid migrations and compile errors automatically
```bash
#!/bin/sh
typecheck && lint
test --bail || exit 1
```
Speaker Notes: Here is the concrete bash ratchet implementation. The agent cannot commit code unless every typecheck and unit test passes cleanly.

--- Slide 4 (SLIDE_04_METRICS) ---
ECONOMICS
The Economics of Skipping Basics
Harness investment vs token waste in real experiments
$9 · 20 min - Solo model prototype with broken physics
$200 · 6 hours - Shippable enterprise engine with full test suite
Speaker Notes: Review these economic figures. Spending 9 dollars yields a discarded toy, whereas 200 dollars in a rich harness delivers shippable software.

--- Slide 5 (SLIDE_05_LADDER) ---
DISCIPLINES
The Four Disciplines of Agentic Engineering
Master each rung sequentially before adopting high-level frameworks
Step 1: Prompt Engineering - GCCD framework for intent
Step 2: Context Architecture - Compact and offload window
Step 3: Harness & Ratchet - Sandboxes and enforcing hooks
Step 4: Loop Engineering - Scheduled prompters with human gates
Speaker Notes: We structure engineering into four sequential disciplines: Prompt, Context, Harness, and Loop. Each discipline builds directly upon the previous rung.

--- Slide 6 (SLIDE_06_GRID) ---
EXECUTIVE SUMMARY
The Blueprint in One Line Each
Summary of the four foundational operating pillars
#### 01 Prompt
Guide intent with Goal, Context, Constraints, and Done-when.
#### 02 Context
Curate the context window: compact, offload, reset, and persist.
#### 03 Harness
Equip sandbox state, execution tools, hooks, and evaluators.
#### 04 Loop
Automate the prompter while keeping human judgment in review.
Speaker Notes: Here is the executive four quadrant summary. Each pillar operates independently with distinct engineering responsibilities.

--- Slide 7 (SLIDE_07_DODONT) ---
STANDARDS
Agentic Tool Adoption: Do's and Don'ts
Operationalize what you learned rather than bypassing disciplines
DO:
• Define verifiable done-when criteria before runs
• Isolate parallel agent tasks in separate worktrees
• Employ independent adversarial checker sub-agents
DON'T:
• Fanning out vague prompts to 20 models at once
• Letting autonomous loops merge code with no review
• Relying on random retries instead of ratchets
Speaker Notes: Review our checklist of recommended standards against common anti-patterns when adopting agentic tooling across engineering teams.

--- Slide 8 (SLIDE_08_TAKEAWAYS) ---
NEXT STEPS
Key Takeaways & Next Steps
Strategic principles and execution roadmap for engineering teams
Speaker Notes: To conclude our presentation, we summarize the three core principles and outline the immediate three-phase delivery roadmap.
"""

        ingestor = SlidesIngestor()
        spec = ingestor.ingest(read_all_text)

        self.assertIsInstance(spec, PresentationSpec)
        all_slides = [s for ch in spec.chapters for s in ch.slides]
        self.assertEqual(len(all_slides), 8)

        # Verify archetypes
        archetypes = [s.archetype for s in all_slides]
        self.assertIn("chapter_divider", archetypes)
        self.assertIn("split_cards", archetypes)
        self.assertIn("code_terminal", archetypes)
        self.assertIn("hero_metrics", archetypes)
        self.assertIn("ladder_hierarchy", archetypes)
        self.assertIn("executive_grid", archetypes)
        self.assertIn("dodont_checklist", archetypes)
        self.assertIn("actionable_takeaways", archetypes)

        # Verify speaker notes compliance (>= 15 words)
        for idx, slide in enumerate(all_slides, start=1):
            notes = slide.notes or slide.speaker_notes
            self.assertTrue(notes, f"Slide {idx} missing speaker notes")
            words = len(notes.split())
            self.assertGreaterEqual(
                words,
                15,
                f"Slide {idx} notes has {words} words (< 15): '{notes}'",
            )

    def test_parse_gslides_json_structure(self) -> None:
        """Tests parsing a Google Slides API JSON dictionary structure."""
        json_data = {
            "slides": [
                {
                    "objectId": "SLIDE_TITLE",
                    "pageElements": [
                        {
                            "shape": {
                                "text": {
                                    "textElements": [
                                        {"textRun": {"content": "Autonomous Agents in Production\n"}},
                                        {"textRun": {"content": "Architecture, Scalability, and Guardrails\n"}},
                                    ]
                                }
                            }
                        }
                    ],
                    "slideProperties": {
                        "notesPage": {
                            "pageElements": [
                                {
                                    "shape": {
                                        "text": {
                                            "textElements": [
                                                {"textRun": {"content": "Welcome to our presentation on autonomous agents in enterprise production environments."}}
                                            ]
                                        }
                                    }
                                }
                            ]
                        }
                    },
                },
                {
                    "objectId": "SLIDE_CARDS",
                    "title": "System Architecture Overview",
                    "subtitle": "Decoupled modules for evaluation and compilation",
                    "cards": [
                        {"title": "Ingestion", "bullets": ["File scanner", "AST parser"]},
                        {"title": "Compiler", "bullets": ["Batch JSON", "Placeholder resolution"]},
                    ],
                    "speaker_notes": "Here we examine the two primary modules of our slide generation platform.",
                },
            ]
        }

        ingestor = SlidesIngestor()
        spec = ingestor.ingest(json_data)

        self.assertIsInstance(spec, PresentationSpec)
        all_slides = [s for ch in spec.chapters for s in ch.slides]
        self.assertEqual(len(all_slides), 2)
        self.assertEqual(all_slides[0].archetype, "chapter_divider")
        self.assertEqual(all_slides[1].archetype, "split_cards")

    def test_ingest_from_json_file(self) -> None:
        """Tests ingesting from a temporary JSON file path."""
        payload = {
            "slides": [
                {
                    "title": "Cloud Scale Migration",
                    "subtitle": "Transitioning services to Borg infrastructure",
                    "speaker_notes": "Welcome to our cloud scale migration architecture presentation for leadership.",
                    "archetype": "chapter_divider",
                },
                {
                    "title": "Best Practices Checklist",
                    "subtitle": "Key guidelines for zero-downtime cutover",
                    "do_items": ["Run dark launch shadow traffic", "Enforce circuit breaker limits"],
                    "dont_items": ["Cut over 100% traffic immediately", "Bypass staging canary tests"],
                    "speaker_notes": "Review this critical checklist when preparing the regional service migration.",
                    "archetype": "dodont_checklist",
                },
            ]
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(payload, f)
            temp_path = f.name

        try:
            ingestor = SlidesIngestor()
            spec = ingestor.ingest(temp_path)
            self.assertEqual(len(spec.chapters[0].slides), 2)
            self.assertEqual(spec.chapters[0].slides[1].archetype, "dodont_checklist")
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_missing_speaker_notes_stay_empty(self) -> None:
        """Slides without speaker notes in the source keep empty notes (never synthesized)."""
        minimal_text = """
--- Slide 1 ---
Executive Overview
Summary of system capabilities
• First capability
• Second capability
"""
        ingestor = SlidesIngestor()
        spec = ingestor.ingest(minimal_text)

        slide = spec.chapters[0].slides[0]
        self.assertEqual(slide.speaker_notes, "")

    def test_invalid_source_raises_error(self) -> None:
        """Verifies that invalid or missing source inputs raise appropriate exceptions."""
        ingestor = SlidesIngestor()
        with self.assertRaises(ValueError):
            ingestor.ingest(None)

        with self.assertRaises(TypeError):
            ingestor.ingest(12345)  # type: ignore


if __name__ == "__main__":
    unittest.main()

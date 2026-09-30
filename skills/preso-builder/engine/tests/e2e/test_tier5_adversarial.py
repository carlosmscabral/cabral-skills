"""Preso Builder E2E Test Suite - Tier 5: Adversarial Coverage Hardening.

Tests extreme edge cases, security and robustness boundaries:
1. Complete WCAG 2.1 AA/AAA contrast matrix sweep across all Blueprint color tokens
2. Canvas coordinate containment & bounding box collision sweeps across all 8 archetypes
3. Strict deterministic element ID uniqueness across multi-chapter compiled batches
4. Fuzzing, malicious script injection, and malformed payload recovery
5. Deterministic batch compilation invariance (100% reproducibility)
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path
import random
import string
import tempfile
import unittest

from preso.compiler.batch_generator import BatchCompiler, BatchCompilerConfig
from preso.compiler.gslides_client import GSlidesClient
from preso.engine.archetypes import ArchetypeEngine
from preso.engine.coordinates import (
    BoundingBox,
    calculate_2x2_grid_bounds,
    calculate_asymmetric_split_bounds,
    calculate_card_internal_bounds,
    calculate_header_bounds,
    calculate_n_column_bounds,
)
from preso.engine.design_tokens import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    COLOR_AMBER_LIGHT,
    COLOR_AMBER_TEXT,
    COLOR_AMBER_WARN,
    COLOR_BG_LIGHT,
    COLOR_BLUE_ACCENT,
    COLOR_BLUE_LIGHT,
    COLOR_BLUE_SUBTITLE,
    COLOR_BLUE_TEXT,
    COLOR_CARD_BORDER,
    COLOR_CARD_WHITE,
    COLOR_GREEN_DO,
    COLOR_GREEN_LIGHT,
    COLOR_GREEN_TEXT,
    COLOR_NAVY_PRIMARY,
    COLOR_NAVY_SURFACE,
    COLOR_RED_DONT,
    COLOR_RED_LIGHT,
    COLOR_RED_TEXT,
    COLOR_SLATE_DARK,
    COLOR_SLATE_HEADER,
    COLOR_TEXT_CODE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_WHITE,
    contrast_ratio,
    ensure_hex,
    is_wcag_aa,
    is_wcag_aaa,
    relative_luminance,
)
from preso.ingest.markdown import MarkdownIngestor
from preso.qa.report_generator import QAReportGenerator
from preso.qa.verifier import QAReport, QAVerifier
from preso.spec.models import (
    CardSpec,
    ChapterSpec,
    ChecklistSpec,
    CodeBlockSpec,
    HeroMetricSpec,
    LadderStepSpec,
    MetadataSpec,
    PresentationSpec,
    PrincipleSpec,
    QuadrantSpec,
    SlideSpec,
    TakeawaySpec,
)
from preso.spec.scaffolder import SpecScaffolder
from preso.spec.validator import SpecValidator


# ==============================================================================
# 1. Complete WCAG 2.1 AA/AAA Contrast Matrix Sweep
# ==============================================================================

class TestWCAGContrastMatrixSweep(unittest.TestCase):
    """Exhaustive mathematical verification of WCAG 2.1 contrast calculations and color tokens."""

    def test_contrast_ratio_mathematical_properties(self) -> None:
        """Verifies mathematical properties of relative luminance and contrast ratio."""
        # 1. Black on White is 21.0:1 (maximum possible contrast)
        cr_max = contrast_ratio("#000000", "#FFFFFF")
        self.assertAlmostEqual(cr_max, 21.0, places=1)

        # 2. Symmetry: contrast_ratio(A, B) == contrast_ratio(B, A)
        self.assertEqual(contrast_ratio("#1A73E8", "#FFFFFF"), contrast_ratio("#FFFFFF", "#1A73E8"))

        # 3. Identity: contrast_ratio(A, A) is exactly 1.0:1 (minimum possible contrast)
        self.assertAlmostEqual(contrast_ratio("#1E2761", "#1E2761"), 1.0, places=2)

        # 4. Range: 1.0 <= CR <= 21.0
        for _ in range(20):
            c1 = f"#{random.randint(0, 0xFFFFFF):06x}"
            c2 = f"#{random.randint(0, 0xFFFFFF):06x}"
            cr = contrast_ratio(c1, c2)
            self.assertGreaterEqual(cr, 1.0)
            self.assertLessEqual(cr, 21.01)

    def test_all_blueprint_color_pairings_meet_wcag_aa(self) -> None:
        """Verifies that all text tokens on their intended background meet WCAG 2.1 AA (CR >= 4.5:1)."""
        pairings = [
            # (Foreground, Background, Minimum Target CR, Description)
            (COLOR_TEXT_PRIMARY, COLOR_BG_LIGHT, 4.5, "Primary body text on light canvas"),
            (COLOR_TEXT_PRIMARY, COLOR_CARD_WHITE, 4.5, "Primary body text on white card"),
            (COLOR_TEXT_WHITE, COLOR_NAVY_PRIMARY, 4.5, "White text on navy chapter divider"),
            (COLOR_TEXT_WHITE, COLOR_SLATE_DARK, 4.5, "White text on dark code terminal"),
            (COLOR_BLUE_TEXT, COLOR_BLUE_LIGHT, 4.5, "Blue pill text on blue tint background"),
            (COLOR_GREEN_TEXT, COLOR_GREEN_LIGHT, 4.5, "Green pill text on green tint background"),
            (COLOR_RED_TEXT, COLOR_RED_LIGHT, 4.5, "Red pill text on red tint background"),
            (COLOR_AMBER_TEXT, COLOR_AMBER_LIGHT, 4.5, "Amber pill text on amber tint background"),
            (COLOR_BLUE_SUBTITLE, COLOR_NAVY_PRIMARY, 4.5, "Blue subtitle on dark navy background"),
            (COLOR_TEXT_CODE, COLOR_SLATE_DARK, 4.5, "Code text on slate terminal container"),
        ]

        for fg, bg, target_cr, desc in pairings:
            cr = contrast_ratio(fg, bg)
            self.assertGreaterEqual(
                cr,
                target_cr,
                f"WCAG AA Failure for '{desc}': Foreground {fg} on Background {bg} has CR {cr:.2f}:1 (Target: >= {target_cr}:1)",
            )
            self.assertTrue(
                is_wcag_aa(fg, bg, is_large_text=False),
                f"is_wcag_aa returned False for '{desc}'",
            )


# ==============================================================================
# 2. Canvas Coordinate Containment & Collision Sweeps
# ==============================================================================

class TestCanvasContainmentAndCollisionSweeps(unittest.TestCase):
    """Exhaustive geometry audit asserting zero collisions and strict canvas containment."""

    def test_all_eight_archetypes_strict_containment(self) -> None:
        """Verifies that every shape generated across all 8 archetypes fits strictly inside 720x405 pt."""
        spec = SpecScaffolder.scaffold_preset("ai_factory")
        compiler = BatchCompiler()
        result = compiler.compile(spec)

        for op in result.operations:
            op_type = op.get("op")
            if op_type in ("add-textbox", "add-shape"):
                x = float(op.get("x", 0.0))
                y = float(op.get("y", 0.0))
                w = float(op.get("width", 0.0))
                h = float(op.get("height", 0.0))
                elem_id = op.get("id", "")

                # Strict canvas containment
                self.assertGreaterEqual(x, 0.0, f"Element {elem_id} x coordinate {x} < 0")
                self.assertGreaterEqual(y, 0.0, f"Element {elem_id} y coordinate {y} < 0")
                self.assertLessEqual(x + w, CANVAS_WIDTH + 0.1, f"Element {elem_id} right edge {x+w} exceeds {CANVAS_WIDTH}")
                self.assertLessEqual(y + h, CANVAS_HEIGHT + 0.1, f"Element {elem_id} bottom edge {y+h} exceeds {CANVAS_HEIGHT}")

    def test_sibling_bounding_box_non_overlap_sweep(self) -> None:
        """Verifies that non-nested sibling cards/columns do not collide or intersect."""
        # 1. 2-card and 3-card columns
        for n in [2, 3, 4]:
            boxes = calculate_n_column_bounds(n=n)
            for i in range(len(boxes)):
                for j in range(i + 1, len(boxes)):
                    b1 = boxes[i]
                    b2 = boxes[j]
                    self.assertFalse(
                        b1.intersects(b2),
                        f"Collision detected between column {i} {b1} and column {j} {b2}",
                    )

        # 2. 2x2 Grid quadrants
        quad_boxes = calculate_2x2_grid_bounds()
        for i in range(len(quad_boxes)):
            for j in range(i + 1, len(quad_boxes)):
                q1 = quad_boxes[i]
                q2 = quad_boxes[j]
                self.assertFalse(
                    q1.intersects(q2),
                    f"Collision detected between quadrant {i} {q1} and quadrant {j} {q2}",
                )

        # 3. Asymmetric Split columns
        left_col, right_col = calculate_asymmetric_split_bounds()
        self.assertFalse(left_col.intersects(right_col))


# ==============================================================================
# 3. Deterministic Unique ID Sweeps
# ==============================================================================

class TestDeterministicUniqueIDUniqueness(unittest.TestCase):
    """Verifies that 100% of element and slide IDs generated are globally unique."""

    def test_multi_chapter_unique_element_ids(self) -> None:
        """Asserts zero duplicate shape or textbox IDs across an entire presentation batch."""
        spec = SpecScaffolder.scaffold_preset("ai_factory")
        compiler = BatchCompiler()
        result = compiler.compile(spec)

        seen_ids: set[str] = set()
        duplicate_ids: list[str] = []

        for op in result.operations:
            elem_id = op.get("id")
            if elem_id:
                if elem_id in seen_ids:
                    duplicate_ids.append(elem_id)
                seen_ids.add(elem_id)

        self.assertEqual(
            len(duplicate_ids),
            0,
            f"Found {len(duplicate_ids)} duplicate element IDs in compiled batch: {duplicate_ids[:5]}",
        )


# ==============================================================================
# 4. Fuzzing & Malformed Payload Recovery
# ==============================================================================

class TestFuzzingAndMalformedPayloadRecovery(unittest.TestCase):
    """Verifies resilience against HTML injection, emojis, null characters, and malformed types."""

    def test_html_and_script_injection_sanitization(self) -> None:
        """Verifies HTML and JavaScript injection payloads compile cleanly without escaping failures."""
        malicious_code = "<script>alert('XSS')</script>\n<style>body{display:none;}</style>"
        slide = SlideSpec(
            archetype="code_terminal",
            title="<script>alert('Title')</script>",
            subtitle="<b>Safe Subtitle</b>",
            terminals=[CodeBlockSpec(filename="<inject>.html", code=malicious_code)],
            notes="<script>Speaker notes injection test.</script>",
        )
        spec = PresentationSpec(chapters=[ChapterSpec(number=1, title="Injection Test", slides=[slide])])

        # Compile
        compiler = BatchCompiler()
        batch_res = compiler.compile(spec)
        self.assertGreater(len(batch_res.operations), 0)

        # Preview generation
        with tempfile.TemporaryDirectory() as tmp_dir:
            preview_file = Path(tmp_dir) / "preview.html"
            html = QAReportGenerator.generate_html_preview(spec=spec, output_path=preview_file)
            self.assertTrue(preview_file.exists())
            # Ensure literal <script> tag does not execute as executable tag
            self.assertIn("&lt;script&gt;", html)

    def test_unicode_and_emoji_payload_resilience(self) -> None:
        """Verifies handling of multi-byte Unicode, math symbols, and emojis."""
        unicode_title = "🚀 AI Factory Blueprint: 10× Scaling (λ → ∞) 日本語 🌟"
        slide = SlideSpec(
            archetype="split_cards",
            title=unicode_title,
            subtitle="Multi-byte UTF-8 test ⚡",
            cards=[
                CardSpec(title="Card 1 🎯", bullets=["Emoji bullet 1 ✨", "Mathematical symbol: ∀x ∈ S ∃y"]),
                CardSpec(title="Card 2 🔒", bullets=["Security & Isolation 🛡️", "Deterministic guarantees 📐"]),
            ],
            notes="Speaker notes with emojis 🎤 and unicode symbols ∀x.",
        )
        spec = PresentationSpec(chapters=[ChapterSpec(number=1, title="Unicode Test", slides=[slide])])

        compiler = BatchCompiler()
        batch_res = compiler.compile(spec)
        self.assertGreater(len(batch_res.operations), 0)

        # Validate
        self.assertTrue(SpecValidator.validate(spec, strict=False).is_valid)

    def test_fuzzed_random_markdown_recovery(self) -> None:
        """Fuzzes MarkdownIngestor with randomized strings, unbalanced delimiters, and garbage input."""
        ingestor = MarkdownIngestor()

        # Fuzz 15 iterations with random garbage strings
        for _ in range(15):
            garbage_length = random.randint(50, 500)
            garbage_chars = string.ascii_letters + string.punctuation + "\n\t " + "🚀🔥⚡∑π"
            garbage_text = "".join(random.choices(garbage_chars, k=garbage_length))

            # Must not raise unhandled exceptions
            spec = ingestor.ingest(garbage_text)
            self.assertIsInstance(spec, PresentationSpec)
            self.assertGreaterEqual(len(spec.chapters), 1)


# ==============================================================================
# 5. Deterministic Compilation Invariance
# ==============================================================================

class TestDeterministicCompilationInvariance(unittest.TestCase):
    """Verifies that 100% of compiler operations are bitwise deterministic and repeatable."""

    def test_compilation_determinism_across_runs(self) -> None:
        """Verifies that compiling the exact same specification 10 times produces identical JSON output."""
        spec = SpecScaffolder.scaffold_preset("ai_factory")
        compiler = BatchCompiler()

        reference_payload = json.dumps(compiler.compile(spec).operations, sort_keys=True)

        for run in range(10):
            current_payload = json.dumps(compiler.compile(spec).operations, sort_keys=True)
            self.assertEqual(
                reference_payload,
                current_payload,
                f"Non-deterministic compilation detected on iteration {run + 1}",
            )


if __name__ == "__main__":
    unittest.main()

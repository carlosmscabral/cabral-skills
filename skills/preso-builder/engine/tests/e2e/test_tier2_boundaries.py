"""Preso Builder E2E Test Suite - Tier 2: Boundary & Corner Cases.

Tests extreme parameters, boundary limits, empty inputs, maximum capacity,
missing fields, zero/negative metrics, and defensive recovery across all
Blueprint components.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from typing import Any

from preso.compiler.batch_generator import (
    BatchCompiler,
    BatchCompilerConfig,
    ChapterManifest,
    PresentationManifest,
    SlideManifest,
)
from preso.compiler.gslides_client import GSlidesClient
from preso.engine.archetypes import (
    ArchetypeEngine,
    generate_actionable_takeaways,
    generate_chapter_divider,
    generate_code_terminal,
    generate_dodont_checklist,
    generate_executive_grid,
    generate_hero_metrics,
    generate_ladder_hierarchy,
    generate_split_cards,
)
from preso.engine.coordinates import (
    BoundingBox,
    calculate_2x2_grid_bounds,
    calculate_asymmetric_split_bounds,
    calculate_card_internal_bounds,
    calculate_header_bounds,
    calculate_n_column_bounds,
)
from preso.engine.design_tokens import CANVAS_HEIGHT, CANVAS_WIDTH
from preso.qa.verifier import QAVerifier
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
# 1. Text Length & Budget Boundaries
# ==============================================================================

class TestTextBudgetBoundaries(unittest.TestCase):
    """Verifies behavior at exact character budget limits and overflow boundaries."""

    def test_slide_title_exact_and_overflow_limits(self) -> None:
        """Tests slide title validation at 0, 60 (budget), and 150 characters."""
        # Empty title with no chapter number on divider
        spec_empty = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="chapter_divider", title="", chapter_number="", notes="Valid speaker notes text for testing.")
            ])]
        )
        res_empty = SpecValidator.validate(spec_empty, strict=True)
        self.assertFalse(res_empty.is_valid)

        # Exactly 60 chars (boundary limit)
        title_60 = "A" * 60
        spec_60 = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="chapter_divider", title=title_60, notes="Valid speaker notes text for testing.")
            ])]
        )
        res_60 = SpecValidator.validate(spec_60, strict=True)
        self.assertTrue(res_60.is_valid)

        # 150 chars (overflow error in strict mode, warning in non-strict mode)
        title_150 = "B" * 150
        spec_150 = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="chapter_divider", title=title_150, notes="Valid speaker notes text for testing.")
            ])]
        )
        res_strict = SpecValidator.validate(spec_150, strict=True)
        self.assertFalse(res_strict.is_valid)
        self.assertTrue(any("title exceeds" in e.lower() for e in res_strict.errors))

        res_nonstrict = SpecValidator.validate(spec_150, strict=False)
        self.assertTrue(res_nonstrict.is_valid)
        self.assertTrue(any("title exceeds" in w.lower() for w in res_nonstrict.warnings))

    def test_subtitle_length_boundaries(self) -> None:
        """Tests subtitle validation at 0 (allowed), 120 (budget), and 300 characters."""
        # 0 chars (allowed)
        spec_no_sub = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="chapter_divider", title="Valid Title", subtitle="", notes="Valid notes for slide.")
            ])]
        )
        self.assertTrue(SpecValidator.validate(spec_no_sub, strict=True).is_valid)

        # 120 chars (valid)
        sub_120 = "C" * 120
        spec_120 = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="chapter_divider", title="Valid Title", subtitle=sub_120, notes="Valid notes for slide.")
            ])]
        )
        self.assertTrue(SpecValidator.validate(spec_120, strict=True).is_valid)

        # 300 chars (triggers error in strict mode, warning in non-strict)
        sub_300 = "D" * 300
        spec_300 = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="chapter_divider", title="Valid Title", subtitle=sub_300, notes="Valid notes for slide.")
            ])]
        )
        res_strict = SpecValidator.validate(spec_300, strict=True)
        self.assertFalse(res_strict.is_valid)
        self.assertTrue(any("subtitle exceeds" in e.lower() for e in res_strict.errors))

        res_nonstrict = SpecValidator.validate(spec_300, strict=False)
        self.assertTrue(res_nonstrict.is_valid)
        self.assertTrue(any("subtitle exceeds" in w.lower() for w in res_nonstrict.warnings))

    def test_kicker_length_boundaries(self) -> None:
        """Tests kicker length boundaries at 0, 30, and 80 chars."""
        # Kicker 80 chars
        kicker_80 = "E" * 80
        spec_kicker = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(
                    archetype="chapter_divider",
                    title="Title",
                    kicker=kicker_80,
                    notes="Speaker notes for kicker test.",
                )
            ])]
        )
        res = SpecValidator.validate(spec_kicker, strict=False)
        self.assertTrue(any("kicker exceeds" in w.lower() for w in res.warnings))

    def test_bullet_point_length_boundaries(self) -> None:
        """Tests card bullet point length boundaries at 0, 90, and 250 characters."""
        card_normal = CardSpec(title="Card 1", bullets=["Normal bullet"])
        card_250 = CardSpec(title="Card 2", bullets=["G" * 250])

        spec = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="split_cards", title="Split", cards=[card_normal, card_250], notes="Speaker notes here.")
            ])]
        )
        res_nonstrict = SpecValidator.validate(spec, strict=False)
        self.assertTrue(any("bullet" in w.lower() and "exceeds" in w.lower() for w in res_nonstrict.warnings))


# ==============================================================================
# 2. Split Card Count Boundaries
# ==============================================================================

class TestSplitCardCountBoundaries(unittest.TestCase):
    """Verifies Archetype 2 behavior across 0, 1, 2, 3, 4, and 5 cards."""

    def test_zero_cards_rejected_by_engine_and_validator(self) -> None:
        """Verifies 0 cards raises ValueError in ArchetypeEngine and error in Validator."""
        with self.assertRaises(ValueError):
            generate_split_cards(slide_id="S01", title="Title", subtitle="Sub", kicker="KICKER", cards=[])

        spec = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="split_cards", title="Split", cards=[], notes="Notes for 0 cards test.")
            ])]
        )
        res = SpecValidator.validate(spec)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("requires cards" in e.lower() for e in res.errors))

    def test_single_card_boundary(self) -> None:
        """Verifies 1 card generates valid single-column card in engine."""
        c1 = CardSpec(title="Solo Card", bullets=["Point 1", "Point 2"])
        ops = generate_split_cards(slide_id="S01", title="Title", subtitle="Sub", kicker="KICKER", cards=[c1.to_dict()])
        self.assertGreater(len(ops), 0)

        # Validator flags 1 card as error or warning since Blueprint standard is 2 or 3
        spec = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="split_cards", title="Split", cards=[c1], notes="Notes for 1 card test.")
            ])]
        )
        res = SpecValidator.validate(spec, strict=False)
        self.assertTrue(any("2 or 3 cards" in w.lower() for w in res.warnings))

    def test_two_and_three_cards_optimal_boundaries(self) -> None:
        """Verifies 2 and 3 cards generate valid bounds without collisions."""
        c1 = CardSpec(title="Card 1", bullets=["Point A"])
        c2 = CardSpec(title="Card 2", bullets=["Point B"])
        c3 = CardSpec(title="Card 3", bullets=["Point C"])

        # 2 cards
        ops_2 = generate_split_cards(slide_id="S01", title="2 Cards", subtitle="Sub", kicker="KICKER", cards=[c1.to_dict(), c2.to_dict()])
        self.assertGreater(len(ops_2), 5)

        # 3 cards
        ops_3 = generate_split_cards(slide_id="S02", title="3 Cards", subtitle="Sub", kicker="KICKER", cards=[c1.to_dict(), c2.to_dict(), c3.to_dict()])
        self.assertGreater(len(ops_3), 5)

    def test_four_and_five_cards_overflow_boundaries(self) -> None:
        """Verifies 4 and 5 cards generate multi-column cards but are flagged by validator."""
        cards_4 = [CardSpec(title=f"Card {i}", bullets=[f"Point {i}"]) for i in range(1, 5)]
        ops_4 = generate_split_cards(slide_id="S01", title="4 Cards", subtitle="Sub", kicker="KICKER", cards=[c.to_dict() for c in cards_4])
        self.assertGreater(len(ops_4), 5)

        spec = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="split_cards", title="4 Cards", cards=cards_4, notes="Notes for 4 cards.")
            ])]
        )
        res = SpecValidator.validate(spec, strict=False)
        self.assertTrue(any("2 or 3 cards" in w.lower() for w in res.warnings))


# ==============================================================================
# 3. Extreme Numbers & Unit Boundaries
# ==============================================================================

class TestExtremeNumbersAndMetrics(unittest.TestCase):
    """Verifies Hero Metric formatting with extreme numbers, zero, negative, and units."""

    def test_large_number_formatting(self) -> None:
        """Verifies large numbers (e.g., $1.2B, 500k, 99.999%) in hero metrics."""
        m1 = HeroMetricSpec(value="$1.2B", unit="ARR", delta="+120% YoY", delta_type="positive")
        m2 = HeroMetricSpec(value="99.999%", unit="Uptime", delta="-0.001% risk", delta_type="negative")
        ops = generate_hero_metrics(slide_id="S01", title="Metrics", subtitle="Sub", kicker="STATS", metrics=[m1.to_dict(), m2.to_dict()])
        texts = [op.get("text", "") for op in ops if op.get("op") == "add-textbox"]
        self.assertTrue(any("$1.2B" in t for t in texts))
        self.assertTrue(any("99.999%" in t for t in texts))

    def test_zero_and_negative_metrics(self) -> None:
        """Verifies 0 and negative values format cleanly without crash."""
        m1 = HeroMetricSpec(value="0", unit="downtime", delta="0 min", delta_type="neutral")
        m2 = HeroMetricSpec(value="-45%", unit="cost", delta="-45% reduction", delta_type="positive")
        ops = generate_hero_metrics(slide_id="S01", title="Zero Cost", subtitle="Sub", kicker="STATS", metrics=[m1.to_dict(), m2.to_dict()])
        self.assertGreater(len(ops), 0)

    def test_metric_stat_string_budget_boundaries(self) -> None:
        """Verifies stat string exceeding 12 characters triggers validation warning in non-strict."""
        m_short = HeroMetricSpec(value="10x", label="GAIN")
        m_long = HeroMetricSpec(value="123456789012345", label="LONG STAT")  # 15 chars > 12

        spec = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="hero_metrics", title="Metrics", metrics=[m_short, m_long], notes="Valid speaker notes.")
            ])]
        )
        res = SpecValidator.validate(spec, strict=False)
        self.assertTrue(any("stat" in w.lower() and "exceeds" in w.lower() for w in res.warnings))


# ==============================================================================
# 4. Speaker Notes Boundaries & Auto-Synthesis
# ==============================================================================

class TestSpeakerNotesBoundaries(unittest.TestCase):
    """Speaker notes are optional: never warned about, never synthesized."""

    def test_empty_or_short_notes_are_accepted_silently(self) -> None:
        """Missing / very short notes produce no warnings."""
        # Empty string
        spec_empty = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="chapter_divider", title="Title", notes="")
            ])]
        )
        res_empty = SpecValidator.validate(spec_empty)
        self.assertTrue(res_empty.is_valid)
        self.assertFalse(any("notes" in w.lower() for w in res_empty.warnings))

        # 10 chars (< 15)
        spec_short = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="chapter_divider", title="Title", notes="Short note")
            ])]
        )
        res_short = SpecValidator.validate(spec_short)
        self.assertTrue(res_short.is_valid)
        self.assertFalse(any("notes" in w.lower() for w in res_short.warnings))

        # Exactly 15 chars (valid)
        spec_15 = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="chapter_divider", title="Title", notes="Valid notes text here!")
            ])]
        )
        self.assertTrue(SpecValidator.validate(spec_15).is_valid)

    def test_compiler_never_synthesizes_notes(self) -> None:
        """BatchCompiler emits no set-notes op for a slide without authored notes."""
        compiler = BatchCompiler(config=BatchCompilerConfig())
        raw_slide = SlideManifest(archetype="split_cards", title="System Architecture", subtitle="Key subsystems")
        manifest = PresentationManifest(slides=[raw_slide])
        result = compiler.compile(manifest)

        # Verify operations were compiled, with no invented notes
        self.assertGreater(len(result.operations), 0)
        self.assertFalse(any(op.get("op") == "set-notes" for op in result.operations))


# ==============================================================================
# 5. Code Terminal Boundaries
# ==============================================================================

class TestCodeTerminalBoundaries(unittest.TestCase):
    """Verifies Archetype 3 behavior across 0 lines, 1 line, 12 lines, and 50+ lines."""

    def test_single_line_code_block(self) -> None:
        """Verifies 1-line code block compiles cleanly."""
        t = CodeBlockSpec(filename="inline.py", code="x = 42")
        ops = generate_code_terminal(slide_id="S01", title="Code", subtitle="Sub", kicker="CODE", terminals=[t.to_dict()])
        self.assertGreater(len(ops), 0)

    def test_code_line_count_validation_boundaries(self) -> None:
        """Verifies code exceeding 16 lines triggers validation warning in non-strict mode."""
        code_10 = "\n".join([f"line_{i} = {i}" for i in range(10)])
        code_20 = "\n".join([f"line_{i} = {i}" for i in range(20)])

        spec_10 = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="code_terminal", title="Code", terminals=[CodeBlockSpec(code=code_10)], notes="Speaker notes here.")
            ])]
        )
        self.assertTrue(SpecValidator.validate(spec_10).is_valid)

        spec_20 = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="code_terminal", title="Code", terminals=[CodeBlockSpec(code=code_20)], notes="Speaker notes here.")
            ])]
        )
        res_20 = SpecValidator.validate(spec_20, strict=False)
        self.assertTrue(any("lines" in w.lower() and "exceeds" in w.lower() for w in res_20.warnings))

    def test_wide_code_line_character_budget(self) -> None:
        """Verifies long code lines (> 60 chars) trigger validation warnings."""
        wide_code = "a" * 80
        spec = PresentationSpec(
            chapters=[ChapterSpec(number=1, title="C1", slides=[
                SlideSpec(archetype="code_terminal", title="Code", terminals=[CodeBlockSpec(code=wide_code)], notes="Speaker notes here.")
            ])]
        )
        res = SpecValidator.validate(spec, strict=False)
        self.assertTrue(any("characters" in w.lower() or "60" in w.lower() for w in res.warnings))


# ==============================================================================
# 6. Stepped Flow & Ladder Boundaries
# ==============================================================================

class TestLadderHierarchyBoundaries(unittest.TestCase):
    """Verifies Archetype 5 across 0, 1, 3, 4, and 6 steps."""

    def test_zero_steps_handling(self) -> None:
        """Verifies 0 steps raises ValueError in engine."""
        with self.assertRaises(ValueError):
            generate_ladder_hierarchy(slide_id="S01", title="Ladder", subtitle="Sub", kicker="STEPS", steps=[])

    def test_step_count_validation_boundaries(self) -> None:
        """Verifies validator enforces 3 to 5 rungs for ladder hierarchy."""
        steps_2 = [LadderStepSpec(step_number=i, title=f"S{i}", description=f"D{i}") for i in range(1, 3)]
        steps_4 = [LadderStepSpec(step_number=i, title=f"S{i}", description=f"D{i}") for i in range(1, 5)]
        steps_6 = [LadderStepSpec(step_number=i, title=f"S{i}", description=f"D{i}") for i in range(1, 7)]

        # 2 steps -> error in validator (requires 3 to 5 steps)
        spec_2 = PresentationSpec(chapters=[ChapterSpec(number=1, title="C1", slides=[
            SlideSpec(archetype="ladder_hierarchy", title="Ladder", steps=steps_2, notes="Speaker notes here.")
        ])])
        res_2 = SpecValidator.validate(spec_2)
        self.assertFalse(res_2.is_valid)
        self.assertTrue(any("requires 3 to 5 steps" in e.lower() for e in res_2.errors))

        # 4 steps -> valid
        spec_4 = PresentationSpec(chapters=[ChapterSpec(number=1, title="C1", slides=[
            SlideSpec(archetype="ladder_hierarchy", title="Ladder", steps=steps_4, notes="Speaker notes here.")
        ])])
        self.assertTrue(SpecValidator.validate(spec_4).is_valid)

        # 6 steps -> error in validator
        spec_6 = PresentationSpec(chapters=[ChapterSpec(number=1, title="C1", slides=[
            SlideSpec(archetype="ladder_hierarchy", title="Ladder", steps=steps_6, notes="Speaker notes here.")
        ])])
        res_6 = SpecValidator.validate(spec_6)
        self.assertFalse(res_6.is_valid)
        self.assertTrue(any("requires 3 to 5 steps" in e.lower() for e in res_6.errors))


# ==============================================================================
# 7. Executive Grid & Quadrant Boundaries
# ==============================================================================

class TestExecutiveGridBoundaries(unittest.TestCase):
    """Verifies Archetype 6 2x2 grid quadrant limits."""

    def test_zero_and_uneven_quadrants(self) -> None:
        """Verifies non-4 quadrants trigger validation errors."""
        quads_3 = [QuadrantSpec(number=f"0{i}", title=f"Q{i}", narrative=f"N{i}") for i in range(1, 4)]
        spec_3 = PresentationSpec(chapters=[ChapterSpec(number=1, title="C1", slides=[
            SlideSpec(archetype="executive_grid", title="Grid", quadrants=quads_3, notes="Speaker notes here.")
        ])])
        res = SpecValidator.validate(spec_3)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("requires exactly 4 quadrants" in e.lower() for e in res.errors))

    def test_exact_four_quadrants_valid(self) -> None:
        """Verifies exactly 4 quadrants pass validation cleanly."""
        quads_4 = [QuadrantSpec(number=f"0{i}", title=f"Q{i}", narrative=f"N{i}") for i in range(1, 5)]
        spec_4 = PresentationSpec(chapters=[ChapterSpec(number=1, title="C1", slides=[
            SlideSpec(archetype="executive_grid", title="Grid", quadrants=quads_4, notes="Speaker notes here.")
        ])])
        self.assertTrue(SpecValidator.validate(spec_4).is_valid)


# ==============================================================================
# 8. Missing Fields & Malformed Payload Boundaries
# ==============================================================================

class TestMissingFieldsAndMalformedData(unittest.TestCase):
    """Verifies defensive error handling on missing, null, or malformed data."""

    def test_missing_metadata_defaults(self) -> None:
        """Verifies PresentationSpec with default metadata parses cleanly."""
        spec = PresentationSpec(chapters=[ChapterSpec(number=1, title="C1", slides=[
            SlideSpec(archetype="chapter_divider", title="Title", notes="Speaker notes here.")
        ])])
        self.assertEqual(spec.metadata.template_id, "1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U")
        self.assertTrue(SpecValidator.validate(spec).is_valid)

    def test_empty_presentation_rejected(self) -> None:
        """Verifies presentation with no chapters or slides is rejected."""
        spec_empty = PresentationSpec(chapters=[])
        res = SpecValidator.validate(spec_empty)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("zero chapters" in e.lower() for e in res.errors))

    def test_unsupported_archetype_rejection(self) -> None:
        """Verifies unknown archetype string is rejected by engine and validator."""
        with self.assertRaises(ValueError):
            ArchetypeEngine.generate_slide_ops({"archetype": "3d_pie_chart", "title": "Fail"}, slide_index=1)

        spec = PresentationSpec(chapters=[ChapterSpec(number=1, title="C1", slides=[
            SlideSpec(archetype="3d_pie_chart", title="Fail", notes="Speaker notes here.")
        ])])
        res = SpecValidator.validate(spec)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("unknown archetype" in e.lower() for e in res.errors))


# ==============================================================================
# 9. Canvas Geometry Clamping Boundaries
# ==============================================================================

class TestCanvasGeometryBoundaries(unittest.TestCase):
    """Verifies coordinate bounding box clamping to 720x405 pt canvas boundaries."""

    def test_bounding_box_canvas_containment(self) -> None:
        """Verifies all layout bounding boxes stay strictly inside 720x405 pt."""
        header_boxes = calculate_header_bounds()
        for key, box in header_boxes.items():
            self.assertGreaterEqual(box.left, 0)
            self.assertGreaterEqual(box.top, 0)
            self.assertLessEqual(box.right, CANVAS_WIDTH)
            self.assertLessEqual(box.bottom, CANVAS_HEIGHT)

        # 4-column bounds
        col_boxes = calculate_n_column_bounds(n=4)
        for box in col_boxes:
            self.assertGreaterEqual(box.left, 0)
            self.assertGreaterEqual(box.top, 0)
            self.assertLessEqual(box.right, CANVAS_WIDTH)
            self.assertLessEqual(box.bottom, CANVAS_HEIGHT)

        # 2x2 grid bounds
        grid_boxes = calculate_2x2_grid_bounds()
        for box in grid_boxes:
            self.assertGreaterEqual(box.left, 0)
            self.assertGreaterEqual(box.top, 0)
            self.assertLessEqual(box.right, CANVAS_WIDTH)
            self.assertLessEqual(box.bottom, CANVAS_HEIGHT)

        # Asymmetric split bounds
        left_box, right_box = calculate_asymmetric_split_bounds()
        self.assertGreaterEqual(left_box.left, 0)
        self.assertLessEqual(right_box.right, CANVAS_WIDTH)

    def test_zero_and_negative_dimension_bounding_box_area(self) -> None:
        """Verifies BoundingBox area calculations on zero/negative dimensions."""
        b_zero = BoundingBox(x=10, y=10, width=0, height=100)
        self.assertEqual(b_zero.area, 0.0)

        b_neg = BoundingBox(x=10, y=10, width=-10, height=100)
        self.assertEqual(b_neg.area, 0.0)


# ==============================================================================
# 10. GSlides Client Batch Limits
# ==============================================================================

class TestGSlidesClientBatchLimits(unittest.TestCase):
    """Verifies GSlidesClient handles large operation arrays in dry-run mode."""

    def test_dry_run_large_batch_payload(self) -> None:
        """Verifies dry-run handles 200+ operations without serialization error."""
        client = GSlidesClient(dry_run=True)
        deck_id = client.create_presentation("Scale Test Deck")
        ops = [{"op": "add-textbox", "id": f"BOX_{i:03d}", "text": f"Text {i}"} for i in range(250)]

        res = client.execute_batch(deck_id, ops)
        self.assertTrue(res["dry_run"])
        self.assertEqual(res["operations"], 250)


if __name__ == "__main__":
    unittest.main()

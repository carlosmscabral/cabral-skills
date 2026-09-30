"""Unit Tests for Multimodal Visual QA Verifier & Report Generator.

Tests:
1. QAVerifier spec validation, character budgets, and speaker notes completeness.
2. Bounding box safe canvas containment (720x405 pt) and sibling overlap collision math.
3. WCAG 2.1 AA/AAA contrast ratio verification across foreground/background pairs.
4. Text capacity and line overflow estimation heuristics.
5. QAReport serialization and summary formatting.
6. QAReportGenerator Markdown report tables and interactive HTML preview gallery for all 8 archetypes.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from preso.compiler.batch_generator import BatchCompiler
from preso.compiler.gslides_client import GSlidesClient
from preso.engine.archetypes import ArchetypeEngine
from preso.engine.design_tokens import (
    COLOR_BG_LIGHT,
    COLOR_BLUE_ACCENT,
    COLOR_BLUE_LIGHT,
    COLOR_BLUE_TEXT,
    COLOR_CARD_WHITE,
    COLOR_GREEN_LIGHT,
    COLOR_GREEN_TEXT,
    COLOR_NAVY_PRIMARY,
    COLOR_RED_LIGHT,
    COLOR_RED_TEXT,
)
from preso.qa.report_generator import QAReportGenerator
from preso.qa.verifier import (
    QAReport,
    QAVerifier,
    SAFE_BOUNDS_X_MAX,
    SAFE_BOUNDS_X_MIN,
    SAFE_BOUNDS_Y_MAX,
    SAFE_BOUNDS_Y_MIN,
)
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


class TestQAVerifierSpec(unittest.TestCase):
    """Tests specification validation within the QA verification engine."""

    def setUp(self) -> None:
        self.verifier = QAVerifier()
        self.valid_spec = SpecScaffolder.scaffold_preset("minimal")

    def test_verify_valid_spec(self) -> None:
        """Verifies that a valid presentation spec passes spec validation cleanly."""
        is_valid, viols, warns, metrics = self.verifier.verify_spec(self.valid_spec)
        self.assertTrue(is_valid)
        self.assertEqual(len(viols), 0)
        self.assertTrue(metrics["spec_valid"])
        self.assertEqual(metrics["spec_error_count"], 0)

    def test_verify_spec_with_title_overflow_violation(self) -> None:
        """Verifies that title text exceeding the 60-character budget triggers an error."""
        invalid_spec = SpecScaffolder.scaffold_preset("minimal")
        invalid_spec.chapters[0].slides[0].title = "A" * 75  # Limit is 60

        is_valid, viols, warns, metrics = self.verifier.verify_spec(invalid_spec)
        self.assertFalse(is_valid)
        self.assertGreaterEqual(len(viols), 1)
        self.assertFalse(metrics["spec_valid"])
        self.assertTrue(any("title exceeds" in v["message"] or "exceeds 60" in v["message"] for v in viols))

    def test_verify_spec_from_yaml_file_path(self) -> None:
        """Verifies that verify_spec accepts a Path object pointing to a YAML file."""
        with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
            f.write(self.valid_spec.to_yaml())
            tmp_path = Path(f.name)

        try:
            is_valid, viols, warns, metrics = self.verifier.verify_spec(tmp_path)
            self.assertTrue(is_valid)
            self.assertEqual(len(viols), 0)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


class TestQAVerifierGeometry(unittest.TestCase):
    """Tests 2D coordinate canvas containment and overlap collision detection."""

    def setUp(self) -> None:
        self.verifier = QAVerifier()

    def test_canvas_containment_pass(self) -> None:
        """Verifies that elements within 720x405 pt canvas pass geometry checks."""
        ops = [
            {"op": "add-slide", "id": "SLIDE_01"},
            {"op": "add-shape", "id": "CARD_1", "shape": "RECTANGLE", "x": 36.0, "y": 100.0, "width": 310.0, "height": 260.0},
            {"op": "add-textbox", "id": "TXT_1", "text": "Card Header", "x": 50.0, "y": 115.0, "width": 280.0, "height": 30.0},
        ]
        viols, warns, metrics, elem_records = self.verifier.verify_batch_geometry(ops)
        self.assertEqual(len(viols), 0)
        self.assertEqual(metrics["out_of_bounds_count"], 0)
        self.assertEqual(metrics["overlap_collision_count"], 0)
        self.assertEqual(len(elem_records), 2)

    def test_canvas_out_of_bounds_detection(self) -> None:
        """Verifies that elements extending past the 720x405 pt boundary trigger violations."""
        ops = [
            {"op": "add-slide", "id": "SLIDE_01"},
            {"op": "add-shape", "id": "OVERFLOW_ELEM", "shape": "RECTANGLE", "x": 600.0, "y": 300.0, "width": 150.0, "height": 120.0},  # x+w = 750 > 720, y+h = 420 > 405
        ]
        viols, warns, metrics, elem_records = self.verifier.verify_batch_geometry(ops)
        self.assertGreaterEqual(len(viols), 1)
        self.assertGreaterEqual(metrics["out_of_bounds_count"], 1)
        self.assertTrue(any("exceeds canvas boundaries" in v["message"] for v in viols))

    def test_overlap_collision_detection(self) -> None:
        """Verifies that intersecting sibling content elements trigger collision errors."""
        ops = [
            {"op": "add-slide", "id": "SLIDE_01"},
            # Two distinct sibling cards that overlap heavily
            {"op": "add-shape", "id": "CARD_A", "shape": "RECTANGLE", "x": 100.0, "y": 100.0, "width": 200.0, "height": 150.0},
            {"op": "add-shape", "id": "CARD_B", "shape": "RECTANGLE", "x": 200.0, "y": 150.0, "width": 200.0, "height": 150.0},
        ]
        viols, warns, metrics, elem_records = self.verifier.verify_batch_geometry(ops)
        self.assertGreaterEqual(len(viols), 1)
        self.assertGreaterEqual(metrics["overlap_collision_count"], 1)
        self.assertTrue(any("Improper overlap" in v["message"] for v in viols))

    def test_nested_container_child_is_not_flagged_as_collision(self) -> None:
        """Verifies that a textbox contained inside a card background shape is not flagged as a collision."""
        ops = [
            {"op": "add-slide", "id": "SLIDE_01"},
            {"op": "add-shape", "id": "CARD_BG", "shape": "RECTANGLE", "x": 50.0, "y": 100.0, "width": 300.0, "height": 200.0},
            {"op": "add-textbox", "id": "CARD_TXT", "text": "Inside Card", "x": 65.0, "y": 115.0, "width": 270.0, "height": 40.0},
        ]
        viols, warns, metrics, elem_records = self.verifier.verify_batch_geometry(ops)
        self.assertEqual(len(viols), 0)
        self.assertEqual(metrics["overlap_collision_count"], 0)


class TestQAVerifierContrast(unittest.TestCase):
    """Tests WCAG 2.1 AA/AAA contrast ratio verification."""

    def setUp(self) -> None:
        self.verifier = QAVerifier()

    def test_blueprint_palette_pairings_meet_wcag_aa(self) -> None:
        """Verifies that standard Blueprint high-contrast pairings pass WCAG AA."""
        ops = [
            {"op": "add-slide", "id": "SLIDE_01"},
            {"op": "set-background", "color": COLOR_BG_LIGHT},
            {"op": "add-shape", "id": "PILL_BG", "shape": "ROUND_RECTANGLE", "background_color": COLOR_BLUE_LIGHT, "x": 50.0, "y": 100.0, "width": 80.0, "height": 20.0},
            {"op": "add-textbox", "id": "PILL_TXT", "text": "CATEGORY", "color": COLOR_BLUE_TEXT, "font_size": 10.0, "x": 50.0, "y": 100.0, "width": 80.0, "height": 20.0},
            {"op": "add-shape", "id": "CARD_BG", "shape": "RECTANGLE", "background_color": COLOR_CARD_WHITE, "x": 50.0, "y": 130.0, "width": 300.0, "height": 200.0},
            {"op": "add-textbox", "id": "CARD_HDR", "text": "Card Title", "color": "#202124", "font_size": 16.0, "bold": True, "x": 65.0, "y": 145.0, "width": 270.0, "height": 30.0},
        ]
        viols, warns, metrics, records = self.verifier.verify_contrast(ops)
        self.assertEqual(len(viols), 0)
        self.assertEqual(metrics["contrast_failures"], 0)
        self.assertEqual(metrics["wcag_aa_compliance_pct"], 100.0)
        self.assertGreaterEqual(metrics["min_contrast_ratio"], 4.5)

    def test_low_contrast_pairing_fails_wcag_aa(self) -> None:
        """Verifies that an inaccessible color combination triggers a WCAG AA contrast failure."""
        ops = [
            {"op": "add-slide", "id": "SLIDE_01"},
            {"op": "set-background", "color": "#FFFFFF"},
            {"op": "add-textbox", "id": "BAD_TXT", "text": "Invisible Text", "color": "#CCCCCC", "font_size": 12.0, "x": 50.0, "y": 100.0, "width": 200.0, "height": 30.0},
        ]
        viols, warns, metrics, records = self.verifier.verify_contrast(ops)
        self.assertGreaterEqual(len(viols), 1)
        self.assertGreaterEqual(metrics["contrast_failures"], 1)
        self.assertLess(metrics["wcag_aa_compliance_pct"], 100.0)
        self.assertTrue(any("WCAG AA contrast violation" in v["message"] for v in viols))


class TestQAVerifierSpeakerNotesAndOverflow(unittest.TestCase):
    """Tests speaker notes audit and text overflow heuristics."""

    def setUp(self) -> None:
        self.verifier = QAVerifier()

    def test_speaker_notes_presence_audit(self) -> None:
        """Missing speaker notes are optional: no violations or warnings, coverage is informational."""
        spec = SpecScaffolder.scaffold_preset("minimal")
        spec.chapters[0].slides[1].notes = ""
        spec.chapters[0].slides[1].speaker_notes = ""

        viols, warns, metrics = self.verifier.verify_speaker_notes(spec=spec)
        self.assertEqual(len(viols), 0)
        self.assertLess(metrics["speaker_notes_coverage_pct"], 100.0)
        self.assertEqual(warns, [])

    def test_text_overflow_detection_on_extreme_content(self) -> None:
        """Verifies that extreme text content in a small box triggers an overflow warning."""
        huge_text = "This is a very long paragraph that goes on and on and on and exceeds any reasonable capacity " * 10
        ops = [
            {"op": "add-slide", "id": "SLIDE_01"},
            {"op": "add-textbox", "id": "TINY_BOX", "text": huge_text, "font_size": 14.0, "x": 50.0, "y": 100.0, "width": 100.0, "height": 30.0},
        ]
        viols, warns, metrics, records = self.verifier.verify_text_overflow(ops)
        self.assertGreaterEqual(metrics["text_overflow_warnings"], 1)
        self.assertTrue(any("Potential text overflow" in w["message"] for w in warns))


class TestQAReportGenerator(unittest.TestCase):
    """Tests Markdown report generation and HTML preview gallery creation."""

    def setUp(self) -> None:
        self.spec = SpecScaffolder.scaffold_preset("ai_factory")
        self.verifier = QAVerifier()
        self.qa_report = self.verifier.verify(self.spec)

    def test_qa_report_metrics_and_summary(self) -> None:
        """Verifies QAReport data model, serialization, and summary formatting."""
        self.assertTrue(self.qa_report.is_passing)
        self.assertGreater(self.qa_report.total_checks, 50)
        self.assertGreater(self.qa_report.passed_checks, 50)

        # Serialization
        d = self.qa_report.to_dict()
        self.assertIn("is_passing", d)
        self.assertIn("metrics", d)

        json_str = self.qa_report.to_json()
        self.assertIn('"is_passing": true', json_str)

        summary_text = self.qa_report.summary()
        self.assertIn("QA VERIFICATION REPORT: PASS", summary_text)
        self.assertIn("WCAG Compliance:", summary_text)

    def test_generate_markdown_report_structure(self) -> None:
        """Verifies that generate_markdown_report produces structured tables."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "qa_report.md"
            md = QAReportGenerator.generate_markdown_report(
                qa_report=self.qa_report,
                output_path=out_file,
                spec=self.spec,
            )
            self.assertTrue(out_file.exists())
            self.assertIn("# Visual QA & Verification Audit Report", md)
            self.assertIn("## 1. Executive Verification Metrics", md)
            self.assertIn("## 2. Slide-by-Slide Verification Matrix", md)
            self.assertIn("## 5. WCAG 2.1 Contrast Analysis Detail", md)
            self.assertIn("WCAG 2.1 AA Contrast Compliance", md)

    def test_generate_html_preview_covers_all_archetypes(self) -> None:
        """Verifies that generate_html_preview renders mockups for all 8 archetypes."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "preview.html"
            html_content = QAReportGenerator.generate_html_preview(
                spec=self.spec,
                qa_report=self.qa_report,
                output_path=out_file,
            )
            self.assertTrue(out_file.exists())
            self.assertIn("<!DOCTYPE html>", html_content)
            self.assertIn("The AI Factory Blueprint", html_content)

            # Check that mockup classes and archetypes are present
            self.assertIn("arch-chapter-divider", html_content)
            self.assertIn("arch-split-cards", html_content)
            self.assertIn("arch-code-terminal", html_content)
            self.assertIn("arch-hero-metrics", html_content)
            self.assertIn("arch-ladder-hierarchy", html_content)
            self.assertIn("arch-executive-grid", html_content)
            self.assertIn("arch-dodont-checklist", html_content)
            self.assertIn("arch-takeaways", html_content)

            # Check interactive gallery controls
            self.assertIn("openLightbox", html_content)
            self.assertIn("toggleNotes", html_content)
            self.assertIn("slide-viewport-wrapper", html_content)

    def test_generate_all_artifacts(self) -> None:
        """Verifies generate_all generates both markdown report and html preview in target directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            res = QAReportGenerator.generate_all(
                spec=self.spec,
                output_dir=tmp_dir,
                qa_report=self.qa_report,
            )
            self.assertTrue(res["report_path"].exists())
            self.assertTrue(res["preview_path"].exists())
            self.assertTrue(res["is_passing"])


if __name__ == "__main__":
    unittest.main()

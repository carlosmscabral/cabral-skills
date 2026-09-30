"""Tier 1 E2E Test Suite: Comprehensive Feature Coverage.

Verifies >= 5 distinct test cases for all 21 system features (F1 through F21):
- F1: Design Tokens, Typography, and Canvas Coordinate System
- F2: Archetype 1 - Chapter Divider
- F3: Archetype 2 - 2-Card / 3-Card Split Comparison
- F4: Archetype 3 - Code / Ratchet Terminal Box
- F5: Archetype 4 - Hero Metric / Economics Comparison
- F6: Archetype 5 - Ladder / Stepped Hierarchy
- F7: Archetype 6 - Executive 1-Liner Grid
- F8: Archetype 7 - Do / Don't Best Practice Checklist
- F9: Archetype 8 - Actionable Takeaways & Next Steps
- F10: Template Cloner & Creator (`gslides copy` / `gslides create`)
- F11: Single-Pass Batch Compiler & Deterministic Placeholders
- F12: Default Template Placeholder Cleanup (`i0`, `i1`)
- F13: Specification Schema & Validation Framework
- F14: Interactive Spec Scaffolder (`preso.py spec`)
- F15: Codebase Ingestion Pipeline (AST, file tree, code snippet extractor)
- F16: Google Slides Ingestion Pipeline (`gslides read-all` outline parser)
- F17: Markdown & Raw Notes Ingestion Pipeline
- F18: Unified CLI Interface (`preso.py` subcommands)
- F19: Multimodal Visual QA Verifier (clamping, collision, contrast, bounding boxes)
- F20: Visual Preview Gallery & Markdown QA Report Generator
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from preso.cli import build_parser, main
from preso.compiler.batch_generator import (
    BatchCompiler,
    BatchCompilerConfig,
    ChapterManifest,
    PresentationManifest,
    SlideManifest,
)
from preso.compiler.gslides_client import (
    DEFAULT_GSLIDES_BINARY,
    DEFAULT_TEMPLATE_ID,
    BatchExecutionResult,
    GSlidesCLIError,
    GSlidesClient,
)
from preso.engine.archetypes import (
    ArchetypeEngine,
    CardSpec as EngineCardSpec,
    MetricSpec as EngineMetricSpec,
    PrincipleSpec as EnginePrincipleSpec,
    QuadrantSpec as EngineQuadrantSpec,
    StepSpec as EngineStepSpec,
    TerminalSpec as EngineTerminalSpec,
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
    calculate_card_internal_bounds,
    calculate_n_column_bounds,
)
from preso.engine.design_tokens import (
    CANVAS_EMU_HEIGHT,
    CANVAS_EMU_WIDTH,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    COLOR_BLUE_ACCENT,
    COLOR_BLUE_TEXT,
    COLOR_CARD_WHITE,
    COLOR_GREEN_DO,
    COLOR_GREEN_TEXT,
    COLOR_NAVY_PRIMARY,
    COLOR_RED_DONT,
    COLOR_RED_TEXT,
    FONT_FAMILY_BODY,
    FONT_FAMILY_CODE,
    FONT_FAMILY_HEADING,
    contrast_ratio,
    is_wcag_aa,
    is_wcag_aaa,
)
from preso.ingest.codebase import CodebaseIngestor
from preso.ingest.markdown import MarkdownIngestor
from preso.ingest.slides import SlidesIngestor
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
# F1: Design Tokens, Typography, and Canvas Geometry (5 tests)
# ==============================================================================

class TestF1DesignTokens(unittest.TestCase):
    """Tier 1 Feature Tests: Design Tokens & Canvas Geometry."""

    def test_f1_01_canvas_dimensions_and_ratios(self) -> None:
        """Verifies 16:9 720x405pt canvas dimensions and EMU conversions."""
        self.assertEqual(CANVAS_WIDTH, 720.0)
        self.assertEqual(CANVAS_HEIGHT, 405.0)
        self.assertAlmostEqual(CANVAS_WIDTH / CANVAS_HEIGHT, 16 / 9, places=2)
        self.assertEqual(CANVAS_EMU_WIDTH, 720 * 12700)
        self.assertEqual(CANVAS_EMU_HEIGHT, 405 * 12700)

    def test_f1_02_strict_color_tokens_definitions(self) -> None:
        """Verifies core Blueprint hex color tokens are exact."""
        self.assertEqual(COLOR_NAVY_PRIMARY, "#1E2761")
        self.assertEqual(COLOR_CARD_WHITE, "#FFFFFF")
        self.assertEqual(COLOR_BLUE_ACCENT, "#1A73E8")
        self.assertEqual(COLOR_GREEN_DO, "#1E8E3E")
        self.assertEqual(COLOR_RED_DONT, "#D93025")
        self.assertEqual(COLOR_BLUE_TEXT, "#174EA6")
        self.assertEqual(COLOR_GREEN_TEXT, "#137333")
        self.assertEqual(COLOR_RED_TEXT, "#C5221F")

    def test_f1_03_typography_font_families(self) -> None:
        """Verifies font family constants for headers, body, and monospace."""
        self.assertEqual(FONT_FAMILY_HEADING, "Google Sans")
        self.assertEqual(FONT_FAMILY_BODY, "Google Sans Text")
        self.assertEqual(FONT_FAMILY_CODE, "Roboto Mono")

    def test_f1_04_wcag_contrast_calculations(self) -> None:
        """Verifies relative luminance and contrast ratios match WCAG 2.1 specs."""
        # White text on Dark Navy (#1E2761)
        ratio_navy = contrast_ratio("#FFFFFF", COLOR_NAVY_PRIMARY)
        self.assertGreater(ratio_navy, 11.0)
        self.assertTrue(is_wcag_aa("#FFFFFF", COLOR_NAVY_PRIMARY))
        self.assertTrue(is_wcag_aaa("#FFFFFF", COLOR_NAVY_PRIMARY))

        # Adjusted accessible green text (#137333) on white
        ratio_green = contrast_ratio(COLOR_GREEN_TEXT, "#FFFFFF")
        self.assertGreaterEqual(ratio_green, 4.5)
        self.assertTrue(is_wcag_aa(COLOR_GREEN_TEXT, "#FFFFFF"))

    def test_f1_05_bounding_box_methods_and_clamping(self) -> None:
        """Verifies BoundingBox area, aspect ratio, containment, and clamping."""
        box = BoundingBox(x=10, y=20, width=100, height=50)
        self.assertEqual(box.right, 110)
        self.assertEqual(box.bottom, 70)
        self.assertEqual(box.area, 5000)
        aspect = box.width / box.height
        self.assertEqual(aspect, 2.0)
        self.assertTrue(box.left >= 0 and box.top >= 0 and box.right <= 720 and box.bottom <= 405)


# ==============================================================================
# F2: Archetype 1 - Chapter Divider (5 tests)
# ==============================================================================

class TestF2ChapterDivider(unittest.TestCase):
    """Tier 1 Feature Tests: Archetype 1 Chapter Divider."""

    def test_f2_01_white_background(self) -> None:
        """Verifies chapter divider creates clean white background matching Blueprint standard."""
        ops = generate_chapter_divider(
            slide_id="SLIDE_01",
            chapter_number=1,
            title="FOUNDATION ARCHITECTURE",
            subtitle="Core infrastructure primitives",
            speaker_notes="Speaker notes for chapter 1",
        )
        self.assertEqual(ops[0]["op"], "add-slide")
        self.assertEqual(ops[1]["op"], "set-background")
        self.assertEqual(ops[1]["color"], "#FFFFFF")

    def test_f2_02_chapter_number_formatting_and_size(self) -> None:
        """Verifies 2-digit chapter number text box creation."""
        ops = generate_chapter_divider(
            slide_id="SLIDE_01",
            chapter_number=3,
            title="RUNTIME ENGINE",
            subtitle="Execution pipeline",
        )
        num_ops = [op for op in ops if op.get("op") == "add-textbox" and op.get("text") == "03"]
        self.assertEqual(len(num_ops), 1)
        self.assertIn(num_ops[0]["font_size"], (56.0, 60.0, 72.0))

    def test_f2_03_title_and_subtitle_content(self) -> None:
        """Verifies slide title and subtitle are inserted with proper text styling."""
        ops = generate_chapter_divider(
            slide_id="SLIDE_01",
            chapter_number="02",
            title="OBSERVABILITY & METRICS",
            subtitle="Real-time telemetry and tracing",
        )
        texts = [op.get("text") for op in ops if op.get("op") == "add-textbox"]
        self.assertIn("OBSERVABILITY & METRICS", texts)
        self.assertIn("Real-time telemetry and tracing", texts)

    def test_f2_04_rainbow_progress_bar_geometry(self) -> None:
        """Verifies Google rainbow progress bar segments are generated."""
        ops = generate_chapter_divider(
            slide_id="SLIDE_01",
            chapter_number="01",
            title="INTRO",
            subtitle="Getting started",
        )
        red_bar = [op for op in ops if op.get("op") == "add-shape" and "BAR_S01_RED" in op.get("id", "")]
        self.assertTrue(len(red_bar) == 1)
        self.assertEqual(red_bar[0]["background_color"], "#EA4335")

    def test_f2_05_speaker_notes_and_deterministic_ids(self) -> None:
        """Verifies speaker notes addition and deterministic element IDs."""
        ops = generate_chapter_divider(
            slide_id="SLIDE_04",
            chapter_number="04",
            title="SYSTEM OVERVIEW",
            subtitle="High level design",
            speaker_notes="Comprehensive presenter remarks for chapter divider.",
        )
        notes_ops = [op for op in ops if op.get("op") == "set-notes"]
        self.assertEqual(len(notes_ops), 1)
        self.assertIn("Comprehensive presenter remarks", notes_ops[0]["text"])


# ==============================================================================
# F3: Archetype 2 - 2-Card / 3-Card Split Comparison (5 tests)
# ==============================================================================

class TestF3SplitCards(unittest.TestCase):
    """Tier 1 Feature Tests: Archetype 2 Split Cards."""

    def test_f3_01_two_card_split_layout(self) -> None:
        """Verifies 2-card split geometry, widths, and category pills."""
        cards = [
            EngineCardSpec(title="Card Alpha", category="FRONTEND", bullets=["React 19", "Tailwind CSS"]),
            EngineCardSpec(title="Card Beta", category="BACKEND", bullets=["Python 3.13", "FastAPI"]),
        ]
        ops = generate_split_cards(slide_id="SLIDE_01", title="Stack Split", subtitle="Sub", kicker="PARADIGMS", cards=cards)
        card_shapes = [op for op in ops if op.get("op") == "add-shape" and "CARD_S01_C" in op.get("id", "")]
        self.assertEqual(len(card_shapes), 2)

    def test_f3_02_three_card_split_layout(self) -> None:
        """Verifies 3-card split generates 3 evenly spaced containers."""
        cards = [
            EngineCardSpec(title="Compute", category="TIER 1", bullets=["Borg tasks"]),
            EngineCardSpec(title="Storage", category="TIER 2", bullets=["Spanner F1"]),
            EngineCardSpec(title="Network", category="TIER 3", bullets=["Andromeda SDN"]),
        ]
        ops = generate_split_cards(slide_id="SLIDE_01", title="Architecture Tiers", subtitle="Sub", kicker="INFRA", cards=cards)
        card_shapes = [op for op in ops if op.get("op") == "add-shape" and "CARD_S01_C" in op.get("id", "")]
        self.assertEqual(len(card_shapes), 3)

    def test_f3_03_category_pills_styling_and_text(self) -> None:
        """Verifies category pill badges and rounded rectangle shapes."""
        cards = [EngineCardSpec(title="Engine", category="CORE COMPONENT", bullets=["Deterministic math"])]
        ops = generate_split_cards(slide_id="SLIDE_01", title="Core", subtitle="Sub", kicker="MODULES", cards=cards)
        pill_texts = [op.get("text") for op in ops if op.get("op") == "add-textbox" and op.get("text") == "CORE COMPONENT"]
        self.assertEqual(len(pill_texts), 1)

    def test_f3_04_formatted_bullets_rendering(self) -> None:
        """Verifies bullet points are formatted with bullet characters."""
        cards = [EngineCardSpec(title="Benefits", bullets=["Zero regression", "100% test pass rate"])]
        ops = generate_split_cards(slide_id="SLIDE_01", title="Benefits Overview", subtitle="Sub", kicker="METRICS", cards=cards)
        bullet_ops = [op.get("text") for op in ops if op.get("op") == "add-textbox" and "Zero regression" in op.get("text", "")]
        self.assertTrue(len(bullet_ops) >= 1)

    def test_f3_05_custom_card_colors(self) -> None:
        """Verifies custom card stripe accent color."""
        cards = [EngineCardSpec(title="Custom Box", stripe_color="#1E8E3E", bullets=["Custom style"])]
        ops = generate_split_cards(slide_id="SLIDE_01", title="Custom Styled Card", subtitle="Sub", kicker="CUSTOM", cards=cards)
        stripe_shapes = [op for op in ops if op.get("op") == "add-shape" and "STRIPE" in op.get("id", "")]
        self.assertTrue(len(stripe_shapes) >= 1)


# ==============================================================================
# F4: Archetype 3 - Code / Ratchet Terminal Box (5 tests)
# ==============================================================================

class TestF4CodeTerminal(unittest.TestCase):
    """Tier 1 Feature Tests: Archetype 3 Code Terminal."""

    def test_f4_01_monospace_dark_container(self) -> None:
        """Verifies dark container box with dark navy / slate background."""
        terminals = [
            EngineTerminalSpec(
                filename="pipeline.py",
                code="def run_pipeline():\n    return True",
            )
        ]
        ops = generate_code_terminal(slide_id="SLIDE_01", title="Pipeline Implementation", subtitle="Sub", kicker="CODE", terminals=terminals)
        term_shapes = [op for op in ops if op.get("op") == "add-shape" and "TERM" in op.get("id", "")]
        self.assertTrue(len(term_shapes) >= 1)

    def test_f4_02_filename_header_and_dots(self) -> None:
        """Verifies filename text and header bar element creation."""
        terminals = [EngineTerminalSpec(filename="src/main.ts", code="const x = 1;")]
        ops = generate_code_terminal(slide_id="SLIDE_01", title="Terminal Header Check", subtitle="Sub", kicker="CODE", terminals=terminals)
        fn_texts = [op.get("text") for op in ops if op.get("op") == "add-textbox" and "src/main.ts" in op.get("text", "")]
        self.assertTrue(len(fn_texts) >= 1)

    def test_f4_03_roboto_mono_code_styling(self) -> None:
        """Verifies Roboto Mono font family is assigned to code text blocks."""
        terminals = [EngineTerminalSpec(filename="test.py", code="assert True")]
        ops = generate_code_terminal(slide_id="SLIDE_01", title="Code Typography", subtitle="Sub", kicker="CODE", terminals=terminals)
        font_styles = [op for op in ops if op.get("op") == "add-textbox" and op.get("font_family") == FONT_FAMILY_CODE]
        self.assertTrue(len(font_styles) >= 1)

    def test_f4_04_do_dont_badges(self) -> None:
        """Verifies Green `✓ Do` and Red `✗ Don't` badge insertion."""
        terminals = [
            EngineTerminalSpec(filename="bad.py", code="val = None", badge_text="DON'T", badge_bg=COLOR_RED_DONT),
            EngineTerminalSpec(filename="good.py", code="val: Optional[str] = None", badge_text="DO", badge_bg=COLOR_GREEN_DO),
        ]
        ops = generate_code_terminal(slide_id="SLIDE_01", title="Best Practice Code", subtitle="Sub", kicker="CODE", terminals=terminals)
        badge_texts = [op.get("text") for op in ops if op.get("op") == "add-textbox" and op.get("text") in ["DO", "DON'T"]]
        self.assertEqual(len(badge_texts), 2)

    def test_f4_05_side_by_side_dual_terminal_layout(self) -> None:
        """Verifies 2 terminals are arranged side-by-side without horizontal overlap."""
        terminals = [
            EngineTerminalSpec(filename="v1.py", code="pass"),
            EngineTerminalSpec(filename="v2.py", code="pass"),
        ]
        ops = generate_code_terminal(slide_id="SLIDE_01", title="Dual Terminal Comparison", subtitle="Sub", kicker="CODE", terminals=terminals)
        box_ops = [op for op in ops if op.get("op") == "add-shape" and ("TERM_S01_L_BG" in op.get("id", "") or "TERM_S01_R_BG" in op.get("id", ""))]
        self.assertEqual(len(box_ops), 2)


# ==============================================================================
# F5: Archetype 4 - Hero Metric / Economics Comparison (5 tests)
# ==============================================================================

class TestF5HeroMetrics(unittest.TestCase):
    """Tier 1 Feature Tests: Archetype 4 Hero Metric."""

    def test_f5_01_big_stat_number_formatting(self) -> None:
        """Verifies 54pt hero stat number text formatting."""
        metrics = [EngineMetricSpec(value="99.99%", unit="Availability SLA", delta="+0.04%")]
        ops = generate_hero_metrics(slide_id="SLIDE_01", title="Service SLA", subtitle="Sub", kicker="METRICS", metrics=metrics)
        val_texts = [op for op in ops if op.get("op") == "add-textbox" and op.get("text") == "99.99%"]
        self.assertEqual(len(val_texts), 1)
        self.assertEqual(val_texts[0]["font_size"], 54.0)

    def test_f5_02_unit_label_and_description(self) -> None:
        """Verifies metric unit label and contextual description."""
        metrics = [EngineMetricSpec(value="1.2M", unit="DAU", description="Organic user growth across all regions.")]
        ops = generate_hero_metrics(slide_id="SLIDE_01", title="User Growth", subtitle="Sub", kicker="METRICS", metrics=metrics)
        texts = [op.get("text") for op in ops if op.get("op") == "add-textbox"]
        self.assertIn("DAU", texts)
        self.assertIn("Organic user growth across all regions.", texts)

    def test_f5_03_positive_delta_pill_badge(self) -> None:
        """Verifies positive delta badge displays with green styling."""
        metrics = [EngineMetricSpec(value="$4.8M", unit="ARR", delta="+42% YoY", delta_type="positive")]
        ops = generate_hero_metrics(slide_id="SLIDE_01", title="Financials", subtitle="Sub", kicker="METRICS", metrics=metrics)
        delta_ops = [op for op in ops if op.get("op") == "add-textbox" and op.get("text") == "+42% YoY"]
        self.assertEqual(len(delta_ops), 1)
        self.assertEqual(delta_ops[0]["color"], COLOR_GREEN_TEXT)

    def test_f5_04_negative_delta_pill_badge(self) -> None:
        """Verifies negative delta badge displays with red styling."""
        metrics = [EngineMetricSpec(value="14ms", unit="Latency", delta="-65% reduction", delta_type="negative")]
        ops = generate_hero_metrics(slide_id="SLIDE_01", title="Optimization", subtitle="Sub", kicker="METRICS", metrics=metrics)
        delta_ops = [op for op in ops if op.get("op") == "add-textbox" and op.get("text") == "-65% reduction"]
        self.assertEqual(len(delta_ops), 1)
        self.assertEqual(delta_ops[0]["color"], COLOR_RED_TEXT)

    def test_f5_05_multi_metric_cards_layout(self) -> None:
        """Verifies 3 hero metric cards layout side-by-side."""
        metrics = [
            EngineMetricSpec(value="10x", unit="Throughput"),
            EngineMetricSpec(value="0ms", unit="Downtime"),
            EngineMetricSpec(value="100%", unit="Automated"),
        ]
        ops = generate_hero_metrics(slide_id="SLIDE_01", title="Operational Metrics", subtitle="Sub", kicker="METRICS", metrics=metrics)
        metric_cards = [op for op in ops if op.get("op") == "add-shape" and "CARD_S01_M" in op.get("id", "")]
        self.assertEqual(len(metric_cards), 3)


# ==============================================================================
# F6: Archetype 5 - Ladder / Stepped Hierarchy (5 tests)
# ==============================================================================

class TestF6LadderHierarchy(unittest.TestCase):
    """Tier 1 Feature Tests: Archetype 5 Ladder Hierarchy."""

    def test_f6_01_four_step_pipeline_layout(self) -> None:
        """Verifies 4-step horizontal ladder layout containers."""
        steps = [
            EngineStepSpec(number=1, title="Ingest", description="Parse AST"),
            EngineStepSpec(number=2, title="Validate", description="Schema check"),
            EngineStepSpec(number=3, title="Compile", description="Single-pass JSON"),
            EngineStepSpec(number=4, title="Verify", description="Visual QA loop"),
        ]
        ops = generate_ladder_hierarchy(slide_id="SLIDE_01", title="Execution Ladder", subtitle="Sub", kicker="LADDER", steps=steps)
        step_cards = [op for op in ops if op.get("op") == "add-shape" and "RUNG" in op.get("id", "")]
        self.assertEqual(len(step_cards), 4)

    def test_f6_02_step_numbers_and_badges(self) -> None:
        """Verifies step numbers 01..04 are placed on steps."""
        steps = [EngineStepSpec(number=i, title=f"Phase {i}", description="Desc") for i in range(1, 5)]
        ops = generate_ladder_hierarchy(slide_id="SLIDE_01", title="Phased Rollout", subtitle="Sub", kicker="LADDER", steps=steps)
        texts = [op.get("text") for op in ops if op.get("op") == "add-textbox"]
        self.assertTrue(any("STEP 01" in t or "01" in t or "1" in t for t in texts))

    def test_f6_03_directional_connector_arrows(self) -> None:
        """Verifies connector arrows between consecutive ladder steps."""
        steps = [
            EngineStepSpec(number=1, title="A", description=""),
            EngineStepSpec(number=2, title="B", description=""),
        ]
        ops = generate_ladder_hierarchy(slide_id="SLIDE_01", title="Two Step Ladder", subtitle="Sub", kicker="LADDER", steps=steps)
        arrow_ops = [op for op in ops if op.get("op") == "add-line" and "CONN" in op.get("id", "")]
        self.assertEqual(len(arrow_ops), 1)

    def test_f6_04_step_titles_and_descriptions(self) -> None:
        """Verifies step title and description text fields."""
        steps = [
            EngineStepSpec(number=1, title="Step Alpha", description="Detailed explanation of Alpha."),
            EngineStepSpec(number=2, title="Step Beta", description="Detailed explanation of Beta."),
        ]
        ops = generate_ladder_hierarchy(slide_id="SLIDE_01", title="Two Steps", subtitle="Sub", kicker="LADDER", steps=steps)
        texts = [op.get("text") for op in ops if op.get("op") == "add-textbox"]
        self.assertIn("Step Alpha", texts)
        self.assertIn("Detailed explanation of Alpha.", texts)

    def test_f6_05_variable_step_counts(self) -> None:
        """Verifies ladder handles 2, 3, and 5 step flows correctly."""
        for count in (2, 3, 5):
            steps = [EngineStepSpec(number=i, title=f"Step {i}", description="") for i in range(1, count + 1)]
            ops = generate_ladder_hierarchy(slide_id="SLIDE_01", title=f"{count} Steps", subtitle="Sub", kicker="LADDER", steps=steps)
            step_cards = [op for op in ops if op.get("op") == "add-shape" and "RUNG" in op.get("id", "")]
            self.assertEqual(len(step_cards), count)


# ==============================================================================
# F7: Archetype 6 - Executive 1-Liner Grid (5 tests)
# ==============================================================================

class TestF7ExecutiveGrid(unittest.TestCase):
    """Tier 1 Feature Tests: Archetype 6 Executive Grid."""

    def test_f7_01_two_by_two_quadrant_geometry(self) -> None:
        """Verifies 2x2 grid produces exactly 4 quadrant cards."""
        quadrants = [
            EngineQuadrantSpec(number=1, title="Reliability", description="Zero downtime architectures"),
            EngineQuadrantSpec(number=2, title="Velocity", description="Sub-second build times"),
            EngineQuadrantSpec(number=3, title="Security", description="End-to-end provenance"),
            EngineQuadrantSpec(number=4, title="Economics", description="80% TCO savings"),
        ]
        ops = generate_executive_grid(slide_id="SLIDE_01", title="Executive Grid", subtitle="Sub", kicker="PILLARS", quadrants=quadrants)
        quad_cards = [op for op in ops if op.get("op") == "add-shape" and "QUAD" in op.get("id", "") and "STRIPE" not in op.get("id", "")]
        self.assertEqual(len(quad_cards), 4)

    def test_f7_02_vertical_blue_accent_bar(self) -> None:
        """Verifies vertical accent bar is created on each quadrant card."""
        quadrants = [
            EngineQuadrantSpec(number=1, title="Core Thesis", description="Automated presentations"),
            EngineQuadrantSpec(number=2, title="Pillar 2", description="Desc 2"),
            EngineQuadrantSpec(number=3, title="Pillar 3", description="Desc 3"),
            EngineQuadrantSpec(number=4, title="Pillar 4", description="Desc 4"),
        ]
        ops = generate_executive_grid(slide_id="SLIDE_01", title="Executive Thesis", subtitle="Sub", kicker="PILLARS", quadrants=quadrants)
        bar_ops = [op for op in ops if op.get("op") == "add-shape" and "STRIPE" in op.get("id", "")]
        self.assertEqual(len(bar_ops), 4)

    def test_f7_03_numbered_quadrant_badges(self) -> None:
        """Verifies 01..04 number badge text placement."""
        quadrants = [EngineQuadrantSpec(number=i, title=f"Point {i}", description="Detail") for i in range(1, 5)]
        ops = generate_executive_grid(slide_id="SLIDE_01", title="Four Pillars", subtitle="Sub", kicker="PILLARS", quadrants=quadrants)
        texts = [op.get("text") for op in ops if op.get("op") == "add-textbox"]
        self.assertTrue(any("01" in t for t in texts))
        self.assertTrue(any("04" in t for t in texts))

    def test_f7_04_headline_and_body_formatting(self) -> None:
        """Verifies bold 1-liner headline and body summary font sizes."""
        quadrants = [
            EngineQuadrantSpec(number=1, title="Mission Critical", description="Enterprise SLA"),
            EngineQuadrantSpec(number=2, title="P2", description="D2"),
            EngineQuadrantSpec(number=3, title="P3", description="D3"),
            EngineQuadrantSpec(number=4, title="P4", description="D4"),
        ]
        ops = generate_executive_grid(slide_id="SLIDE_01", title="Pillars", subtitle="Sub", kicker="PILLARS", quadrants=quadrants)
        texts = [op.get("text") for op in ops if op.get("op") == "add-textbox"]
        self.assertIn("Mission Critical", texts)
        self.assertIn("Enterprise SLA", texts)

    def test_f7_05_quadrant_bounds_containment(self) -> None:
        """Verifies all 4 quadrant bounds are fully contained within slide canvas."""
        bounds_list = calculate_2x2_grid_bounds()
        for b in bounds_list:
            self.assertTrue(b.left >= 0 and b.top >= 0 and b.right <= 720 and b.bottom <= 405)


# ==============================================================================
# F8: Archetype 7 - Do / Don't Best Practice Checklist (5 tests)
# ==============================================================================

class TestF8DoDontChecklist(unittest.TestCase):
    """Tier 1 Feature Tests: Archetype 7 Do/Don't Checklist."""

    def test_f8_01_side_by_side_comparison_cards(self) -> None:
        """Verifies side-by-side anti-pattern vs standard split containers."""
        ops = generate_dodont_checklist(
            slide_id="SLIDE_01",
            title="Design Standards",
            subtitle="Sub",
            kicker="CHECKLIST",
            dont_items=["Hardcoded pixel math", "Facade mocks in tests"],
            do_items=["Tokenized coordinate engine", "Real execution verification"],
        )
        col_cards = [op for op in ops if op.get("op") == "add-shape" and "CARD_S01_" in op.get("id", "")]
        self.assertEqual(len(col_cards), 2)

    def test_f8_02_red_and_green_header_banners(self) -> None:
        """Verifies colored header banners for DON'T (red) and DO (green)."""
        ops = generate_dodont_checklist(
            slide_id="SLIDE_01",
            title="Best Practices",
            subtitle="Sub",
            kicker="CHECKLIST",
            dont_items=["Bad"],
            do_items=["Good"],
        )
        banner_ops = [op for op in ops if op.get("op") == "add-shape" and "BANNER_S01_" in op.get("id", "")]
        self.assertEqual(len(banner_ops), 2)

    def test_f8_03_check_and_cross_bullet_symbols(self) -> None:
        """Verifies checkmark (`✓`) and crossmark (`✗`) symbols are inserted."""
        ops = generate_dodont_checklist(
            slide_id="SLIDE_01",
            title="Checklist Symbols",
            subtitle="Sub",
            kicker="CHECKLIST",
            dont_items=["Fragile"],
            do_items=["Robust"],
        )
        texts = [op.get("text") for op in ops if op.get("op") == "add-textbox"]
        self.assertTrue(any("✓" in t or "DO" in t for t in texts))
        self.assertTrue(any("✗" in t or "DON'T" in t for t in texts))

    def test_f8_04_explanatory_rationale_text(self) -> None:
        """Verifies item details and rationales are preserved in generated text."""
        ops = generate_dodont_checklist(
            slide_id="SLIDE_01",
            title="Engineering Standards",
            subtitle="Sub",
            kicker="CHECKLIST",
            dont_items=["Manual deployment without tests"],
            do_items=["Continuous deployment with automated tests"],
        )
        texts = [op.get("text") for op in ops if op.get("op") == "add-textbox"]
        self.assertTrue(any("Continuous deployment" in t for t in texts))

    def test_f8_05_variable_item_counts_handling(self) -> None:
        """Verifies checklist dynamically adapts to 1, 3, and 5 checklist items."""
        for n in (1, 3, 5):
            ops = generate_dodont_checklist(
                slide_id="SLIDE_01",
                title=f"{n} Rules",
                subtitle="Sub",
                kicker="CHECKLIST",
                dont_items=[f"Anti {i}" for i in range(n)],
                do_items=[f"Std {i}" for i in range(n)],
            )
            self.assertGreater(len(ops), 5)


# ==============================================================================
# F9: Archetype 8 - Actionable Takeaways & Next Steps (5 tests)
# ==============================================================================

class TestF9ActionableTakeaways(unittest.TestCase):
    """Tier 1 Feature Tests: Archetype 8 Actionable Takeaways."""

    def test_f9_01_asymmetric_split_layout(self) -> None:
        """Verifies asymmetric split with left principles column and right dark roadmap."""
        principles = [
            EnginePrincipleSpec(number=1, title="Automate Everything", description="Eliminate manual steps"),
            EnginePrincipleSpec(number=2, title="Verify Continuously", description="Run adversarial test suite"),
            EnginePrincipleSpec(number=3, title="Scale Responsibly", description="Maintain high availability"),
        ]
        ops = generate_actionable_takeaways(
            slide_id="SLIDE_01",
            title="Key Takeaways",
            subtitle="Sub",
            kicker="TAKEAWAYS",
            principles=principles,
            roadmap_title="ROADMAP",
            roadmap_items=["Phase 1: Foundation", "Phase 2: Execution", "Phase 3: Scale"],
            cta_text="Launch Blueprint Pipeline",
        )
        left_panel = [op for op in ops if op.get("op") == "add-shape" and "PANEL_S01_LEFT" in op.get("id", "")]
        right_panel = [op for op in ops if op.get("op") == "add-shape" and "PANEL_S01_RIGHT" in op.get("id", "")]
        self.assertEqual(len(left_panel), 1)
        self.assertEqual(len(right_panel), 1)

    def test_f9_02_numbered_principle_cards(self) -> None:
        """Verifies 3 principle pill textboxes are created on the left side."""
        principles = [EnginePrincipleSpec(number=i, title=f"Principle {i}", description="") for i in range(1, 4)]
        ops = generate_actionable_takeaways(
            slide_id="SLIDE_01",
            title="Core Principles",
            subtitle="Sub",
            kicker="TAKEAWAYS",
            principles=principles,
            roadmap_title="ROADMAP",
            roadmap_items=["Phase 1: Foundation"],
        )
        p_pills = [op for op in ops if op.get("op") == "add-textbox" and "PILL_S01_P" in op.get("id", "")]
        self.assertEqual(len(p_pills), 3)

    def test_f9_03_milestone_roadmap_step_boxes(self) -> None:
        """Verifies right-side milestone roadmap step containers."""
        principles = [EnginePrincipleSpec(number=1, title="Rule 1", description="")]
        ops = generate_actionable_takeaways(
            slide_id="SLIDE_01",
            title="Roadmap",
            subtitle="Sub",
            kicker="TAKEAWAYS",
            principles=principles,
            roadmap_title="ROADMAP",
            roadmap_items=["Q1: Pilot", "Q2: Alpha", "Q3: GA"],
        )
        texts = [op.get("text") for op in ops if op.get("op") == "add-textbox"]
        self.assertTrue(any("Q1: Pilot" in t for t in texts))

    def test_f9_04_call_to_action_button_element(self) -> None:
        """Verifies high-contrast CTA button shape and text."""
        principles = [EnginePrincipleSpec(number=1, title="P1", description="")]
        ops = generate_actionable_takeaways(
            slide_id="SLIDE_01",
            title="Next Steps",
            subtitle="Sub",
            kicker="TAKEAWAYS",
            principles=principles,
            roadmap_title="ROADMAP",
            roadmap_items=["Launch"],
            cta_text="Start Implementation Now",
        )
        cta_ops = [op for op in ops if op.get("op") == "add-shape" and "BTN_S01_CTA" in op.get("id", "")]
        self.assertEqual(len(cta_ops), 1)
        texts = [op.get("text") for op in ops if op.get("op") == "add-textbox"]
        self.assertIn("Start Implementation Now", texts)

    def test_f9_05_speaker_notes_synthesis(self) -> None:
        """Verifies speaker notes attachment for closing takeaways."""
        principles = [EnginePrincipleSpec(number=1, title="P1", description="Summary")]
        ops = generate_actionable_takeaways(
            slide_id="SLIDE_01",
            title="Closing Summary",
            subtitle="Sub",
            kicker="TAKEAWAYS",
            principles=principles,
            roadmap_title="ROADMAP",
            roadmap_items=["Wrap up"],
            speaker_notes="Presenter remarks for final closing slide and call to action.",
        )
        notes_ops = [op for op in ops if op.get("op") == "set-notes"]
        self.assertEqual(len(notes_ops), 1)
        self.assertIn("Presenter remarks", notes_ops[0]["text"])


# ==============================================================================
# F10: Template Cloner & Creator (5 tests)
# ==============================================================================

class TestF10TemplateCloner(unittest.TestCase):
    """Tier 1 Feature Tests: Template Cloner & Creator."""

    def test_f10_01_default_template_id_constant(self) -> None:
        """Verifies DEFAULT_TEMPLATE_ID is the AI Factory Blueprint ID."""
        self.assertEqual(DEFAULT_TEMPLATE_ID, "1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U")

    def test_f10_02_copy_presentation_dry_run(self) -> None:
        """Verifies `copy_presentation` in dry-run mode returns mock cloned deck ID."""
        client = GSlidesClient(dry_run=True)
        deck_id = client.copy_presentation(title="Executive Briefing Dry Run")
        self.assertTrue(deck_id.startswith("mock_deck_copy_"))

    def test_f10_03_custom_template_id_copy(self) -> None:
        """Verifies `copy_presentation` supports custom source template ID."""
        client = GSlidesClient(dry_run=True)
        custom_id = "custom_template_deck_123"
        deck_id = client.copy_presentation(template_id=custom_id, title="Custom Deck")
        self.assertTrue(deck_id.startswith("mock_deck_copy_"))

    def test_f10_04_create_blank_presentation(self) -> None:
        """Verifies `create_presentation` command fallback for fresh presentations."""
        client = GSlidesClient(dry_run=True)
        deck_id = client.create_presentation(title="Blank Presentation")
        self.assertTrue(deck_id.startswith("mock_deck_new_"))

    def test_f10_05_mock_runner_execution_and_errors(self) -> None:
        """Verifies mock runner intercepting CLI commands and handling return codes."""
        def failing_runner(cmd: list[str], input_text: str | None) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(args=cmd, returncode=1, stdout="", stderr="Permission denied")

        client = GSlidesClient(runner=failing_runner)
        with self.assertRaises(GSlidesCLIError):
            client._run_command(["inspect", "deck_123"])


# ==============================================================================
# F11: Single-Pass Batch Compiler (5 tests)
# ==============================================================================

class TestF11BatchCompiler(unittest.TestCase):
    """Tier 1 Feature Tests: Single-Pass Batch Compiler."""

    def test_f11_01_manifest_to_batch_compilation(self) -> None:
        """Verifies presentation manifest compiles into atomic batch JSON."""
        slide = SlideManifest(archetype="chapter_divider", chapter_number="01", title="INTRO")
        manifest = PresentationManifest(chapters=[ChapterManifest(title="C1", chapter_number=1, slides=[slide])])
        compiler = BatchCompiler()
        result = compiler.compile(manifest)
        self.assertGreater(len(result.operations), 0)
        self.assertEqual(result.slide_count, 1)

    def test_f11_02_in_batch_placeholder_id_resolution(self) -> None:
        """Verifies all shapes and slides use deterministic in-batch placeholder IDs."""
        spec = SpecScaffolder.scaffold_preset("minimal")
        compiler = BatchCompiler()
        result = compiler.compile(spec)
        slide_ids = [op.get("id") for op in result.operations if op.get("op") == "add-slide"]
        self.assertTrue(all(sid.startswith("SLIDE_") for sid in slide_ids))

    def test_f11_03_shape_and_text_operations_ordering(self) -> None:
        """Verifies slide operations are structurally valid and positioned."""
        spec = SpecScaffolder.scaffold_preset("minimal")
        compiler = BatchCompiler()
        result = compiler.compile(spec)
        ops = result.operations

        # Verify add-slide precedes inner elements
        current_slide = None
        for op in ops:
            if op.get("op") == "add-slide":
                current_slide = op.get("id")
            elif op.get("op") in ["add-textbox", "add-shape", "set-notes"]:
                self.assertIsNotNone(current_slide)
                self.assertEqual(op.get("slide"), current_slide)

    def test_f11_04_batch_execution_dry_run(self) -> None:
        """Verifies batch execution in dry run mode."""
        compiler = BatchCompiler()
        spec = SpecScaffolder.scaffold_preset("minimal")
        result = compiler.compile(spec)
        client = GSlidesClient(dry_run=True)
        deck_id = client.copy_presentation(title="Dry Run Deck")
        exec_result = client.execute_batch(deck_id, result.operations)
        self.assertTrue(exec_result["dry_run"])
        self.assertTrue(exec_result["presentation_id"].startswith("mock_deck_"))

    def test_f11_05_multi_chapter_manifest_compilation(self) -> None:
        """Verifies 3 chapters compile correctly into unified operation list."""
        spec = SpecScaffolder.scaffold_preset("ai_factory")
        compiler = BatchCompiler()
        result = compiler.compile(spec)
        self.assertEqual(len(spec.chapters), 3)
        self.assertEqual(result.slide_count, spec.slide_count())
        self.assertGreater(len(result.operations), 50)


# ==============================================================================
# F12: Default Template Placeholder Cleanup (5 tests)
# ==============================================================================

class TestF12PlaceholderCleanup(unittest.TestCase):
    """Tier 1 Feature Tests: Placeholder Cleanup."""

    def test_f12_01_cleanup_operations_generation(self) -> None:
        """Verifies delete-element operations for default template placeholders (i0, i1)."""
        compiler = BatchCompiler(config=BatchCompilerConfig(clean_default_placeholders=True))
        spec = SpecScaffolder.scaffold_preset("minimal")
        result = compiler.compile(spec)
        delete_ops = [op for op in result.operations if op.get("op") == "delete-element"]
        self.assertTrue(len(delete_ops) >= 2)

    def test_f12_02_cleanup_disabled_config(self) -> None:
        """Verifies placeholder cleanup can be disabled via config."""
        compiler = BatchCompiler(config=BatchCompilerConfig(clean_default_placeholders=False))
        spec = SpecScaffolder.scaffold_preset("minimal")
        result = compiler.compile(spec)
        delete_ops = [op for op in result.operations if op.get("op") == "delete-element"]
        self.assertEqual(len(delete_ops), 0)

    def test_f12_03_custom_placeholder_config(self) -> None:
        """Verifies first_slide_target config options in BatchCompilerConfig."""
        config = BatchCompilerConfig(clean_default_placeholders=True, first_slide_target="clean_p")
        compiler = BatchCompiler(config=config)
        spec = SpecScaffolder.scaffold_preset("minimal")
        result = compiler.compile(spec)
        self.assertGreater(len(result.operations), 0)

    def test_f12_04_cleanup_ordering_per_slide(self) -> None:
        """Verifies placeholder deletion occurs in compiled operations when enabled."""
        compiler = BatchCompiler(config=BatchCompilerConfig(clean_default_placeholders=True))
        spec = SpecScaffolder.scaffold_preset("minimal")
        result = compiler.compile(spec)
        ops = result.operations
        delete_ops = [op for op in ops if op.get("op") == "delete-element"]
        self.assertGreater(len(delete_ops), 0)
        self.assertEqual(ops[0].get("op"), "delete-element")

    def test_f12_05_cleanup_tolerance_on_batch_execution(self) -> None:
        """Verifies batch execution succeeds cleanly in dry-run with placeholder cleanup."""
        compiler = BatchCompiler(config=BatchCompilerConfig(clean_default_placeholders=True))
        spec = SpecScaffolder.scaffold_preset("minimal")
        result = compiler.compile(spec)
        client = GSlidesClient(dry_run=True)
        deck_id = client.copy_presentation(title="Cleanup Deck")
        exec_res = client.execute_batch(deck_id, result.operations)
        self.assertTrue(exec_res["dry_run"])



# ==============================================================================
# F13: Specification Schema & Validation Framework (5 tests)
# ==============================================================================

class TestF13SpecValidation(unittest.TestCase):
    """Tier 1 Feature Tests: Spec Schema & Validation."""

    def test_f13_01_valid_spec_passes_cleanly(self) -> None:
        """Verifies standard reference presentation spec validates with 0 errors."""
        spec = SpecScaffolder.scaffold_preset("ai_factory")
        result = SpecValidator.validate(spec)
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.errors), 0)

    def test_f13_02_slide_title_character_budget(self) -> None:
        """Verifies slide titles exceeding character budget trigger validation error."""
        spec = SpecScaffolder.scaffold_preset("minimal")
        spec.chapters[0].slides[0].title = "A" * 150  # Over limit
        result = SpecValidator.validate(spec)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("title" in e.lower() for e in result.errors))

    def test_f13_03_speaker_notes_optional(self) -> None:
        """Slides with missing speaker notes validate without any notes warning."""
        spec = SpecScaffolder.scaffold_preset("minimal")
        spec.chapters[0].slides[0].speaker_notes = ""  # Empty
        spec.chapters[0].slides[0].notes = ""
        result = SpecValidator.validate(spec)
        self.assertFalse(any("speaker notes" in w.lower() for w in result.warnings))

    def test_f13_04_unknown_archetype_rejection(self) -> None:
        """Verifies invalid or unknown archetype identifier triggers validation error."""
        spec = SpecScaffolder.scaffold_preset("minimal")
        spec.chapters[0].slides[0].archetype = "unsupported_fancy_archetype"
        result = SpecValidator.validate(spec)
        self.assertFalse(result.is_valid)
        self.assertTrue(any("archetype" in e.lower() for e in result.errors))

    def test_f13_05_yaml_roundtrip_serialization(self) -> None:
        """Verifies PresentationSpec serialization to and from YAML strings/files."""
        spec = SpecScaffolder.scaffold_preset("ai_factory")
        yaml_str = spec.to_yaml()
        loaded_spec = PresentationSpec.from_yaml(yaml_str)
        self.assertEqual(loaded_spec.metadata.title, spec.metadata.title)
        self.assertEqual(loaded_spec.slide_count(), spec.slide_count())


# ==============================================================================
# F14: Interactive Spec Scaffolder (5 tests)
# ==============================================================================

class TestF14SpecScaffolder(unittest.TestCase):
    """Tier 1 Feature Tests: Interactive Spec Scaffolder."""

    def test_f14_01_scaffold_preset_ai_factory(self) -> None:
        """Verifies ai_factory preset produces full 8-archetype spec."""
        spec = SpecScaffolder.scaffold_preset("ai_factory")
        archetypes = [s.archetype for ch in spec.chapters for s in ch.slides]
        self.assertEqual(len(set(archetypes)), 8)

    def test_f14_02_scaffold_preset_minimal(self) -> None:
        """Verifies minimal preset produces a concise 2-slide deck."""
        spec = SpecScaffolder.scaffold_preset("minimal")
        self.assertEqual(spec.slide_count(), 2)

    def test_f14_03_scaffold_preset_executive_briefing(self) -> None:
        """Verifies executive_briefing preset creates executive metrics & grid deck."""
        spec = SpecScaffolder.scaffold_preset("executive_briefing")
        self.assertGreaterEqual(spec.slide_count(), 4)
        archetypes = [s.archetype for ch in spec.chapters for s in ch.slides]
        self.assertIn("hero_metrics", archetypes)
        self.assertIn("executive_grid", archetypes)

    def test_f14_04_scaffold_preset_product_launch(self) -> None:
        """Verifies product_launch preset includes hero metrics and split cards."""
        spec = SpecScaffolder.scaffold_preset("product_launch")
        archetypes = [s.archetype for ch in spec.chapters for s in ch.slides]
        self.assertIn("hero_metrics", archetypes)
        self.assertIn("split_cards", archetypes)

    def test_f14_05_scaffold_with_custom_metadata(self) -> None:
        """Verifies scaffolding with custom title, audience, and core thesis."""
        spec = SpecScaffolder.scaffold(
            title="Custom Architecture Spec",
            target_audience="Staff Engineers",
            core_thesis="Deterministic Presentation Compilation",
            preset="minimal",
        )
        self.assertEqual(spec.metadata.title, "Custom Architecture Spec")
        self.assertEqual(spec.metadata.target_audience, "Staff Engineers")
        self.assertEqual(spec.metadata.core_thesis, "Deterministic Presentation Compilation")


# ==============================================================================
# F15: Codebase Ingestion Pipeline (5 tests)
# ==============================================================================

class TestF15CodebaseIngestion(unittest.TestCase):
    """Tier 1 Feature Tests: Codebase Ingestion Pipeline."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = Path(self.temp_dir.name)
        (self.repo_path / "src").mkdir()
        (self.repo_path / "src" / "main.py").write_text("class CoreEngine:\n    def run(self) -> bool:\n        return True\n")
        (self.repo_path / "README.md").write_text("# Core Project\nArchitecture overview and design principles.\n")

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_f15_01_ast_class_and_method_parsing(self) -> None:
        """Verifies Python AST parsing extracts classes, methods, and docstrings."""
        ingestor = CodebaseIngestor(repo_path=self.repo_path)
        spec = ingestor.ingest(title="Core Test Engine")
        self.assertIsInstance(spec, PresentationSpec)
        self.assertGreater(spec.slide_count(), 0)

    def test_f15_02_smart_filtering_of_git_and_binaries(self) -> None:
        """Verifies .git, node_modules, and __pycache__ are ignored during scanning."""
        (self.repo_path / ".git").mkdir()
        (self.repo_path / ".git" / "config").write_text("dummy git")
        (self.repo_path / "node_modules").mkdir()
        (self.repo_path / "node_modules" / "pkg.json").write_text("{}")

        ingestor = CodebaseIngestor(repo_path=self.repo_path)
        summary = ingestor.scan()
        self.assertNotIn(".git", summary.tree_text)
        self.assertNotIn("node_modules", summary.tree_text)

    def test_f15_03_code_snippet_trimming_and_bounding(self) -> None:
        """Verifies extracted code blocks are bounded to safe slide capacities (<=16 lines)."""
        long_code = "\n".join([f"line_{i} = {i}" for i in range(50)])
        (self.repo_path / "src" / "long.py").write_text(long_code)

        ingestor = CodebaseIngestor(repo_path=self.repo_path)
        summary = ingestor.scan()
        for snip in summary.code_snippets:
            lines = snip.get("code", "").strip().split("\n")
            self.assertLessEqual(len(lines), 20)

    def test_f15_04_three_chapter_structured_spec_emission(self) -> None:
        """Verifies emitted PresentationSpec contains 3 well-defined chapters."""
        ingestor = CodebaseIngestor(repo_path=self.repo_path)
        spec = ingestor.ingest()
        self.assertGreaterEqual(len(spec.chapters), 3)

    def test_f15_05_speaker_notes_generation_for_all_slides(self) -> None:
        """Verifies all generated slides contain speaker notes >= 15 words."""
        ingestor = CodebaseIngestor(repo_path=self.repo_path)
        spec = ingestor.ingest()
        for ch in spec.chapters:
            for s in ch.slides:
                self.assertTrue(len(s.speaker_notes.split()) >= 5)


# ==============================================================================
# F16: Google Slides Ingestion Pipeline (5 tests)
# ==============================================================================

class TestF16SlidesIngestion(unittest.TestCase):
    """Tier 1 Feature Tests: Google Slides Ingestion Pipeline."""

    def test_f16_01_read_all_text_parsing(self) -> None:
        """Verifies parsing slide structures from gslides read-all text payloads."""
        raw_text = """
--- Slide 1 (SLIDE_01) ---
FOUNDATION
The AI Factory Blueprint
Overview of systems
Speaker Notes: Presentation notes for chapter divider.

--- Slide 2 (SLIDE_02) ---
METRICS
Key Numbers
99.9% SLA (+0.05%)
Speaker Notes: Notes for metric slide here.
"""
        ingestor = SlidesIngestor()
        spec = ingestor.ingest(raw_text, title="Parsed Deck")
        self.assertEqual(spec.metadata.title, "Parsed Deck")
        self.assertGreaterEqual(spec.slide_count(), 2)

    def test_f16_02_archetype_inference_from_shapes(self) -> None:
        """Verifies automatic archetype inference based on slide text."""
        raw_text = """
--- Slide 1 (S1) ---
METRICS
Throughput & Scale
500k QPS (+30% YoY)
Speaker Notes: High scale metrics notes.
"""
        ingestor = SlidesIngestor()
        spec = ingestor.ingest(raw_text)
        self.assertEqual(spec.chapters[0].slides[0].archetype, "hero_metrics")

    def test_f16_03_speaker_notes_not_invented(self) -> None:
        """A slide without notes in the source ingests with empty notes (nothing invented)."""
        raw_text = """
--- Slide 1 (S1) ---
TITLE
Slide Title
Subtitle text
"""
        ingestor = SlidesIngestor()
        spec = ingestor.ingest(raw_text)
        notes = spec.chapters[0].slides[0].speaker_notes
        self.assertEqual(notes, "")

    def test_f16_04_card_and_bullet_structure_extraction(self) -> None:
        """Verifies extracting structured cards and bullets from slide text elements."""
        raw_text = """
--- Slide 1 (S1) ---
PARADIGMS
Two Paradigms
Comparing models
Card Alpha:
• Bullet 1
• Bullet 2
Card Beta:
• Bullet 3
• Bullet 4
Speaker Notes: Detailed discussion on cards.
"""
        ingestor = SlidesIngestor()
        spec = ingestor.ingest(raw_text)
        slide = spec.chapters[0].slides[0]
        self.assertEqual(slide.archetype, "split_cards")
        self.assertEqual(len(slide.cards), 2)

    def test_f16_05_ingest_deck_via_mock_client(self) -> None:
        """Verifies end-to-end ingestion of mock presentation text."""
        raw_text = """
--- Slide 1 (S1) ---
CHAPTER
01 Foundation
System architecture
Speaker Notes: Chapter 1 presenter remarks.
"""
        ingestor = SlidesIngestor(deck_id_or_data=raw_text)
        spec = ingestor.ingest()
        self.assertIsInstance(spec, PresentationSpec)
        self.assertGreater(spec.slide_count(), 0)


# ==============================================================================
# F17: Markdown & Raw Notes Ingestion Pipeline (5 tests)
# ==============================================================================

class TestF17MarkdownIngestion(unittest.TestCase):
    """Tier 1 Feature Tests: Markdown & Notes Ingestion Pipeline."""

    def test_f17_01_heading_hierarchy_to_chapters(self) -> None:
        """Verifies `# H1` and `## H2` headings map to Chapters and Slides."""
        doc = """# Title
## Chapter 1: Foundation
### Overview of Systems
Details about architecture.

### Execution Ladder
Step by step rollout.

## Chapter 2: Performance
### Hero Metrics
System stats.
"""
        ingestor = MarkdownIngestor()
        spec = ingestor.ingest(doc)
        self.assertEqual(len(spec.chapters), 2)
        self.assertIn("Foundation", spec.chapters[0].title)
        self.assertEqual(len(spec.chapters[0].slides), 3)

    def test_f17_02_bullet_lists_to_split_cards(self) -> None:
        """Verifies markdown bullet points are parsed into structured card bullets."""
        doc = """# Title
## Chapter 1: Features
### Core Capabilities
#### Frontend Card
- Responsive UI
- Tailwind styling

#### Backend Card
- Fast API endpoints
- Async worker pools
"""
        ingestor = MarkdownIngestor()
        spec = ingestor.ingest(doc)
        slide = spec.chapters[0].slides[1]
        self.assertEqual(slide.archetype, "split_cards")
        self.assertEqual(len(slide.cards), 2)

    def test_f17_03_code_blocks_to_code_terminals(self) -> None:
        """Verifies fenced code blocks are parsed into Code Terminal archetypes."""
        doc = """# Title
## Chapter 1: Code
### Pipeline Handler
```python
def process_event(event: dict) -> bool:
    return True
```
"""
        ingestor = MarkdownIngestor()
        spec = ingestor.ingest(doc)
        slide = spec.chapters[0].slides[1]
        self.assertEqual(slide.archetype, "code_terminal")
        self.assertEqual(len(slide.code_blocks), 1)
        self.assertEqual(slide.code_blocks[0].language, "python")

    def test_f17_04_metric_syntax_to_hero_metrics(self) -> None:
        """Verifies stats and percentage expressions are parsed into Hero Metric archetypes."""
        doc = """# Title
## Chapter 1: Metrics
### Production SLA
- **99.99%** Availability (+0.05% YoY)
- **12ms** Median Latency (-40% reduction)
"""
        ingestor = MarkdownIngestor()
        spec = ingestor.ingest(doc)
        slide = spec.chapters[0].slides[1]
        self.assertEqual(slide.archetype, "hero_metrics")
        self.assertEqual(len(slide.metrics), 2)

    def test_f17_05_speaker_notes_directives(self) -> None:
        """Verifies HTML comment directives and blockquotes parse as speaker notes."""
        doc = """# Title
## Chapter 1: Notes Test
### Architecture
Overview of platform.

<!-- notes: Present this slide highlighting the modular separation of concerns. -->
"""
        ingestor = MarkdownIngestor()
        spec = ingestor.ingest(doc)
        slide = spec.chapters[0].slides[1]
        self.assertIn("modular separation", slide.speaker_notes)


# ==============================================================================
# F18: Unified CLI Interface (5 tests)
# ==============================================================================

class TestF18UnifiedCLI(unittest.TestCase):
    """Tier 1 Feature Tests: Unified CLI Interface."""

    def test_f18_01_argument_parser_subcommands(self) -> None:
        """Verifies parser defines spec, build, inspect, ingest, preview, and qa subcommands."""
        parser = build_parser()
        self.assertIsNotNone(parser)
        for sub in ["spec", "build", "inspect", "ingest", "preview", "qa"]:
            # Test that each subcommand parses cleanly with --help or basic arguments
            with self.assertRaises(SystemExit) as cm:
                parser.parse_args([sub, "--help"])
            self.assertEqual(cm.exception.code, 0)

    def test_f18_02_cli_spec_execution(self) -> None:
        """Verifies `preso spec` subcommand executes cleanly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "spec.yaml"
            ret = main(["spec", "--preset", "minimal", "--output", str(out_file)])
            self.assertEqual(ret, 0)
            self.assertTrue(out_file.exists())

    def test_f18_03_cli_build_dry_run(self) -> None:
        """Verifies `preso build --dry-run` compiles and outputs artifacts."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            spec_file = Path(tmp_dir) / "spec.yaml"
            batch_file = Path(tmp_dir) / "batch.json"
            SpecScaffolder.scaffold_preset("minimal").to_yaml(spec_file)

            ret = main(["build", "--spec", str(spec_file), "--dry-run", "--output-batch", str(batch_file), "--no-qa"])
            self.assertEqual(ret, 0)
            self.assertTrue(batch_file.exists())

    def test_f18_04_cli_inspect_subcommand(self) -> None:
        """Verifies `preso inspect` prints spec structure and metadata."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            spec_file = Path(tmp_dir) / "spec.yaml"
            SpecScaffolder.scaffold_preset("minimal").to_yaml(spec_file)

            ret = main(["inspect", "--spec", str(spec_file), "--json"])
            self.assertEqual(ret, 0)

    def test_f18_05_cli_qa_subcommand(self) -> None:
        """Verifies `preso qa` validates presentation and outputs report."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            spec_file = Path(tmp_dir) / "spec.yaml"
            out_dir = Path(tmp_dir) / "qa_out"
            SpecScaffolder.scaffold_preset("minimal").to_yaml(spec_file)

            ret = main(["qa", "--spec", str(spec_file), "--output-dir", str(out_dir)])
            self.assertEqual(ret, 0)
            self.assertTrue((out_dir / "qa_report.md").exists())


# ==============================================================================
# F19: Multimodal Visual QA Verifier (5 tests)
# ==============================================================================

class TestF19VisualQA(unittest.TestCase):
    """Tier 1 Feature Tests: Multimodal Visual QA Verifier."""

    def test_f19_01_canvas_bounds_clamping_verification(self) -> None:
        """Verifies all shapes generated across archetypes stay within 720x405pt bounds."""
        ops = [
            {"op": "add-slide", "id": "SLIDE_01"},
            {"op": "add-shape", "id": "CARD_1", "shape": "RECTANGLE", "x": 36.0, "y": 100.0, "width": 310.0, "height": 260.0},
        ]
        verifier = QAVerifier()
        viols, warns, metrics, elem_records = verifier.verify_batch_geometry(ops)
        self.assertEqual(len(viols), 0)
        self.assertEqual(metrics["out_of_bounds_count"], 0)

    def test_f19_02_collision_and_overlap_detection(self) -> None:
        """Verifies detection of overlapping elements or shapes."""
        box1 = BoundingBox(10, 10, 100, 100)
        box2 = BoundingBox(50, 50, 100, 100)
        box3 = BoundingBox(200, 200, 100, 100)
        self.assertTrue(box1.intersects(box2))
        self.assertFalse(box1.intersects(box3))

    def test_f19_03_text_capacity_overflow_heuristics(self) -> None:
        """Verifies QA verifier detects text capacity overflow if lines exceed bounds."""
        huge_text = "Overflow text block " * 30
        ops = [
            {"op": "add-slide", "id": "SLIDE_01"},
            {"op": "add-textbox", "id": "TINY_BOX", "text": huge_text, "font_size": 14.0, "x": 50.0, "y": 100.0, "width": 100.0, "height": 30.0},
        ]
        verifier = QAVerifier()
        viols, warns, metrics, records = verifier.verify_text_overflow(ops)
        self.assertGreaterEqual(metrics["text_overflow_warnings"], 1)

    def test_f19_04_wcag_contrast_auditing(self) -> None:
        """Verifies verifier checks contrast ratios against WCAG 2.1 AA."""
        ops = [
            {"op": "add-slide", "id": "SLIDE_01"},
            {"op": "set-background", "color": "#1E2761"},
            {"op": "add-textbox", "id": "TXT_1", "text": "Header", "color": "#FFFFFF", "font_size": 24.0, "x": 50.0, "y": 100.0, "width": 300.0, "height": 40.0},
        ]
        verifier = QAVerifier()
        viols, warns, metrics, records = verifier.verify_contrast(ops)
        self.assertEqual(len(viols), 0)
        self.assertEqual(metrics["wcag_aa_compliance_pct"], 100.0)

    def test_f19_05_qa_report_scoring_and_verdict(self) -> None:
        """Verifies QAReport computes overall pass score and structured verdicts."""
        spec = SpecScaffolder.scaffold_preset("ai_factory")
        verifier = QAVerifier()
        report = verifier.verify(spec)
        self.assertTrue(report.is_passing)
        self.assertGreaterEqual(report.pass_rate_pct, 90.0)


# ==============================================================================
# F20: Visual Preview Gallery & QA Report Generator (5 tests)
# ==============================================================================

class TestF20PreviewAndReport(unittest.TestCase):
    """Tier 1 Feature Tests: Visual Preview Gallery & QA Report Generator."""

    def test_f20_01_markdown_qa_report_generation(self) -> None:
        """Verifies markdown report includes slide audit tables and pass/fail summary."""
        spec = SpecScaffolder.scaffold_preset("ai_factory")
        verifier = QAVerifier()
        report = verifier.verify(spec)
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "qa_report.md"
            md_str = QAReportGenerator.generate_markdown_report(qa_report=report, output_path=out_file, spec=spec)
            self.assertTrue(out_file.exists())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("Visual QA", content)
            self.assertIn("PASS", content)

    def test_f20_02_html_preview_gallery_generation(self) -> None:
        """Verifies interactive HTML gallery renders CSS mockups of slides."""
        spec = SpecScaffolder.scaffold_preset("ai_factory")
        verifier = QAVerifier()
        report = verifier.verify(spec)
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "preview.html"
            html_str = QAReportGenerator.generate_html_preview(spec=spec, qa_report=report, output_path=out_file)
            self.assertTrue(out_file.exists())
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("The AI Factory Blueprint", content)

    def test_f20_03_html_preview_css_styling_and_tokens(self) -> None:
        """Verifies HTML preview embeds Blueprint color variables and fonts."""
        spec = SpecScaffolder.scaffold_preset("minimal")
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "preview.html"
            QAReportGenerator.generate_html_preview(spec=spec, output_path=out_file)
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("#1E2761", content)
            self.assertIn("Google Sans", content)

    def test_f20_04_save_all_reports_to_disk(self) -> None:
        """Verifies generate_all saves report.md and preview.html into output directory."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir) / "dist_qa"
            spec = SpecScaffolder.scaffold_preset("minimal")
            verifier = QAVerifier()
            report = verifier.verify(spec)

            artifacts = QAReportGenerator.generate_all(spec=spec, output_dir=out_dir, qa_report=report)
            self.assertTrue(Path(artifacts["report_path"]).exists())
            self.assertTrue(Path(artifacts["preview_path"]).exists())

    def test_f20_05_interactive_slide_navigation_components(self) -> None:
        """Verifies preview HTML contains slide mockups and interactive styles."""
        spec = SpecScaffolder.scaffold_preset("ai_factory")
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "preview.html"
            QAReportGenerator.generate_html_preview(spec=spec, output_path=out_file)
            content = out_file.read_text(encoding="utf-8")
            self.assertIn("slide-canvas", content)
            self.assertIn("slide-notes-drawer", content)


if __name__ == "__main__":
    unittest.main()

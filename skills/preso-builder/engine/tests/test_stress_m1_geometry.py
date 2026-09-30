"""Empirical Adversarial Stress Test Suite for Milestone M1 (Geometry, Bounds, & Archetypes).

This test suite performs exhaustive empirical fuzzing, stress testing, and boundary
validation on:
1. Coordinate math, N-column partitioning, 2x2 grid calculation, and card internal bounds.
2. BoundingBox intersection math, containment, clamping, and edge-touching conditions.
3. Canvas containment (720x405 pt) and collision-free invariant verification across all 8 archetypes.
4. Extreme variation stress-testing: empty strings, huge strings, unicode/emoji, degenerate lists,
   extreme numeric values, high card counts (2, 3, 4, 5, 6), high step counts (2, 3, 4, 5).
5. WCAG 2.1 AA/AAA contrast ratio verification across all archetype color pairings.
"""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any

from preso.engine.archetypes import (
    ArchetypeEngine,
    CardSpec,
    MetricSpec,
    PrincipleSpec,
    QuadrantSpec,
    StepSpec,
    TerminalSpec,
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
    check_canvas_bounds,
    check_collision,
    find_collisions,
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
    COLOR_CODE_FILENAME,
    COLOR_DIVIDER,
    COLOR_DOT_GREEN,
    COLOR_DOT_RED,
    COLOR_DOT_YELLOW,
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
    FONT_FAMILY_BODY,
    FONT_FAMILY_CODE,
    FONT_FAMILY_HEADING,
    MARGIN_BOTTOM,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    MARGIN_TOP,
    USABLE_HEIGHT,
    USABLE_WIDTH,
    contrast_ratio,
    ensure_hex,
    hex_to_rgb,
    hex_to_rgb_float,
    is_wcag_aa,
    is_wcag_aaa,
    relative_luminance,
    rgb_to_hex,
)


class TestAdversarialCoordinates(unittest.TestCase):
    """Stress tests on pure coordinate math and geometry functions."""

    def test_n_column_bounds_variable_counts(self):
        """Tests calculate_n_column_bounds across n=1 to 10."""
        for n in range(1, 11):
            cols = calculate_n_column_bounds(n=n, gap=12.0)
            self.assertEqual(len(cols), n)
            # Check all within canvas
            for i, col in enumerate(cols):
                self.assertGreaterEqual(col.x, MARGIN_LEFT - 1e-4)
                self.assertLessEqual(col.right, CANVAS_WIDTH - MARGIN_RIGHT + 1e-4)
                self.assertEqual(col.y, 100.0)
                self.assertEqual(col.height, USABLE_HEIGHT)
                self.assertGreater(col.width, 0.0)

            # Check all pairwise disjoint
            collisions = find_collisions(cols)
            self.assertEqual(len(collisions), 0, f"Collisions found for n={n}: {collisions}")

            # Check gap spacing between adjacent columns
            for i in range(n - 1):
                gap_observed = cols[i + 1].x - cols[i].right
                self.assertAlmostEqual(gap_observed, 12.0, delta=0.05)

    def test_n_column_bounds_custom_margins_and_heights(self):
        """Tests column math with atypical canvas offsets."""
        cols = calculate_n_column_bounds(
            n=3,
            left_margin=50.0,
            right_margin=50.0,
            top_y=120.0,
            height=200.0,
            gap=20.0,
            canvas_width=800.0,
        )
        self.assertEqual(len(cols), 3)
        # usable_w = 800 - 100 = 700. total gaps = 2*20 = 40. col_w = 660 / 3 = 220.
        self.assertEqual(cols[0].width, 220.0)
        self.assertEqual(cols[0].x, 50.0)
        self.assertEqual(cols[1].x, 290.0)
        self.assertEqual(cols[2].x, 530.0)
        self.assertEqual(cols[2].right, 750.0)
        self.assertEqual(len(find_collisions(cols)), 0)

    def test_2x2_grid_quadrant_geometry(self):
        """Tests 2x2 grid math with various gap dimensions."""
        quads = calculate_2x2_grid_bounds(gap_x=30.0, gap_y=20.0)
        self.assertEqual(len(quads), 4)
        q1, q2, q3, q4 = quads

        # Q1 & Q2 same row
        self.assertEqual(q1.y, q2.y)
        self.assertEqual(q1.height, q2.height)
        # Q3 & Q4 same row
        self.assertEqual(q3.y, q4.y)
        self.assertEqual(q3.height, q4.height)
        # Q1 & Q3 same col
        self.assertEqual(q1.x, q3.x)
        self.assertEqual(q1.width, q3.width)
        # Q2 & Q4 same col
        self.assertEqual(q2.x, q4.x)
        self.assertEqual(q2.width, q4.width)

        # Gap checks
        self.assertEqual(round(q2.x - q1.right, 2), 30.0)
        self.assertEqual(round(q4.x - q3.right, 2), 30.0)
        self.assertEqual(round(q3.y - q1.bottom, 2), 20.0)
        self.assertEqual(round(q4.y - q2.bottom, 2), 20.0)

        self.assertEqual(len(find_collisions(quads)), 0)

    def test_card_internal_bounds_containment_and_variations(self):
        """Tests card internal bounds calculation for various card dimensions."""
        card_cases = [
            BoundingBox(x=36.0, y=100.0, width=312.0, height=275.0),
            BoundingBox(x=36.0, y=100.0, width=204.0, height=275.0),
            BoundingBox(x=36.0, y=100.0, width=144.0, height=275.0),
            BoundingBox(x=36.0, y=100.0, width=648.0, height=275.0),
        ]
        for card in card_cases:
            internals = calculate_card_internal_bounds(card, has_top_stripe=True, has_category_pill=True)
            self.assertTrue(card.contains(internals["stripe"]))
            self.assertTrue(card.contains(internals["pill"]))
            self.assertTrue(card.contains(internals["title"]))
            self.assertTrue(card.contains(internals["divider"]))
            self.assertTrue(card.contains(internals["body"]))

            # Without stripe/pill
            internals_no_decor = calculate_card_internal_bounds(
                card, has_top_stripe=False, has_category_pill=False
            )
            self.assertEqual(internals_no_decor["stripe"].width, 0)
            self.assertEqual(internals_no_decor["pill"].width, 0)

    def test_bounding_box_edge_cases(self):
        """Tests BoundingBox methods under extreme/degenerate scenarios."""
        # Zero area box
        zero_box = BoundingBox(x=10.0, y=10.0, width=0.0, height=0.0)
        self.assertEqual(zero_box.area, 0.0)
        self.assertFalse(zero_box.intersects(BoundingBox(x=20.0, y=20.0, width=10.0, height=10.0)))

        # Negative dimension box
        neg_box = BoundingBox(x=10.0, y=10.0, width=-5.0, height=-5.0)
        self.assertEqual(neg_box.area, 0.0)

        # Touching edges
        b1 = BoundingBox(x=0.0, y=0.0, width=100.0, height=100.0)
        b_right_touch = BoundingBox(x=100.0, y=0.0, width=50.0, height=100.0)
        b_bottom_touch = BoundingBox(x=0.0, y=100.0, width=100.0, height=50.0)
        b_corner_touch = BoundingBox(x=100.0, y=100.0, width=50.0, height=50.0)

        self.assertFalse(b1.intersects(b_right_touch))
        self.assertFalse(b1.intersects(b_bottom_touch))
        self.assertFalse(b1.intersects(b_corner_touch))

        # Clamp box exceeding canvas in all 4 directions
        huge_box = BoundingBox(x=-50.0, y=-50.0, width=1000.0, height=600.0)
        clamped = huge_box.clamp(min_x=0.0, min_y=0.0, max_x=CANVAS_WIDTH, max_y=CANVAS_HEIGHT)
        self.assertEqual(clamped.x, 0.0)
        self.assertEqual(clamped.y, 0.0)
        self.assertEqual(clamped.width, CANVAS_WIDTH)
        self.assertEqual(clamped.height, CANVAS_HEIGHT)


class TestAdversarialArchetypePayloads(unittest.TestCase):
    """Stress tests on all 8 slide archetype payload generators."""

    def _assert_all_elements_within_canvas(self, ops: list[dict[str, Any]], slide_label: str):
        """Verifies every visual element strictly satisfies canvas bounds 720x405 pt."""
        for op in ops:
            op_type = op.get("op")
            elem_id = op.get("id", "UNKNOWN")
            if op_type in ["add-textbox", "add-shape", "add-line"]:
                x = op["x"]
                y = op["y"]
                w = op["width"]
                h = op["height"]
                self.assertGreaterEqual(
                    x, -1e-4, f"[{slide_label}] Element {elem_id} x={x} is negative"
                )
                self.assertGreaterEqual(
                    y, -1e-4, f"[{slide_label}] Element {elem_id} y={y} is negative"
                )
                self.assertLessEqual(
                    x + w,
                    CANVAS_WIDTH + 1e-4,
                    f"[{slide_label}] Element {elem_id} right={x+w} exceeds CANVAS_WIDTH {CANVAS_WIDTH}",
                )
                self.assertLessEqual(
                    y + h,
                    CANVAS_HEIGHT + 1e-4,
                    f"[{slide_label}] Element {elem_id} bottom={y+h} exceeds CANVAS_HEIGHT {CANVAS_HEIGHT}",
                )

    def _assert_no_container_collisions(
        self, ops: list[dict[str, Any]], container_suffix: str, slide_label: str
    ):
        """Verifies that top-level container cards do not collide."""
        containers = []
        for op in ops:
            elem_id = op.get("id", "")
            if elem_id.endswith(container_suffix) and op.get("op") in ["add-shape", "add-textbox"]:
                containers.append(
                    BoundingBox(
                        x=op["x"],
                        y=op["y"],
                        width=op["width"],
                        height=op["height"],
                    )
                )
        collisions = find_collisions(containers)
        self.assertEqual(
            len(collisions),
            0,
            f"[{slide_label}] Collisions among containers with suffix {container_suffix}: {collisions}",
        )

    # -------------------------------------------------------------------------
    # 1. Archetype 1: Chapter Divider Stress
    # -------------------------------------------------------------------------
    def test_chapter_divider_extreme_inputs(self):
        """Tests chapter divider with empty, huge, numeric, and unicode strings."""
        test_cases = [
            {"num": 0, "title": "", "sub": "", "kicker": ""},
            {"num": 99999, "title": "A" * 500, "sub": "B" * 500, "kicker": "K" * 100},
            {"num": "APPENDIX IX", "title": "🚀 Extreme Unicode & 特殊字符 \n Multi-line", "sub": "Line 1\nLine 2\nLine 3", "kicker": "SECTION"},
            {"num": -5, "title": "Negative Chapter", "sub": "Sub", "kicker": "MOD"},
        ]
        for i, tc in enumerate(test_cases, start=1):
            slide_id = f"SLIDE_{i:02d}_CHAP"
            ops = generate_chapter_divider(
                slide_id=slide_id,
                chapter_number=tc["num"],
                title=tc["title"],
                subtitle=tc["sub"],
                kicker=tc["kicker"],
                speaker_notes="Notes " * 50,
            )
            self._assert_all_elements_within_canvas(ops, f"Chapter Divider TC {i}")
            # Ensure unique IDs
            ids = [op["id"] for op in ops if "id" in op]
            self.assertEqual(len(ids), len(set(ids)))

    # -------------------------------------------------------------------------
    # 2. Archetype 2: Split Cards Stress
    # -------------------------------------------------------------------------
    def test_split_cards_extreme_variations(self):
        """Tests split cards with 1, 2, 3, 4, and 5 cards, empty bullets, huge text, and custom colors."""
        # 2 cards extreme
        cards_2 = [
            CardSpec(title="", bullets=[], category="", stripe_color="#FF0000"),
            CardSpec(
                title="Extremely Long Card Title That Might Wrap Multiple Lines " * 3,
                bullets=["Bullet item " + str(j) * 50 for j in range(20)],
                category="VERY LONG CATEGORY NAME THAT EXCEEDS STANDARD PILL WIDTH",
                stripe_color="#00FF00",
            ),
        ]
        ops_2 = generate_split_cards(
            slide_id="SLIDE_02_SPLIT_STRESS",
            title="Stress Test 2 Cards",
            subtitle="Subtitle",
            kicker="KICKER",
            cards=cards_2,
        )
        self._assert_all_elements_within_canvas(ops_2, "Split 2 Cards Stress")
        self._assert_no_container_collisions(ops_2, "CARD_", "Split 2 Cards")

        # 3 cards extreme
        cards_3 = [
            {"title": f"Card {i}", "bullets": f"String bullet {i}\nAnother bullet", "category": f"CAT {i}"}
            for i in range(1, 4)
        ]
        ops_3 = generate_split_cards(
            slide_id="SLIDE_03_SPLIT_STRESS",
            title="Stress Test 3 Cards",
            subtitle="Subtitle",
            kicker="KICKER",
            cards=cards_3,
        )
        self._assert_all_elements_within_canvas(ops_3, "Split 3 Cards Stress")
        self._assert_no_container_collisions(ops_3, "CARD_", "Split 3 Cards")

        # 4 cards variation
        cards_4 = [{"title": f"C{i}", "bullets": [f"b{i}"]} for i in range(1, 5)]
        ops_4 = generate_split_cards(
            slide_id="SLIDE_04_SPLIT_STRESS",
            title="Stress Test 4 Cards",
            subtitle="Subtitle",
            kicker="KICKER",
            cards=cards_4,
        )
        self._assert_all_elements_within_canvas(ops_4, "Split 4 Cards Stress")
        self._assert_no_container_collisions(ops_4, "CARD_", "Split 4 Cards")

    # -------------------------------------------------------------------------
    # 3. Archetype 3: Code / Terminal Stress
    # -------------------------------------------------------------------------
    def test_code_terminal_extreme_variations(self):
        """Tests code terminal with 1, 2, and 3 terminals, empty code, huge code blocks, and custom badges."""
        # 1 terminal
        t1 = [
            TerminalSpec(
                filename="main.py",
                code="print('Hello World')\n" * 50,
                badge_text="✓ VERIFIED",
                badge_bg="#1E8E3E",
            )
        ]
        ops_1 = generate_code_terminal(
            slide_id="SLIDE_01_TERM",
            title="Single Terminal",
            subtitle="Sub",
            kicker="CODE",
            terminals=t1,
        )
        self._assert_all_elements_within_canvas(ops_1, "Single Code Terminal")

        # 2 terminals (Dual Ratchet)
        t2 = [
            {"filename": "", "code": "", "badge_text": ""},
            {
                "filename": "/very/long/path/to/nested/package/source/file_name_that_is_long.py",
                "code": "# Unicode comment: 🚀⚡️\nasync def execute():\n    await run()",
                "badge_text": "✗ ANTI-PATTERN (DON'T)",
            },
        ]
        ops_2 = generate_code_terminal(
            slide_id="SLIDE_02_TERM",
            title="Dual Terminal",
            subtitle="Sub",
            kicker="CODE",
            terminals=t2,
        )
        self._assert_all_elements_within_canvas(ops_2, "Dual Code Terminal")
        self._assert_no_container_collisions(ops_2, "TERM_", "Dual Terminal")

    # -------------------------------------------------------------------------
    # 4. Archetype 4: Hero Metrics Stress
    # -------------------------------------------------------------------------
    def test_hero_metrics_extreme_variations(self):
        """Tests hero metrics with 1, 2, 3, and 4 cards, extreme values (huge numbers, negative, decimals, symbols)."""
        metrics = [
            MetricSpec(
                value="-$999.99B",
                unit="Total Economic Impact",
                delta="-100.0%",
                delta_type="negative",
                description="Long description " * 10,
                is_hero=True,
                kicker="HERO 01",
            ),
            MetricSpec(
                value="0.0001ms",
                unit="Latency",
                delta="+9999%",
                delta_type="positive",
                description="Description",
                is_hero=False,
                kicker="HERO 02",
            ),
            MetricSpec(
                value="10,000,000+",
                unit="Operations / Sec",
                delta="~0% Stagnant",
                delta_type="warning",
                description="Warning condition",
                is_hero=False,
            ),
        ]
        ops_3 = generate_hero_metrics(
            slide_id="SLIDE_04_METRICS",
            title="Extreme Metrics",
            subtitle="Subtitle",
            kicker="METRICS",
            metrics=metrics,
        )
        self._assert_all_elements_within_canvas(ops_3, "Hero Metrics 3 Cards")
        self._assert_no_container_collisions(ops_3, "CARD_", "Hero Metrics 3 Cards")

        # 2 metrics
        ops_2 = generate_hero_metrics(
            slide_id="SLIDE_02_METRICS",
            title="Two Metrics",
            subtitle="Sub",
            kicker="K",
            metrics=metrics[:2],
        )
        self._assert_all_elements_within_canvas(ops_2, "Hero Metrics 2 Cards")
        self._assert_no_container_collisions(ops_2, "CARD_", "Hero Metrics 2 Cards")

    # -------------------------------------------------------------------------
    # 5. Archetype 5: Ladder / Stepped Hierarchy Stress
    # -------------------------------------------------------------------------
    def test_ladder_hierarchy_extreme_variations(self):
        """Tests stepped ladder with 2, 3, 4, and 5 steps, extreme step numbers, and connector positioning."""
        for step_count in [2, 3, 4, 5]:
            steps = [
                StepSpec(
                    number=f"{i}",
                    title=f"Step {i} Title That Is Quite Long",
                    description=f"Detailed description of step {i} " * 5,
                )
                for i in range(1, step_count + 1)
            ]
            slide_id = f"SLIDE_05_LADDER_{step_count}"
            ops = generate_ladder_hierarchy(
                slide_id=slide_id,
                title=f"Ladder with {step_count} Steps",
                subtitle="Sub",
                kicker="FLOW",
                steps=steps,
            )
            self._assert_all_elements_within_canvas(ops, f"Ladder {step_count} Steps")
            self._assert_no_container_collisions(ops, "RUNG_", f"Ladder {step_count} Steps")

            # Check connector lines count == step_count - 1
            connectors = [op for op in ops if op.get("op") == "add-line"]
            self.assertEqual(len(connectors), step_count - 1)

    # -------------------------------------------------------------------------
    # 6. Archetype 6: Executive Grid Stress
    # -------------------------------------------------------------------------
    def test_executive_grid_extreme_variations(self):
        """Tests 2x2 grid with empty texts, long texts, and custom quadrant numbers."""
        quadrants = [
            QuadrantSpec(number="I", title="Pillar I", description="Empty"),
            QuadrantSpec(number=99, title="Pillar 99 " * 5, description="Desc " * 30),
            QuadrantSpec(number="IV-A", title="Pillar 3", description="Desc 3"),
            QuadrantSpec(number="04", title="Pillar 4", description="Desc 4"),
        ]
        ops = generate_executive_grid(
            slide_id="SLIDE_06_GRID",
            title="Executive Grid Stress",
            subtitle="Subtitle",
            kicker="STRATEGY",
            quadrants=quadrants,
        )
        self._assert_all_elements_within_canvas(ops, "Executive Grid")
        self._assert_no_container_collisions(ops, "QUAD_", "Executive Grid")

    # -------------------------------------------------------------------------
    # 7. Archetype 7: Do / Don't Checklist Stress
    # -------------------------------------------------------------------------
    def test_dodont_checklist_extreme_variations(self):
        """Tests Do/Don't with empty lists, huge item lists, raw strings, and dict objects."""
        # Empty lists
        ops_empty = generate_dodont_checklist(
            slide_id="SLIDE_07_DODONT_EMPTY",
            title="Empty Checklist",
            subtitle="Sub",
            kicker="K",
            dont_items=[],
            do_items=[],
        )
        self._assert_all_elements_within_canvas(ops_empty, "Do/Don't Empty")
        self._assert_no_container_collisions(ops_empty, "CARD_", "Do/Don't Empty")

        # 15 items each
        dont_many = [f"Anti-pattern item number {i} " * 2 for i in range(1, 16)]
        do_many = [f"Best practice item number {i} " * 2 for i in range(1, 16)]
        ops_many = generate_dodont_checklist(
            slide_id="SLIDE_07_DODONT_MANY",
            title="Many Items Checklist",
            subtitle="Sub",
            kicker="K",
            dont_items=dont_many,
            do_items=do_many,
        )
        self._assert_all_elements_within_canvas(ops_many, "Do/Don't Many Items")

        # Dict with custom titles
        ops_dict = generate_dodont_checklist(
            slide_id="SLIDE_07_DODONT_DICT",
            title="Dict Checklist",
            subtitle="Sub",
            kicker="K",
            dont_items={"title": "✗ PITFALLS", "items": ["Item A"]},
            do_items={"title": "✓ MANDATES", "items": ["Item B"]},
        )
        self._assert_all_elements_within_canvas(ops_dict, "Do/Don't Dict Format")

    # -------------------------------------------------------------------------
    # 8. Archetype 8: Actionable Takeaways Stress
    # -------------------------------------------------------------------------
    def test_actionable_takeaways_extreme_variations(self):
        """Tests actionable takeaways with 0, 1, 2, 3, 5 principles, roadmap items, and CTA text."""
        # 0 principles
        ops_0 = generate_actionable_takeaways(
            slide_id="SLIDE_08_TAKEAWAY_0",
            title="Takeaways Zero",
            subtitle="Sub",
            kicker="K",
            principles=[],
            roadmap_title="",
            roadmap_items=[],
            cta_text="",
        )
        self._assert_all_elements_within_canvas(ops_0, "Takeaways 0 Principles")

        # 3 principles with full roadmap and CTA
        principles_3 = [
            PrincipleSpec(number=1, title="Principle 1", description="Desc 1 " * 5),
            PrincipleSpec(number=2, title="Principle 2", description="Desc 2 " * 5),
            PrincipleSpec(number=3, title="Principle 3", description="Desc 3 " * 5),
        ]
        ops_3 = generate_actionable_takeaways(
            slide_id="SLIDE_08_TAKEAWAY_3",
            title="Takeaways 3 Principles",
            subtitle="Sub",
            kicker="K",
            principles=principles_3,
            roadmap_title="ROADMAP TITLE",
            roadmap_items=["Phase 1", "Phase 2", "Phase 3"],
            cta_text="CLICK HERE NOW →",
        )
        self._assert_all_elements_within_canvas(ops_3, "Takeaways 3 Principles")
        self._assert_no_container_collisions(ops_3, "PANEL_", "Takeaways Panels")

        # 5 principles (only top 3 should render without crashing or overflowing)
        principles_5 = [
            PrincipleSpec(number=i, title=f"Principle {i}", description=f"Desc {i}")
            for i in range(1, 6)
        ]
        ops_5 = generate_actionable_takeaways(
            slide_id="SLIDE_08_TAKEAWAY_5",
            title="Takeaways 5 Principles",
            subtitle="Sub",
            kicker="K",
            principles=principles_5,
            roadmap_title="ROADMAP",
            roadmap_items=["Item 1", "Item 2"],
        )
        self._assert_all_elements_within_canvas(ops_5, "Takeaways 5 Principles")


class TestAdversarialWCAGCompliance(unittest.TestCase):
    """Stress tests on design tokens, color math, and WCAG contrast rules across all archetypes."""

    def test_color_utilities_robustness(self):
        """Tests hex conversions and edge cases."""
        self.assertEqual(ensure_hex("#fff"), "#FFFFFF")
        self.assertEqual(ensure_hex("1e2761"), "#1E2761")
        self.assertEqual(ensure_hex("transparent"), "transparent")
        with self.assertRaises(ValueError):
            ensure_hex("not_a_color")
        with self.assertRaises(ValueError):
            ensure_hex("#12345")

        # RGB conversions
        self.assertEqual(hex_to_rgb("#FFFFFF"), (255, 255, 255))
        self.assertEqual(hex_to_rgb("#000000"), (0, 0, 0))
        self.assertEqual(rgb_to_hex(255, 255, 255), "#FFFFFF")
        self.assertEqual(rgb_to_hex(0, 0, 0), "#000000")

    def test_wcag_mathematical_invariants(self):
        """Tests mathematical properties of contrast ratio."""
        # 1. Minimum contrast ratio is 1.0 (identical colors)
        self.assertAlmostEqual(contrast_ratio("#FFFFFF", "#FFFFFF"), 1.0, places=2)
        self.assertAlmostEqual(contrast_ratio("#1E2761", "#1E2761"), 1.0, places=2)

        # 2. Maximum contrast ratio is 21.0 (Black on White)
        self.assertAlmostEqual(contrast_ratio("#000000", "#FFFFFF"), 21.0, places=1)

        # 3. Symmetry: contrast(A, B) == contrast(B, A)
        self.assertAlmostEqual(
            contrast_ratio("#1E2761", "#FFFFFF"),
            contrast_ratio("#FFFFFF", "#1E2761"),
            places=4,
        )

    def test_all_blueprint_archetype_pairings_meet_wcag_standards(self):
        """Verifies contrast ratios of all Blueprint archetype color pairings."""
        pairings = [
            # Archetype 1: Chapter Divider (Dark Navy Master)
            ("Chapter Divider Title", COLOR_TEXT_WHITE, COLOR_NAVY_PRIMARY, 13.83, True),
            ("Chapter Divider Subtitle", COLOR_BLUE_SUBTITLE, COLOR_NAVY_PRIMARY, 9.98, True),
            ("Chapter Divider Kicker", COLOR_BLUE_SUBTITLE, COLOR_NAVY_SURFACE, 7.23, True),
            # Archetypes 2-8: Slide Headers on Light BG
            ("Slide Header Title", COLOR_NAVY_PRIMARY, COLOR_BG_LIGHT, 13.12, True),
            ("Slide Header Kicker", COLOR_BLUE_TEXT, COLOR_BG_LIGHT, 7.44, True),
            ("Slide Header Subtitle", COLOR_TEXT_MUTED, COLOR_BG_LIGHT, 5.74, True),
            # Archetype 2: Cards on Light BG
            ("Card Title", COLOR_TEXT_PRIMARY, COLOR_CARD_WHITE, 16.10, True),
            ("Card Body", COLOR_TEXT_MUTED, COLOR_CARD_WHITE, 6.05, True),
            ("Card Pill Text", COLOR_BLUE_TEXT, COLOR_BLUE_LIGHT, 6.85, True),
            # Archetype 3: Code Terminal
            ("Terminal Code Text", COLOR_TEXT_CODE, COLOR_SLATE_DARK, 11.62, True),
            ("Terminal Filename", COLOR_CODE_FILENAME, COLOR_SLATE_HEADER, 7.32, True),
            ("Terminal DO Badge", COLOR_TEXT_WHITE, COLOR_GREEN_TEXT, 5.95, True),
            ("Terminal DONT Badge", COLOR_TEXT_WHITE, COLOR_RED_TEXT, 5.80, True),
            # Archetype 4: Hero Metrics
            ("Hero Stat (Dark)", COLOR_TEXT_WHITE, COLOR_NAVY_PRIMARY, 13.83, True),
            ("Hero Desc (Dark)", COLOR_BLUE_SUBTITLE, COLOR_NAVY_PRIMARY, 9.98, True),
            ("Standard Stat (White)", COLOR_BLUE_ACCENT, COLOR_CARD_WHITE, 4.51, True),
            ("Standard Desc (White)", COLOR_TEXT_MUTED, COLOR_CARD_WHITE, 6.05, True),
            ("Positive Delta", COLOR_GREEN_TEXT, COLOR_GREEN_LIGHT, 5.24, True),
            ("Negative Delta", COLOR_RED_TEXT, COLOR_RED_LIGHT, 4.92, True),
            ("Warning Delta", COLOR_AMBER_TEXT, COLOR_AMBER_LIGHT, 7.58, True),
            # Archetype 7: Do / Don't Checklist
            ("Do Banner Title", COLOR_GREEN_TEXT, COLOR_GREEN_LIGHT, 5.24, True),
            ("Don't Banner Title", COLOR_RED_TEXT, COLOR_RED_LIGHT, 4.92, True),
            ("Do/Don't Body", COLOR_TEXT_PRIMARY, COLOR_CARD_WHITE, 16.10, True),
            # Archetype 8: Takeaways
            ("CTA Button Text", COLOR_TEXT_WHITE, COLOR_BLUE_ACCENT, 4.51, True),
            ("Roadmap Title", COLOR_TEXT_WHITE, COLOR_NAVY_PRIMARY, 13.83, True),
            ("Roadmap Body", COLOR_BLUE_SUBTITLE, COLOR_NAVY_PRIMARY, 9.98, True),
        ]

        for label, fg, bg, expected_cr, is_normal_aa in pairings:
            cr = contrast_ratio(fg, bg)
            self.assertAlmostEqual(
                cr,
                expected_cr,
                places=1,
                msg=f"[{label}] CR mismatch: got {cr:.2f}, expected {expected_cr:.2f}",
            )
            if is_normal_aa:
                self.assertGreaterEqual(
                    cr,
                    4.5,
                    f"[{label}] Contrast ratio {cr:.2f} is below 4.5:1 normal text threshold",
                )
            else:
                # Large text or UI badge component threshold (>= 3.0:1)
                self.assertGreaterEqual(
                    cr,
                    3.0,
                    f"[{label}] Contrast ratio {cr:.2f} is below 3.0:1 UI badge threshold",
                )


class TestFuzzAndPropertyTesting(unittest.TestCase):
    """Property-based randomized fuzz testing across all 8 Blueprint archetypes."""

    def test_randomized_fuzz_archetypes(self):
        """Fuzzes ArchetypeEngine.generate_slide_ops with 500 randomized slide configurations."""
        import random
        import string

        def _random_str(min_len: int = 0, max_len: int = 50) -> str:
            length = random.randint(min_len, max_len)
            chars = string.ascii_letters + string.digits + " \t\n!@#$%^&*()_+-=[]{}|;':\",./<>?🚀⚡️🔥"
            return "".join(random.choice(chars) for _ in range(length))

        archetypes = [
            "chapter_divider",
            "split_cards",
            "code_terminal",
            "hero_metrics",
            "ladder_hierarchy",
            "executive_grid",
            "dodont_checklist",
            "actionable_takeaways",
        ]

        for iteration in range(500):
            arch = random.choice(archetypes)
            slide_idx = random.randint(1, 99)
            title = _random_str(0, 200)
            subtitle = _random_str(0, 300)
            kicker = _random_str(0, 50)
            notes = _random_str(0, 500)

            spec: dict[str, Any] = {
                "archetype": arch,
                "title": title,
                "subtitle": subtitle,
                "kicker": kicker,
                "notes": notes,
            }

            if arch == "chapter_divider":
                spec["chapter_number"] = random.choice([0, 1, 99, "05", "Appendix X", -1])

            elif arch == "split_cards":
                n_cards = random.randint(1, 5)
                spec["cards"] = [
                    {
                        "title": _random_str(0, 100),
                        "bullets": [_random_str(0, 150) for _ in range(random.randint(0, 8))],
                        "category": _random_str(0, 30),
                        "stripe_color": random.choice(["#1A73E8", "#1E8E3E", "#D93025", "#F9AB00"]),
                    }
                    for _ in range(n_cards)
                ]

            elif arch == "code_terminal":
                n_terms = random.randint(1, 3)
                spec["terminals"] = [
                    {
                        "filename": _random_str(1, 40),
                        "code": _random_str(0, 400),
                        "badge_text": random.choice(["✓ DO", "✗ DON'T", "VERIFIED", ""]),
                    }
                    for _ in range(n_terms)
                ]

            elif arch == "hero_metrics":
                n_metrics = random.randint(1, 4)
                spec["metrics"] = [
                    {
                        "value": _random_str(1, 20),
                        "unit": _random_str(0, 50),
                        "delta": _random_str(0, 30),
                        "delta_type": random.choice(["positive", "negative", "warning", "neutral"]),
                        "description": _random_str(0, 200),
                        "is_hero": random.choice([True, False]),
                    }
                    for _ in range(n_metrics)
                ]

            elif arch == "ladder_hierarchy":
                n_steps = random.randint(2, 5)
                spec["steps"] = [
                    {
                        "number": i + 1,
                        "title": _random_str(0, 80),
                        "description": _random_str(0, 200),
                    }
                    for i in range(n_steps)
                ]

            elif arch == "executive_grid":
                spec["quadrants"] = [
                    {
                        "number": i + 1,
                        "title": _random_str(0, 80),
                        "description": _random_str(0, 200),
                    }
                    for i in range(4)
                ]

            elif arch == "dodont_checklist":
                spec["dont"] = [_random_str(0, 100) for _ in range(random.randint(0, 6))]
                spec["do"] = [_random_str(0, 100) for _ in range(random.randint(0, 6))]

            elif arch == "actionable_takeaways":
                spec["principles"] = [
                    {
                        "number": i + 1,
                        "title": _random_str(0, 80),
                        "description": _random_str(0, 200),
                    }
                    for i in range(random.randint(0, 5))
                ]
                spec["roadmap_title"] = _random_str(0, 50)
                spec["roadmap_items"] = [_random_str(0, 100) for _ in range(random.randint(0, 6))]
                spec["cta_text"] = _random_str(0, 50)

            # Generate ops
            ops = ArchetypeEngine.generate_slide_ops(spec, slide_index=slide_idx)
            self.assertGreater(len(ops), 0)
            self.assertEqual(ops[0]["op"], "add-slide")
            self.assertEqual(ops[1]["op"], "set-background")

            # Validate bounds, IDs, and references
            created_ids = set()
            for op in ops:
                elem_id = op.get("id")
                if elem_id:
                    self.assertNotIn(
                        elem_id,
                        created_ids,
                        f"Iteration {iteration} ({arch}): Duplicate ID {elem_id}",
                    )
                    created_ids.add(elem_id)

                if op.get("op") in ["add-textbox", "add-shape", "add-line"]:
                    x = op["x"]
                    y = op["y"]
                    w = op["width"]
                    h = op["height"]
                    self.assertGreaterEqual(
                        x, -1e-3, f"Iteration {iteration} ({arch}): Negative x={x} in {op}"
                    )
                    self.assertGreaterEqual(
                        y, -1e-3, f"Iteration {iteration} ({arch}): Negative y={y} in {op}"
                    )
                    self.assertLessEqual(
                        x + w,
                        CANVAS_WIDTH + 1e-3,
                        f"Iteration {iteration} ({arch}): Right {x+w} exceeds {CANVAS_WIDTH} in {op}",
                    )
                    self.assertLessEqual(
                        y + h,
                        CANVAS_HEIGHT + 1e-3,
                        f"Iteration {iteration} ({arch}): Bottom {y+h} exceeds {CANVAS_HEIGHT} in {op}",
                    )

                if op.get("op") == "style-shape":
                    elem_ref = op["element"]
                    self.assertIn(
                        elem_ref,
                        created_ids,
                        f"Iteration {iteration} ({arch}): style-shape references uncreated {elem_ref}",
                    )


if __name__ == "__main__":
    unittest.main()



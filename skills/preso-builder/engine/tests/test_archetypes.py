"""Unit tests for preso.engine.archetypes module and ArchetypeEngine."""

import unittest
from dataclasses import dataclass

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
from preso.engine.design_tokens import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    COLOR_AMBER_LIGHT,
    COLOR_AMBER_WARN,
    COLOR_BG_LIGHT,
    COLOR_BLUE_ACCENT,
    COLOR_CARD_WHITE,
    COLOR_GREEN_DO,
    COLOR_GREEN_LIGHT,
    COLOR_NAVY_PRIMARY,
    COLOR_RED_DONT,
    COLOR_RED_LIGHT,
    COLOR_SLATE_DARK,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_WHITE,
    FONT_FAMILY_BODY,
    FONT_FAMILY_CODE,
    FONT_FAMILY_HEADING,
    FONT_SIZE_CHAPTER_NUM,
    FONT_SIZE_CHAPTER_TITLE,
    FONT_SIZE_HERO_STAT,
)


@dataclass
class CustomSlideSpec:
    """Mock slide spec class for testing object-based dispatcher."""

    archetype: str
    title: str
    subtitle: str
    kicker: str
    cards: list
    speaker_notes: str = ""


class TestArchetypeGenerators(unittest.TestCase):
    """Unit tests for individual archetype batch generator functions."""

    def _verify_slide_invariants(self, ops: list[dict], expected_slide_id: str):
        """Verifies common structural invariants across generated batch ops."""
        # 1. First op must be add-slide
        self.assertGreater(len(ops), 0)
        self.assertEqual(ops[0]["op"], "add-slide")
        self.assertEqual(ops[0]["id"], expected_slide_id)
        self.assertEqual(ops[0]["layout"], "BLANK")

        # 2. Second op is set-background
        self.assertEqual(ops[1]["op"], "set-background")
        self.assertEqual(ops[1]["slide"], expected_slide_id)

        # 3. Collect element IDs and verify uniqueness
        seen_ids = set()
        for op in ops:
            op_type = op.get("op")
            self.assertIn(
                op_type,
                [
                    "add-slide",
                    "set-background",
                    "add-textbox",
                    "add-shape",
                    "style-shape",
                    "add-line",
                    "set-notes",
                ],
            )

            # Check bounds for positioned elements
            if op_type in ["add-textbox", "add-shape", "add-line"]:
                x = op["x"]
                y = op["y"]
                w = op["width"]
                h = op["height"]
                self.assertGreaterEqual(x, 0.0, f"Negative x in {op}")
                self.assertGreaterEqual(y, 0.0, f"Negative y in {op}")
                self.assertLessEqual(x + w, CANVAS_WIDTH + 1e-4, f"X overflow in {op}")
                self.assertLessEqual(y + h, CANVAS_HEIGHT + 1e-4, f"Y overflow in {op}")

            if op_type == "add-textbox":
                font_fam = op.get("font_family")
                self.assertIn(
                    font_fam,
                    [FONT_FAMILY_HEADING, FONT_FAMILY_BODY, FONT_FAMILY_CODE],
                    f"Unexpected font family {font_fam}",
                )

            # Verify unique IDs
            elem_id = op.get("id")
            if elem_id:
                self.assertNotIn(elem_id, seen_ids, f"Duplicate ID: {elem_id}")
                seen_ids.add(elem_id)

    # -------------------------------------------------------------------------
    # 1. Archetype 1: Chapter Divider
    # -------------------------------------------------------------------------
    def test_generate_chapter_divider(self):
        ops = generate_chapter_divider(
            slide_id="SLIDE_01_CHAPTER",
            chapter_number=1,
            title="The Modern AI Factory Architecture",
            subtitle="Transitioning to verified compilation engines.",
            speaker_notes="Welcome to Chapter 1.",
        )
        self._verify_slide_invariants(ops, "SLIDE_01_CHAPTER")

        # Background check (White canvas)
        self.assertEqual(ops[1]["color"], COLOR_CARD_WHITE)

        # Rainbow bar segments
        red_bar = next(op for op in ops if op.get("id") == "BAR_S01_RED")
        self.assertEqual(red_bar["background_color"], "#EA4335")

        # Find specific elements
        num_op = next(op for op in ops if op.get("id") == "NUM_S01")
        self.assertEqual(num_op["text"], "01")
        self.assertIn(num_op["font_size"], (56.0, 60.0, 72.0))
        self.assertEqual(num_op["font_family"], FONT_FAMILY_HEADING)

        title_op = next(op for op in ops if op.get("id") == "TITL_S01")
        self.assertEqual(title_op["text"], "The Modern AI Factory Architecture")
        self.assertIn(title_op["font_size"], (46.0, 54.0, 56.0, 72.0))

        notes_op = next(op for op in ops if op.get("op") == "set-notes")
        self.assertEqual(notes_op["text"], "Welcome to Chapter 1.")

    def test_generate_chapter_divider_string_number_and_custom_kicker(self):
        ops = generate_chapter_divider(
            slide_id="SLIDE_08_CHAPTER",
            chapter_number="08",
            title="Appendix & References",
            subtitle="Additional architecture diagrams",
            kicker="MODULE",
        )
        self._verify_slide_invariants(ops, "SLIDE_08_CHAPTER")
        num_op = next(op for op in ops if op.get("id") == "NUM_S08")
        self.assertEqual(num_op["text"], "08")

    # -------------------------------------------------------------------------
    # 2. Archetype 2: Split Cards
    # -------------------------------------------------------------------------
    def test_generate_split_cards_2_cards(self):
        cards = [
            CardSpec(
                title="Ingestion Engine",
                bullets=["Parse AST from repo", "Extract models", "Format snippets"],
                category="INPUT",
            ),
            CardSpec(
                title="Compiler Pipeline",
                bullets=["Deterministic coordinate math", "Single-pass batch gen"],
                category="OUTPUT",
            ),
        ]
        ops = generate_split_cards(
            slide_id="SLIDE_02_SPLIT",
            title="Two Pillars of Presentation Builder",
            subtitle="Modular ingestion and batch generation pipeline",
            kicker="ARCHITECTURE",
            cards=cards,
            speaker_notes="Notice the clear 2-column split comparison.",
        )
        self._verify_slide_invariants(ops, "SLIDE_02_SPLIT")

        card1 = next(op for op in ops if op.get("id") == "CARD_S02_C1")
        card2 = next(op for op in ops if op.get("id") == "CARD_S02_C2")
        self.assertEqual(card1["width"], 312.0)
        self.assertEqual(card2["width"], 312.0)
        self.assertEqual(card1["x"], 36.0)
        self.assertEqual(card2["x"], 372.0)

    def test_generate_split_cards_3_cards(self):
        cards = [
            {"title": "Card A", "bullets": ["A1", "A2"], "category": "CAT A"},
            {"title": "Card B", "bullets": ["B1", "B2"], "category": "CAT B"},
            {"title": "Card C", "bullets": ["C1", "C2"], "category": "CAT C"},
        ]
        ops = generate_split_cards(
            slide_id="SLIDE_03_SPLIT3",
            title="Three Pillar Model",
            subtitle="Overview of three subsystems",
            kicker="PILLARS",
            cards=cards,
        )
        self._verify_slide_invariants(ops, "SLIDE_03_SPLIT3")

        card1 = next(op for op in ops if op.get("id") == "CARD_S03_C1")
        card2 = next(op for op in ops if op.get("id") == "CARD_S03_C2")
        card3 = next(op for op in ops if op.get("id") == "CARD_S03_C3")
        self.assertEqual(card1["width"], 204.0)
        self.assertEqual(card2["width"], 204.0)
        self.assertEqual(card3["width"], 204.0)

    def test_generate_split_cards_empty_raises_error(self):
        with self.assertRaises(ValueError):
            generate_split_cards(
                slide_id="SLIDE_02_ERR",
                title="T",
                subtitle="S",
                kicker="K",
                cards=[],
            )

    # -------------------------------------------------------------------------
    # 3. Archetype 3: Code Terminal Box
    # -------------------------------------------------------------------------
    def test_generate_code_terminal_dual(self):
        terminals = [
            TerminalSpec(
                filename="legacy.py",
                code="def handle():\n    pass",
                badge_text="✗ DON'T",
                badge_bg=COLOR_RED_DONT,
            ),
            TerminalSpec(
                filename="modern.py",
                code="async def handle():\n    return 200",
                badge_text="✓ DO",
                badge_bg=COLOR_GREEN_DO,
            ),
        ]
        ops = generate_code_terminal(
            slide_id="SLIDE_04_CODE",
            title="Automated Ratchet Enforcement",
            subtitle="Side-by-side syntax comparison",
            kicker="CODE QUALITY",
            terminals=terminals,
            speaker_notes="Demonstrating the side-by-side terminal ratchet.",
        )
        self._verify_slide_invariants(ops, "SLIDE_04_CODE")

        t_left = next(op for op in ops if op.get("id") == "TERM_S04_L_BG")
        t_right = next(op for op in ops if op.get("id") == "TERM_S04_R_BG")
        self.assertEqual(t_left["background_color"], COLOR_SLATE_DARK)
        self.assertEqual(t_right["background_color"], COLOR_SLATE_DARK)

        b_left = next(op for op in ops if op.get("id") == "BADGE_S04_L")
        b_right = next(op for op in ops if op.get("id") == "BADGE_S04_R")
        self.assertEqual(b_left["text"], "✗ DON'T")
        self.assertEqual(b_right["text"], "✓ DO")

        code_left = next(op for op in ops if op.get("id") == "CODE_S04_L")
        self.assertEqual(code_left["font_family"], FONT_FAMILY_CODE)

    def test_generate_code_terminal_single_full_width(self):
        terminals = [
            TerminalSpec(
                filename="pipeline.py",
                code="class Pipeline:\n    def run(self):\n        return True",
            )
        ]
        ops = generate_code_terminal(
            slide_id="SLIDE_05_CODE_FULL",
            title="Full Width Pipeline Implementation",
            subtitle="Comprehensive class architecture",
            kicker="IMPLEMENTATION",
            terminals=terminals,
        )
        self._verify_slide_invariants(ops, "SLIDE_05_CODE_FULL")

        t_full = next(op for op in ops if op.get("id") == "TERM_S05_T1_BG")
        self.assertEqual(t_full["width"], 648.0)

    def test_generate_code_terminal_empty_raises_error(self):
        with self.assertRaises(ValueError):
            generate_code_terminal(
                slide_id="SLIDE_05_ERR",
                title="T",
                subtitle="S",
                kicker="K",
                terminals=[],
            )

    # -------------------------------------------------------------------------
    # 4. Archetype 4: Hero Metrics
    # -------------------------------------------------------------------------
    def test_generate_hero_metrics(self):
        metrics = [
            MetricSpec(
                value="10x",
                unit="Pipeline Velocity",
                delta="+340% YoY",
                delta_type="positive",
                description="Automated code generation time.",
            ),
            MetricSpec(
                value="$4.2M",
                unit="Annual OPEX Saved",
                delta="-68% Cloud Run",
                delta_type="negative",
                description="Shifted manual triage to agents.",
                is_hero=True,
            ),
            MetricSpec(
                value="99.9%",
                unit="First-Pass Rate",
                delta="~0% Drift",
                delta_type="warning",
                description="Verified via QA ratchet loop.",
            ),
        ]
        ops = generate_hero_metrics(
            slide_id="SLIDE_06_METRICS",
            title="Measurable Factory Throughput & Cost Savings",
            subtitle="Key economic metrics from automated pipelines",
            kicker="ROI & ECONOMICS",
            metrics=metrics,
            speaker_notes="Highlighting the 10x velocity and $4.2M OPEX savings.",
        )
        self._verify_slide_invariants(ops, "SLIDE_06_METRICS")

        # Metric 2 is Hero -> Navy background
        card2 = next(op for op in ops if op.get("id") == "CARD_S06_M2")
        self.assertEqual(card2["background_color"], COLOR_NAVY_PRIMARY)

        # Metric 1 is standard -> White background
        card1 = next(op for op in ops if op.get("id") == "CARD_S06_M1")
        self.assertEqual(card1["background_color"], COLOR_CARD_WHITE)

        stat1 = next(op for op in ops if op.get("id") == "STAT_S06_M1")
        self.assertEqual(stat1["text"], "10x")
        self.assertEqual(stat1["font_size"], FONT_SIZE_HERO_STAT)

        # Check delta colors
        delta2 = next(op for op in ops if op.get("id") == "DELTA_S06_M2")
        self.assertEqual(delta2["background_color"], COLOR_RED_LIGHT)

        delta3 = next(op for op in ops if op.get("id") == "DELTA_S06_M3")
        self.assertEqual(delta3["background_color"], COLOR_AMBER_LIGHT)

    def test_generate_hero_metrics_empty_raises_error(self):
        with self.assertRaises(ValueError):
            generate_hero_metrics(
                slide_id="SLIDE_06_ERR",
                title="T",
                subtitle="S",
                kicker="K",
                metrics=[],
            )

    # -------------------------------------------------------------------------
    # 5. Archetype 5: Ladder / Stepped Hierarchy
    # -------------------------------------------------------------------------
    def test_generate_ladder_hierarchy(self):
        steps = [
            StepSpec(number=1, title="Ingest", description="Scan AST from repository."),
            StepSpec(number=2, title="Compile", description="Build single-pass batch."),
            StepSpec(number=3, title="Ratchet", description="Execute visual QA loop."),
            StepSpec(number=4, title="Deploy", description="Render Google Slides deck."),
        ]
        ops = generate_ladder_hierarchy(
            slide_id="SLIDE_07_LADDER",
            title="4-Step Progressive Architecture Maturity",
            subtitle="Step-by-step pipeline from codebase to executive slides",
            kicker="PROCESS FLOW",
            steps=steps,
            speaker_notes="Walking through the four maturity steps.",
        )
        self._verify_slide_invariants(ops, "SLIDE_07_LADDER")

        # Check connectors (3 connectors between 4 steps)
        connectors = [op for op in ops if op.get("op") == "add-line"]
        self.assertEqual(len(connectors), 3)
        self.assertEqual(connectors[0]["id"], "CONN_S07_1_2")
        self.assertEqual(connectors[0]["end_arrow"], "FILL_ARROW")

        # Check 4 step rungs
        for i in range(1, 5):
            rung = next(op for op in ops if op.get("id") == f"RUNG_S07_{i}")
            self.assertEqual(rung["width"], 144.0)

    def test_generate_ladder_hierarchy_invalid_steps_raises(self):
        with self.assertRaises(ValueError):
            generate_ladder_hierarchy(
                slide_id="SLIDE_07_ERR",
                title="T",
                subtitle="S",
                kicker="K",
                steps=[StepSpec(1, "Single", "Desc")],
            )

    # -------------------------------------------------------------------------
    # 6. Archetype 6: Executive 1-Liner Grid
    # -------------------------------------------------------------------------
    def test_generate_executive_grid(self):
        quadrants = [
            QuadrantSpec(number=1, title="Invariant Testing", description="Full coverage across AST."),
            QuadrantSpec(number=2, title="Single-Pass Batch", description="Deterministic payload build."),
            QuadrantSpec(number=3, title="Zero Manual Layout", description="Programmatic point geometry."),
            QuadrantSpec(number=4, title="Multimodal Visual QA", description="Automated thumbnail diffs."),
        ]
        ops = generate_executive_grid(
            slide_id="SLIDE_08_GRID",
            title="Executive 4-Pillar Architectural Framework",
            subtitle="Four guiding pillars of the presentation compiler",
            kicker="STRATEGY",
            quadrants=quadrants,
            speaker_notes="Reviewing the 4 core pillars.",
        )
        self._verify_slide_invariants(ops, "SLIDE_08_GRID")

        for i in range(1, 5):
            quad = next(op for op in ops if op.get("id") == f"QUAD_S08_Q{i}")
            self.assertEqual(quad["width"], 312.0)
            self.assertEqual(quad["height"], 130.0)

    def test_generate_executive_grid_invalid_count_raises(self):
        with self.assertRaises(ValueError):
            generate_executive_grid(
                slide_id="SLIDE_08_ERR",
                title="T",
                subtitle="S",
                kicker="K",
                quadrants=[QuadrantSpec(1, "Q1", "D1"), QuadrantSpec(2, "Q2", "D2")],
            )

    # -------------------------------------------------------------------------
    # 7. Archetype 7: Do / Don't Checklist
    # -------------------------------------------------------------------------
    def test_generate_dodont_checklist(self):
        dont_items = [
            "Hardcoded pixel offsets without geometry tokens",
            "Multi-pass API calls with race conditions",
            "Manual unverified visual review",
        ]
        do_items = [
            "Calculated point-geometry tokens with safe bounds",
            "Atomic single-pass gslides batch payloads",
            "Automated export-thumbnail QA verifier",
        ]
        ops = generate_dodont_checklist(
            slide_id="SLIDE_09_DODONT",
            title="Production Architectural Guidelines",
            subtitle="Anti-patterns vs Blueprint standards",
            kicker="GOVERNANCE",
            dont_items=dont_items,
            do_items=do_items,
            speaker_notes="Compare anti-patterns on left with standards on right.",
        )
        self._verify_slide_invariants(ops, "SLIDE_09_DODONT")

        banner_dont = next(op for op in ops if op.get("id") == "BANNER_S09_DONT")
        self.assertEqual(banner_dont["background_color"], COLOR_RED_LIGHT)

        banner_do = next(op for op in ops if op.get("id") == "BANNER_S09_DO")
        self.assertEqual(banner_do["background_color"], COLOR_GREEN_LIGHT)

    def test_generate_dodont_checklist_dict_with_custom_titles(self):
        dont_dict = {
            "title": "✗ LEGACY DESIGN TRAPS",
            "items": ["Manual coordinate guesswork", "Unvalidated typography"],
        }
        do_dict = {
            "title": "✓ MODERN BLUEPRINT RULES",
            "items": ["Formulaic coordinate engine", "Strict font hierarchy"],
        }
        ops = generate_dodont_checklist(
            slide_id="SLIDE_09_DODONT2",
            title="Design Rules",
            subtitle="Comparison of design workflows",
            kicker="RULES",
            dont_items=dont_dict,
            do_items=do_dict,
        )
        self._verify_slide_invariants(ops, "SLIDE_09_DODONT2")

        titl_dont = next(op for op in ops if op.get("id") == "TITL_S09_DONT")
        titl_do = next(op for op in ops if op.get("id") == "TITL_S09_DO")
        self.assertEqual(titl_dont["text"], "✗ LEGACY DESIGN TRAPS")
        self.assertEqual(titl_do["text"], "✓ MODERN BLUEPRINT RULES")

    # -------------------------------------------------------------------------
    # 8. Archetype 8: Actionable Takeaways
    # -------------------------------------------------------------------------
    def test_generate_actionable_takeaways(self):
        principles = [
            PrincipleSpec(number=1, title="Ingest Repository AST", description="Automated structure parse."),
            PrincipleSpec(number=2, title="Generate Verified Batch Spec", description="Single-pass compiler."),
            PrincipleSpec(number=3, title="Execute Automated QA", description="Zero-defect certification."),
        ]
        ops = generate_actionable_takeaways(
            slide_id="SLIDE_10_TAKEAWAYS",
            title="Implementation Roadmap & Key Action Items",
            subtitle="Closing milestones and next steps",
            kicker="SUMMARY",
            principles=principles,
            roadmap_title="MILESTONES & TIMELINE",
            roadmap_items=["Phase 1: Engine Core", "Phase 2: Compiler", "Phase 3: Visual QA"],
            cta_text="START BUILDING NOW →",
            speaker_notes="Final takeaways and next steps for the engineering team.",
        )
        self._verify_slide_invariants(ops, "SLIDE_10_TAKEAWAYS")

        left_panel = next(op for op in ops if op.get("id") == "PANEL_S10_LEFT")
        right_panel = next(op for op in ops if op.get("id") == "PANEL_S10_RIGHT")
        self.assertEqual(left_panel["width"], 380.0)
        self.assertEqual(right_panel["width"], 244.0)
        self.assertEqual(right_panel["background_color"], COLOR_NAVY_PRIMARY)

        cta_shape = next(op for op in ops if op.get("id") == "BTN_S10_CTA")
        cta_txt = next(op for op in ops if op.get("id") == "BTN_TXT_S10_CTA")
        self.assertEqual(cta_shape["background_color"], COLOR_BLUE_ACCENT)
        self.assertEqual(cta_txt["text"], "START BUILDING NOW →")


class TestArchetypeEngineDispatcher(unittest.TestCase):
    """Tests ArchetypeEngine centralized dispatching mechanism."""

    def test_dispatch_all_8_archetypes_from_dict(self):
        specs = [
            {
                "archetype": "chapter_divider",
                "chapter_number": 1,
                "title": "Chapter 1",
                "subtitle": "Overview",
                "notes": "Notes 1",
            },
            {
                "archetype": "split_cards",
                "title": "Cards",
                "subtitle": "Sub",
                "kicker": "K",
                "cards": [{"title": "C1", "bullets": ["b1"]}],
            },
            {
                "archetype": "code_terminal",
                "title": "Code",
                "subtitle": "Sub",
                "kicker": "K",
                "terminals": [{"filename": "f.py", "code": "x=1"}],
            },
            {
                "archetype": "hero_metrics",
                "title": "Metrics",
                "subtitle": "Sub",
                "kicker": "K",
                "metrics": [{"value": "10x", "unit": "Speed"}],
            },
            {
                "archetype": "ladder_hierarchy",
                "title": "Ladder",
                "subtitle": "Sub",
                "kicker": "K",
                "steps": [{"number": 1, "title": "S1", "description": "d1"}, {"number": 2, "title": "S2", "description": "d2"}],
            },
            {
                "archetype": "executive_grid",
                "title": "Grid",
                "subtitle": "Sub",
                "kicker": "K",
                "quadrants": [
                    {"number": 1, "title": "Q1", "description": "d1"},
                    {"number": 2, "title": "Q2", "description": "d2"},
                    {"number": 3, "title": "Q3", "description": "d3"},
                    {"number": 4, "title": "Q4", "description": "d4"},
                ],
            },
            {
                "archetype": "dodont_checklist",
                "title": "DoDont",
                "subtitle": "Sub",
                "kicker": "K",
                "dont": ["bad"],
                "do": ["good"],
            },
            {
                "archetype": "actionable_takeaways",
                "title": "Takeaways",
                "subtitle": "Sub",
                "kicker": "K",
                "principles": [{"number": 1, "title": "P1", "description": "d1"}],
                "roadmap_items": ["item1"],
            },
        ]

        for i, spec in enumerate(specs, start=1):
            ops = ArchetypeEngine.generate_slide_ops(spec, slide_index=i)
            self.assertGreater(len(ops), 0)
            self.assertEqual(ops[0]["op"], "add-slide")

    def test_dispatch_kebab_case_archetypes(self):
        kebab_specs = [
            {"archetype": "chapter-divider", "chapter_number": 1, "title": "C1", "subtitle": "S1"},
            {"archetype": "split-cards", "title": "T", "subtitle": "S", "cards": [{"title": "C", "bullets": ["b"]}]},
            {"archetype": "code-terminal", "title": "T", "subtitle": "S", "terminals": [{"filename": "a.py", "code": "x=1"}]},
            {"archetype": "hero-metrics", "title": "T", "subtitle": "S", "metrics": [{"value": "1", "unit": "U"}]},
            {"archetype": "ladder-hierarchy", "title": "T", "subtitle": "S", "steps": [{"number": 1, "title": "A", "description": "B"}, {"number": 2, "title": "C", "description": "D"}]},
            {"archetype": "executive-grid", "title": "T", "subtitle": "S", "quadrants": [{"number": i, "title": f"T{i}", "description": f"D{i}"} for i in range(1, 5)]},
            {"archetype": "dodont-checklist", "title": "T", "subtitle": "S", "dont": ["d"], "do": ["d"]},
            {"archetype": "actionable-takeaways", "title": "T", "subtitle": "S", "principles": [{"number": 1, "title": "P", "description": "D"}]},
        ]
        for i, spec in enumerate(kebab_specs, start=1):
            ops = ArchetypeEngine.generate_slide_ops(spec, slide_index=i)
            self.assertGreater(len(ops), 0)
            self.assertEqual(ops[0]["op"], "add-slide")

    def test_dispatch_custom_spec_object(self):
        spec_obj = CustomSlideSpec(
            archetype="split_cards",
            title="Object Title",
            subtitle="Object Subtitle",
            kicker="OBJECT",
            cards=[CardSpec("C1", ["Bullet 1"])],
            speaker_notes="Notes from object",
        )
        ops = ArchetypeEngine.generate_slide_ops(spec_obj, slide_index=1)
        self.assertGreater(len(ops), 0)
        self.assertEqual(ops[0]["op"], "add-slide")
        notes_op = next(op for op in ops if op.get("op") == "set-notes")
        self.assertEqual(notes_op["text"], "Notes from object")

    def test_dispatch_invalid_type_raises(self):
        with self.assertRaises(TypeError):
            ArchetypeEngine.generate_slide_ops(12345)

    def test_dispatch_unknown_archetype_raises_error(self):
        with self.assertRaises(ValueError):
            ArchetypeEngine.generate_slide_ops({"archetype": "unknown_type"}, slide_index=1)


if __name__ == "__main__":
    unittest.main()

"""Empirical Adversarial Test Suite for Milestone M1 (Challenger 2).

Verifies:
1. WCAG 2.1 AA/AAA contrast ratios for all generated text and background pairings across all 8 archetypes.
2. gslides batch JSON payload schema and structural invariants for all 8 archetypes.
"""

import json
import unittest
from typing import Any, Dict, List

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
from preso.engine.coordinates import BoundingBox
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
    contrast_ratio,
    ensure_hex,
    is_wcag_aa,
    is_wcag_aaa,
    relative_luminance,
)


class TestAdversarialBatchPayloadSchema(unittest.TestCase):
    """Empirically validates gslides batch JSON schema and structural invariants for all 8 archetypes."""

    VALID_OPS = {
        "add-slide",
        "set-background",
        "add-textbox",
        "add-shape",
        "style-shape",
        "add-line",
        "set-notes",
        "add-table",
        "delete-element",
    }

    def _validate_payload(self, ops: list[dict[str, Any]], expected_slide_id: str):
        # 1. JSON serializability
        serialized = json.dumps(ops)
        loaded = json.loads(serialized)
        self.assertEqual(len(loaded), len(ops))

        # 2. add-slide invariant
        self.assertGreater(len(ops), 0)
        self.assertEqual(ops[0]["op"], "add-slide")
        self.assertEqual(ops[0]["id"], expected_slide_id)
        self.assertEqual(ops[0]["layout"], "BLANK")

        # 3. set-background invariant
        self.assertEqual(ops[1]["op"], "set-background")
        self.assertEqual(ops[1]["slide"], expected_slide_id)
        self.assertTrue(ops[1]["color"].startswith("#"))

        # 4. Element IDs and coordinates
        seen_ids = set()
        for idx, op in enumerate(ops):
            op_name = op.get("op")
            self.assertIn(op_name, self.VALID_OPS, f"Op #{idx} has invalid op: {op_name}")

            if "slide" in op:
                self.assertEqual(op["slide"], expected_slide_id)

            if "id" in op:
                elem_id = op["id"]
                self.assertNotIn(elem_id, seen_ids, f"Duplicate ID '{elem_id}' in op #{idx}")
                seen_ids.add(elem_id)

            if op_name in ["add-textbox", "add-shape", "add-line"]:
                x = op["x"]
                y = op["y"]
                w = op["width"]
                h = op["height"]
                self.assertGreaterEqual(x, 0.0)
                self.assertGreaterEqual(y, 0.0)
                self.assertLessEqual(x + w, CANVAS_WIDTH + 1e-3)
                self.assertLessEqual(y + h, CANVAS_HEIGHT + 1e-3)

            if op_name == "add-textbox":
                self.assertIn("text", op)
                self.assertGreater(op["font_size"], 0.0)
                self.assertIn(
                    op["font_family"],
                    [FONT_FAMILY_HEADING, FONT_FAMILY_BODY, FONT_FAMILY_CODE],
                )
                self.assertEqual(op["color"], ensure_hex(op["color"]))

            if op_name == "style-shape":
                self.assertIn(op["element"], seen_ids)

            if op_name == "set-notes":
                self.assertIn("text", op)

    def test_all_8_archetypes_payload_schema(self):
        """Tests that all 8 archetypes produce 100% structurally valid gslides batch JSON payloads."""
        payloads = [
            ("SLIDE_01", generate_chapter_divider("SLIDE_01", 1, "Title", "Sub", "Notes")),
            ("SLIDE_02", generate_split_cards("SLIDE_02", "T", "S", "K", [CardSpec("C1", ["b1"])])),
            ("SLIDE_03", generate_code_terminal("SLIDE_03", "T", "S", "K", [TerminalSpec("a.py", "x=1")])),
            ("SLIDE_04", generate_hero_metrics("SLIDE_04", "T", "S", "K", [MetricSpec("10", "U")])),
            ("SLIDE_05", generate_ladder_hierarchy("SLIDE_05", "T", "S", "K", [StepSpec(1, "S1", "D1"), StepSpec(2, "S2", "D2")])),
            ("SLIDE_06", generate_executive_grid("SLIDE_06", "T", "S", "K", [QuadrantSpec(i, f"Q{i}", f"D{i}") for i in range(1, 5)])),
            ("SLIDE_07", generate_dodont_checklist("SLIDE_07", "T", "S", "K", ["dont"], ["do"])),
            ("SLIDE_08", generate_actionable_takeaways("SLIDE_08", "T", "S", "K", [PrincipleSpec(1, "P1", "D1")], "ROADMAP", ["item1"])),
        ]
        for slide_id, ops in payloads:
            self._validate_payload(ops, slide_id)


class TestAdversarialWCAGContrastAudit(unittest.TestCase):
    """Empirical audit of WCAG 2.1 AA/AAA contrast ratios."""

    def test_audit_contrast_ratios(self):
        """Evaluates contrast ratios and records passing/failing pairings."""
        pairings = [
            # Archetype 1
            ("Archetype 1 Kicker", COLOR_BLUE_SUBTITLE, COLOR_NAVY_SURFACE, 11.0, True),
            ("Archetype 1 Chapter Num", COLOR_BLUE_SUBTITLE, COLOR_NAVY_PRIMARY, 84.0, True),
            ("Archetype 1 Title", COLOR_TEXT_WHITE, COLOR_NAVY_PRIMARY, 36.0, True),
            ("Archetype 1 Subtitle", COLOR_BLUE_SUBTITLE, COLOR_NAVY_PRIMARY, 16.0, False),
            # Archetype 2
            ("Header Kicker", COLOR_BLUE_TEXT, COLOR_BG_LIGHT, 10.0, True),
            ("Header Title", COLOR_NAVY_PRIMARY, COLOR_BG_LIGHT, 24.0, True),
            ("Header Subtitle", COLOR_TEXT_MUTED, COLOR_BG_LIGHT, 13.0, False),
            ("Card Category Pill", COLOR_BLUE_TEXT, COLOR_BLUE_LIGHT, 10.0, True),
            ("Card Title", COLOR_TEXT_PRIMARY, COLOR_CARD_WHITE, 16.0, True),
            ("Card Body", COLOR_TEXT_MUTED, COLOR_CARD_WHITE, 12.0, False),
            # Archetype 3
            ("Terminal Filename", COLOR_CODE_FILENAME, COLOR_SLATE_HEADER, 11.0, True),
            ("Terminal Do Badge", COLOR_TEXT_WHITE, COLOR_GREEN_TEXT, 10.5, True),
            ("Terminal Don't Badge", COLOR_TEXT_WHITE, COLOR_RED_TEXT, 10.5, True),
            ("Terminal Code", COLOR_TEXT_CODE, COLOR_SLATE_DARK, 10.5, False),
            # Archetype 4
            ("Metric Kicker", COLOR_TEXT_MUTED, COLOR_CARD_WHITE, 10.5, True),
            ("Hero Stat Display", COLOR_BLUE_ACCENT, COLOR_CARD_WHITE, 54.0, True),
            ("Metric Unit", COLOR_TEXT_PRIMARY, COLOR_CARD_WHITE, 13.0, True),
            ("Delta Positive", COLOR_GREEN_TEXT, COLOR_GREEN_LIGHT, 11.0, True),
            ("Delta Negative", COLOR_RED_TEXT, COLOR_RED_LIGHT, 11.0, True),
            ("Delta Warning", COLOR_AMBER_TEXT, COLOR_AMBER_LIGHT, 11.0, True),
            ("Metric Desc", COLOR_TEXT_MUTED, COLOR_CARD_WHITE, 11.5, False),
            ("Hero Card Stat", COLOR_TEXT_WHITE, COLOR_NAVY_PRIMARY, 54.0, True),
            ("Hero Card Unit", COLOR_TEXT_WHITE, COLOR_NAVY_PRIMARY, 13.0, True),
            ("Hero Card Desc", COLOR_BLUE_SUBTITLE, COLOR_NAVY_PRIMARY, 11.5, False),
            # Archetype 5
            ("Step Badge", COLOR_TEXT_WHITE, COLOR_BLUE_ACCENT, 13.0, True),
            ("Step Title", COLOR_TEXT_PRIMARY, COLOR_CARD_WHITE, 14.0, True),
            ("Step Desc", COLOR_TEXT_MUTED, COLOR_CARD_WHITE, 11.0, False),
            # Archetype 6
            ("Grid Pill", COLOR_BLUE_TEXT, COLOR_BLUE_LIGHT, 11.0, True),
            ("Grid Title", COLOR_TEXT_PRIMARY, COLOR_CARD_WHITE, 14.0, True),
            ("Grid Body", COLOR_TEXT_MUTED, COLOR_CARD_WHITE, 11.5, False),
            # Archetype 7
            ("Don't Banner", COLOR_RED_TEXT, COLOR_RED_LIGHT, 13.0, True),
            ("Don't Body", COLOR_TEXT_PRIMARY, COLOR_CARD_WHITE, 12.0, False),
            ("Do Banner", COLOR_GREEN_TEXT, COLOR_GREEN_LIGHT, 13.0, True),
            ("Do Body", COLOR_TEXT_PRIMARY, COLOR_CARD_WHITE, 12.0, False),
            # Archetype 8
            ("Principle Pill", COLOR_BLUE_TEXT, COLOR_BLUE_LIGHT, 11.0, True),
            ("Principle Title", COLOR_TEXT_PRIMARY, COLOR_CARD_WHITE, 14.0, True),
            ("Principle Desc", COLOR_TEXT_MUTED, COLOR_CARD_WHITE, 11.5, False),
            ("Roadmap Title", COLOR_TEXT_WHITE, COLOR_NAVY_PRIMARY, 14.0, True),
            ("Roadmap Body", COLOR_BLUE_SUBTITLE, COLOR_NAVY_PRIMARY, 12.0, False),
            ("CTA Button", COLOR_TEXT_WHITE, COLOR_BLUE_ACCENT, 13.0, True),
        ]

        failures = []
        passes = []

        for name, fg, bg, size, bold in pairings:
            is_large = size >= 18.0 or (size >= 14.0 and bold)
            cr = contrast_ratio(fg, bg)
            aa = is_wcag_aa(fg, bg, is_large_text=is_large)
            aaa = is_wcag_aaa(fg, bg, is_large_text=is_large)
            req_cr = 3.0 if is_large else 4.5

            record = {
                "name": name,
                "fg": fg,
                "bg": bg,
                "size": size,
                "bold": bold,
                "is_large": is_large,
                "cr": round(cr, 2),
                "req": req_cr,
                "aa": aa,
                "aaa": aaa,
            }
            if aa:
                passes.append(record)
            else:
                failures.append(record)

        self.assertGreater(len(passes), 0)
        self.assertEqual(len(failures), 0)


if __name__ == "__main__":
    unittest.main()

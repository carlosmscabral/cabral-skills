"""Comprehensive Empirical Analysis of WCAG 2.1 AA/AAA and Batch Payloads for all 8 Archetypes."""

import json
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
from preso.engine.coordinates import BoundingBox
from preso.engine.design_tokens import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    COLOR_AMBER_LIGHT,
    COLOR_AMBER_WARN,
    COLOR_BG_LIGHT,
    COLOR_BLUE_ACCENT,
    COLOR_BLUE_LIGHT,
    COLOR_BLUE_SUBTITLE,
    COLOR_CARD_BORDER,
    COLOR_CARD_WHITE,
    COLOR_CODE_FILENAME,
    COLOR_DIVIDER,
    COLOR_GREEN_DO,
    COLOR_GREEN_LIGHT,
    COLOR_NAVY_PRIMARY,
    COLOR_NAVY_SURFACE,
    COLOR_RED_DONT,
    COLOR_RED_LIGHT,
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


def run_full_empirical_audit():
    archetype_generators = {
        "1. Chapter Divider": generate_chapter_divider(
            "SLIDE_01", 1, "The AI Factory Blueprint", "A verified architecture", "Speaker notes 1"
        ),
        "2. Split Cards (2-Card)": generate_split_cards(
            "SLIDE_02", "Comparison", "Subtitle", "Kicker",
            [CardSpec("Card 1", ["bullet 1"], "CAT 1"), CardSpec("Card 2", ["bullet 2"], "CAT 2")],
            "Speaker notes 2"
        ),
        "2. Split Cards (3-Card)": generate_split_cards(
            "SLIDE_02B", "3-Card Comparison", "Subtitle", "Kicker",
            [CardSpec("C1", ["b1"], "C1"), CardSpec("C2", ["b2"], "C2"), CardSpec("C3", ["b3"], "C3")],
            "Speaker notes 2b"
        ),
        "3. Code Terminal (Dual)": generate_code_terminal(
            "SLIDE_03", "Code", "Subtitle", "Kicker",
            [TerminalSpec("legacy.py", "pass", "✗ DON'T"), TerminalSpec("modern.py", "return", "✓ DO")],
            "Speaker notes 3"
        ),
        "3. Code Terminal (Single)": generate_code_terminal(
            "SLIDE_03B", "Full Code", "Subtitle", "Kicker",
            [TerminalSpec("full.py", "def run():\n  pass")],
            "Speaker notes 3b"
        ),
        "4. Hero Metrics": generate_hero_metrics(
            "SLIDE_04", "Metrics", "Subtitle", "Kicker",
            [
                MetricSpec("10x", "Velocity", "+300%", "positive", "Desc 1"),
                MetricSpec("$4.2M", "Savings", "-60%", "negative", "Desc 2", is_hero=True),
                MetricSpec("99.9%", "Uptime", "~0%", "warning", "Desc 3"),
            ],
            "Speaker notes 4"
        ),
        "5. Ladder Hierarchy": generate_ladder_hierarchy(
            "SLIDE_05", "Pipeline", "Subtitle", "Kicker",
            [StepSpec(1, "Step 1", "Desc 1"), StepSpec(2, "Step 2", "Desc 2"), StepSpec(3, "Step 3", "Desc 3"), StepSpec(4, "Step 4", "Desc 4")],
            "Speaker notes 5"
        ),
        "6. Executive Grid": generate_executive_grid(
            "SLIDE_06", "Grid", "Subtitle", "Kicker",
            [QuadrantSpec(1, "P1", "D1"), QuadrantSpec(2, "P2", "D2"), QuadrantSpec(3, "P3", "D3"), QuadrantSpec(4, "P4", "D4")],
            "Speaker notes 6"
        ),
        "7. Do / Don't Checklist": generate_dodont_checklist(
            "SLIDE_07", "Checklist", "Subtitle", "Kicker",
            dont_items=["Anti-pattern 1", "Anti-pattern 2"],
            do_items=["Standard 1", "Standard 2"],
            speaker_notes="Speaker notes 7"
        ),
        "8. Actionable Takeaways": generate_actionable_takeaways(
            "SLIDE_08", "Takeaways", "Subtitle", "Kicker",
            principles=[PrincipleSpec(1, "Principle 1", "Desc 1"), PrincipleSpec(2, "Principle 2", "Desc 2"), PrincipleSpec(3, "Principle 3", "Desc 3")],
            roadmap_title="ROADMAP",
            roadmap_items=["Item 1", "Item 2"],
            cta_text="START BUILDING NOW →",
            speaker_notes="Speaker notes 8"
        ),
    }

    print("=" * 80)
    print("EMPIRICAL BATCH PAYLOAD & WCAG CONTRAST AUDIT")
    print("=" * 80)

    total_textboxes = 0
    total_shapes = 0
    total_lines = 0
    wcag_aa_passes = 0
    wcag_aa_failures = 0
    wcag_aaa_passes = 0

    detailed_elements = []

    for arch_name, ops in archetype_generators.items():
        slide_bg = ops[1]["color"] if ops[1]["op"] == "set-background" else "#FFFFFF"
        print(f"\n--- Archetype: {arch_name} (Total Ops: {len(ops)}, Slide BG: {slide_bg}) ---")

        # Track shapes for background context
        shapes_by_id = {}
        for op in ops:
            if op.get("op") == "add-shape":
                shapes_by_id[op["id"]] = op

        for op in ops:
            op_type = op.get("op")
            if op_type == "add-textbox":
                total_textboxes += 1
                elem_id = op["id"]
                text_sample = op["text"].replace("\n", " ")[:30]
                fg = op.get("color", "#000000")
                font_size = op.get("font_size", 12.0)
                is_bold = op.get("bold", False)
                is_large = font_size >= 18.0 or (font_size >= 14.0 and is_bold)

                # Determine effective bg
                if "background_color" in op and op["background_color"] != "transparent":
                    bg = op["background_color"]
                else:
                    # Find containing shape or slide bg
                    tb_x = op["x"]
                    tb_y = op["y"]
                    tb_w = op["width"]
                    tb_h = op["height"]
                    containing_bg = slide_bg
                    for sid, s in shapes_by_id.items():
                        # check if shape encloses textbox center
                        sx, sy, sw, sh = s["x"], s["y"], s["width"], s["height"]
                        if sx <= tb_x + tb_w / 2 <= sx + sw and sy <= tb_y + tb_h / 2 <= sy + sh:
                            s_bg = s.get("background_color")
                            if s_bg and s_bg != "transparent":
                                containing_bg = s_bg
                    bg = containing_bg

                cr = contrast_ratio(fg, bg)
                aa = is_wcag_aa(fg, bg, is_large_text=is_large)
                aaa = is_wcag_aaa(fg, bg, is_large_text=is_large)

                if aa:
                    wcag_aa_passes += 1
                else:
                    wcag_aa_failures += 1

                if aaa:
                    wcag_aaa_passes += 1

                status_str = "PASS (AAA)" if aaa else ("PASS (AA)" if aa else "FAIL (WCAG AA VIOLATION)")

                print(f"  [{status_str}] ID: {elem_id:<20} | Text: '{text_sample:<25}' | Size: {font_size:4.1f}pt {'(B)' if is_bold else '   '} | {fg} on {bg} | CR: {cr:5.2f}:1 (Req: {'3.0:1 (large)' if is_large else '4.5:1'})")

                detailed_elements.append({
                    "archetype": arch_name,
                    "id": elem_id,
                    "text": text_sample,
                    "fg": fg,
                    "bg": bg,
                    "font_size": font_size,
                    "bold": is_bold,
                    "is_large": is_large,
                    "contrast_ratio": round(cr, 2),
                    "wcag_aa": aa,
                    "wcag_aaa": aaa,
                })

            elif op_type == "add-shape":
                total_shapes += 1
            elif op_type == "add-line":
                total_lines += 1

    print("\n" + "=" * 80)
    print("AUDIT SUMMARY")
    print(f"Total Archetypes Audited: {len(archetype_generators)}")
    print(f"Total Textboxes Evaluated: {total_textboxes}")
    print(f"Total Shapes Evaluated: {total_shapes}")
    print(f"Total Lines Evaluated: {total_lines}")
    print(f"WCAG AA Passes: {wcag_aa_passes} / {total_textboxes} ({wcag_aa_passes/total_textboxes*100:.1f}%)")
    print(f"WCAG AA Failures: {wcag_aa_failures} / {total_textboxes} ({wcag_aa_failures/total_textboxes*100:.1f}%)")
    print(f"WCAG AAA Passes: {wcag_aaa_passes} / {total_textboxes} ({wcag_aaa_passes/total_textboxes*100:.1f}%)")
    print("=" * 80)


if __name__ == "__main__":
    run_full_empirical_audit()

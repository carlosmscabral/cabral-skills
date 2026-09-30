"""Comprehensive Batch Payload Invariant and Boundary Checker."""

import json
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
from preso.engine.design_tokens import CANVAS_HEIGHT, CANVAS_WIDTH


def audit_batch_payloads():
    test_cases = {
        "1. Chapter Divider (Standard)": generate_chapter_divider(
            "SLIDE_01", 1, "Title 1", "Subtitle 1", "Notes 1", "CHAPTER"
        ),
        "1. Chapter Divider (String Number & Custom Kicker)": generate_chapter_divider(
            "SLIDE_01B", "09", "Title 1B", "Subtitle 1B", "Notes 1B", "MODULE"
        ),
        "2. Split Cards (1 Card)": generate_split_cards(
            "SLIDE_02A", "1 Card", "Sub", "KICK",
            [{"title": "Card A", "bullets": ["B1", "B2"], "category": "CAT"}]
        ),
        "2. Split Cards (2 Cards)": generate_split_cards(
            "SLIDE_02B", "2 Cards", "Sub", "KICK",
            [
                CardSpec("Card 1", ["Bullet 1", "Bullet 2"], "CAT 1", "#1A73E8"),
                CardSpec("Card 2", ["Bullet 3"], "CAT 2", "#1E8E3E"),
            ]
        ),
        "2. Split Cards (3 Cards)": generate_split_cards(
            "SLIDE_02C", "3 Cards", "Sub", "KICK",
            [
                CardSpec("Card 1", ["Bullet 1"], "CAT 1"),
                CardSpec("Card 2", ["Bullet 2"], "CAT 2"),
                CardSpec("Card 3", ["Bullet 3"], "CAT 3"),
            ]
        ),
        "3. Code Terminal (Dual)": generate_code_terminal(
            "SLIDE_03A", "Dual Code", "Sub", "KICK",
            [
                TerminalSpec("old.py", "def a():\n  pass", "✗ DON'T"),
                TerminalSpec("new.py", "async def a():\n  return 1", "✓ DO"),
            ]
        ),
        "3. Code Terminal (Single Full Width)": generate_code_terminal(
            "SLIDE_03B", "Single Code", "Sub", "KICK",
            [TerminalSpec("main.py", "print('hello world')")]
        ),
        "4. Hero Metrics (2 Cards, 1 Hero)": generate_hero_metrics(
            "SLIDE_04A", "Hero Metrics", "Sub", "KICK",
            [
                MetricSpec("10x", "Velocity", "+300%", "positive", "Desc 1"),
                MetricSpec("$5M", "Cost Saved", "-40%", "negative", "Desc 2", is_hero=True),
            ]
        ),
        "4. Hero Metrics (3 Cards, All Types)": generate_hero_metrics(
            "SLIDE_04B", "3 Metrics", "Sub", "KICK",
            [
                {"value": "100%", "unit": "Pass", "delta": "+5%", "delta_type": "positive", "description": "D1"},
                {"value": "0.1s", "unit": "Latency", "delta": "-90%", "delta_type": "negative", "description": "D2", "is_hero": True},
                {"value": "99.9%", "unit": "SLA", "delta": "~0%", "delta_type": "warning", "description": "D3"},
            ]
        ),
        "5. Ladder Hierarchy (2 Steps)": generate_ladder_hierarchy(
            "SLIDE_05A", "2-Step Flow", "Sub", "KICK",
            [StepSpec(1, "Step 1", "Desc 1"), StepSpec(2, "Step 2", "Desc 2")]
        ),
        "5. Ladder Hierarchy (4 Steps)": generate_ladder_hierarchy(
            "SLIDE_05B", "4-Step Flow", "Sub", "KICK",
            [
                StepSpec(1, "Ingest", "D1"),
                StepSpec(2, "Compile", "D2"),
                StepSpec(3, "Verify", "D3"),
                StepSpec(4, "Deploy", "D4"),
            ]
        ),
        "6. Executive Grid (4 Quadrants)": generate_executive_grid(
            "SLIDE_06", "4 Quadrants", "Sub", "KICK",
            [
                QuadrantSpec(1, "P1", "D1"),
                QuadrantSpec(2, "P2", "D2"),
                QuadrantSpec(3, "P3", "D3"),
                QuadrantSpec(4, "P4", "D4"),
            ]
        ),
        "7. Do / Don't Checklist (Lists)": generate_dodont_checklist(
            "SLIDE_07A", "Guidelines", "Sub", "KICK",
            dont_items=["Bad practice 1", "Bad practice 2"],
            do_items=["Good practice 1", "Good practice 2"],
        ),
        "7. Do / Don't Checklist (Dict with Custom Titles)": generate_dodont_checklist(
            "SLIDE_07B", "Custom Guidelines", "Sub", "KICK",
            dont_items={"title": "✗ PITFALLS", "items": ["Pitfall 1"]},
            do_items={"title": "✓ BLUEPRINTS", "items": ["Blueprint 1"]},
        ),
        "8. Actionable Takeaways (3 Principles + Roadmap + CTA)": generate_actionable_takeaways(
            "SLIDE_08", "Takeaways", "Sub", "KICK",
            principles=[
                PrincipleSpec(1, "P1", "D1"),
                PrincipleSpec(2, "P2", "D2"),
                PrincipleSpec(3, "P3", "D3"),
            ],
            roadmap_title="ROADMAP",
            roadmap_items=["Item 1", "Item 2", "Item 3"],
            cta_text="GET STARTED →",
            speaker_notes="Closing notes",
        ),
    }

    print("=" * 80)
    print("BATCH PAYLOAD STRUCTURAL & GEOMETRIC AUDIT")
    print("=" * 80)

    total_cases = len(test_cases)
    passed_cases = 0

    for name, ops in test_cases.items():
        errors = []
        # JSON test
        try:
            raw_json = json.dumps(ops)
            loaded = json.loads(raw_json)
        except Exception as e:
            errors.append(f"JSON serialization failure: {e}")

        # Op 0 add-slide
        if not ops or ops[0].get("op") != "add-slide":
            errors.append("First op is not 'add-slide'")
        slide_id = ops[0].get("id")

        # Op 1 set-background
        if len(ops) < 2 or ops[1].get("op") != "set-background":
            errors.append("Second op is not 'set-background'")

        # IDs and bounds
        seen_ids = set()
        for idx, op in enumerate(ops):
            op_name = op.get("op")
            if "id" in op:
                if op["id"] in seen_ids:
                    errors.append(f"Duplicate element ID: '{op['id']}' at op #{idx}")
                seen_ids.add(op["id"])

            if "slide" in op and op["slide"] != slide_id:
                errors.append(f"Op #{idx} references wrong slide ID '{op['slide']}' (expected '{slide_id}')")

            if op_name in ["add-textbox", "add-shape", "add-line"]:
                x, y, w, h = op["x"], op["y"], op["width"], op["height"]
                if x < 0 or y < 0:
                    errors.append(f"Negative coordinate in op #{idx}: x={x}, y={y}")
                if x + w > CANVAS_WIDTH + 1e-3 or y + h > CANVAS_HEIGHT + 1e-3:
                    errors.append(f"Boundary overflow in op #{idx}: right={x+w}, bottom={y+h}")

            if op_name == "style-shape":
                if op["element"] not in seen_ids:
                    errors.append(f"style-shape op #{idx} references unknown element '{op['element']}'")

        if not errors:
            passed_cases += 1
            print(f"[PASS] {name:<55} ({len(ops):2d} ops, {len(seen_ids):2d} elements)")
        else:
            print(f"[FAIL] {name:<55} Errors: {errors}")

    print("=" * 80)
    print(f"Batch Payload Audit Result: {passed_cases} / {total_cases} passed ({passed_cases/total_cases*100:.1f}%)")
    print("=" * 80)


if __name__ == "__main__":
    audit_batch_payloads()

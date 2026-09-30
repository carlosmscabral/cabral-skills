"""Unit tests for Structured Blueprint Specification Framework (preso.spec).

Covers data models, schema validation rules, character budget enforcement,
speaker notes requirements, YAML/JSON serialization, and scaffolding presets.
"""

from __future__ import annotations

import io
from pathlib import Path
import tempfile
import unittest

from preso.engine.archetypes import ArchetypeEngine
from preso.spec.models import (
    CardSpec,
    ChapterSpec,
    ChecklistSpec,
    CodeBlockSpec,
    HeroMetricSpec,
    LadderStepSpec,
    MetadataSpec,
    MetricSpec,
    PresentationSpec,
    PrincipleSpec,
    QuadrantSpec,
    SlideSpec,
    StepSpec,
    TakeawaySpec,
    TerminalSpec,
)
from preso.spec.scaffolder import SpecScaffolder
from preso.spec.validator import (
    ARCHETYPE_ALIASES,
    CANONICAL_ARCHETYPES,
    SpecValidator,
    ValidationResult,
)


class TestSpecModels(unittest.TestCase):
    """Tests for dataclass instantiation, alias normalization, and serialization."""

    def test_metadata_spec_defaults_and_dict(self) -> None:
        meta = MetadataSpec(title="Test Title", subtitle="Test Subtitle")
        d = meta.to_dict()
        self.assertEqual(d["title"], "Test Title")
        self.assertEqual(d["subtitle"], "Test Subtitle")
        self.assertEqual(d["template_id"], "1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U")

        restored = MetadataSpec.from_dict(d)
        self.assertEqual(restored.title, "Test Title")
        self.assertEqual(restored.subtitle, "Test Subtitle")

    def test_card_spec_aliases_and_bullets(self) -> None:
        # Test category alias and string bullet parsing
        card = CardSpec.from_dict({
            "header": "Card Header",
            "category_pill": "CATEGORY",
            "bullets": "Bullet 1\nBullet 2",
            "stripe_color": "#1A73E8",
        })
        self.assertEqual(card.title, "Card Header")
        self.assertEqual(card.kicker, "CATEGORY")
        self.assertEqual(card.bullets, ["Bullet 1", "Bullet 2"])
        self.assertEqual(card.theme, "#1A73E8")

        d = card.to_dict()
        self.assertEqual(d["title"], "Card Header")
        self.assertEqual(d["category_pill"], "CATEGORY")
        self.assertEqual(d["stripe_color"], "#1A73E8")

    def test_code_block_spec_status_badge(self) -> None:
        term_do = CodeBlockSpec(filename="test.sh", code="echo 1", status="do")
        self.assertEqual(term_do.badge_text, "✓ DO")

        term_dont = CodeBlockSpec(filename="bad.sh", code="exit 1", status="dont")
        self.assertEqual(term_dont.badge_text, "✗ DON'T")

        d = term_do.to_dict()
        restored = CodeBlockSpec.from_dict(d)
        self.assertEqual(restored.filename, "test.sh")
        self.assertEqual(restored.code, "echo 1")

    def test_hero_metric_spec_aliases(self) -> None:
        metric = HeroMetricSpec.from_dict({
            "stat": "$500",
            "unit": "per month",
            "label": "SAVINGS",
            "context": "Significant operational savings.",
            "is_hero": True,
        })
        self.assertEqual(metric.value, "$500")
        self.assertEqual(metric.description, "Significant operational savings.")
        self.assertTrue(metric.is_hero)

        d = metric.to_dict()
        self.assertEqual(d["value"], "$500")
        self.assertEqual(d["context"], "Significant operational savings.")

    def test_ladder_step_spec_aliases(self) -> None:
        step = LadderStepSpec.from_dict({
            "number": 2,
            "title": "Architecture",
            "description": "System design",
        })
        self.assertEqual(step.step_number, 2)
        self.assertEqual(step.title, "Architecture")

        d = step.to_dict()
        self.assertEqual(d["step_number"], 2)
        self.assertEqual(d["title"], "Architecture")

    def test_quadrant_spec_aliases(self) -> None:
        quad = QuadrantSpec.from_dict({
            "number": "03",
            "title": "Harness",
            "body": "Deterministic execution",
        })
        self.assertEqual(quad.number, "03")
        self.assertEqual(quad.title, "Harness")
        self.assertEqual(quad.narrative, "Deterministic execution")

        d = quad.to_dict()
        self.assertEqual(d["narrative"], "Deterministic execution")
        self.assertEqual(d["body"], "Deterministic execution")

    def test_checklist_spec_and_aliases(self) -> None:
        checklist = ChecklistSpec.from_dict({
            "do": ["Do item 1", "Do item 2"],
            "dont": ["Don't item 1"],
            "takeaway": "Discipline matters",
        })
        self.assertEqual(len(checklist.do_items), 2)
        self.assertEqual(len(checklist.dont_items), 1)
        self.assertEqual(checklist.takeaway, "Discipline matters")

        d = checklist.to_dict()
        self.assertEqual(d["do_items"], ["Do item 1", "Do item 2"])
        self.assertEqual(d["dont_items"], ["Don't item 1"])

    def test_takeaway_spec_principles_parsing(self) -> None:
        takeaway = TakeawaySpec.from_dict({
            "thesis": "Judgement over keystrokes",
            "principles": [
                "Decompose: Break problems down",
                {"title": "Verify", "description": "Always check outputs"},
            ],
            "roadmap_items": ["Step 1", "Step 2"],
            "cta_text": "BEGIN NOW →",
        })
        self.assertEqual(len(takeaway.principles), 2)
        self.assertEqual(takeaway.thesis, "Judgement over keystrokes")
        self.assertEqual(len(takeaway.roadmap_items), 2)

    def test_slide_spec_speaker_notes_property(self) -> None:
        slide = SlideSpec(archetype="chapter_divider", title="Intro", notes="Original notes")
        self.assertEqual(slide.speaker_notes, "Original notes")
        slide.speaker_notes = "Updated notes"
        self.assertEqual(slide.notes, "Updated notes")

    def test_presentation_spec_yaml_roundtrip(self) -> None:
        spec = SpecScaffolder.scaffold_default()
        yaml_str = spec.to_yaml()
        self.assertIsInstance(yaml_str, str)
        self.assertIn("The AI Factory Blueprint", yaml_str)

        loaded_spec = PresentationSpec.from_yaml(yaml_str)
        self.assertEqual(loaded_spec.metadata.title, spec.metadata.title)
        self.assertEqual(len(loaded_spec.chapters), len(spec.chapters))
        self.assertEqual(loaded_spec.slide_count(), spec.slide_count())

    def test_presentation_spec_json_roundtrip(self) -> None:
        spec = SpecScaffolder.scaffold_preset("minimal")
        json_str = spec.to_json()
        self.assertIsInstance(json_str, str)

        loaded_spec = PresentationSpec.from_json(json_str)
        self.assertEqual(loaded_spec.slide_count(), spec.slide_count())

    def test_presentation_spec_file_io(self) -> None:
        spec = SpecScaffolder.scaffold_preset("minimal")
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tf:
            temp_path = Path(tf.name)

        try:
            spec.to_yaml(temp_path)
            loaded = PresentationSpec.from_yaml(temp_path)
            self.assertEqual(loaded.metadata.title, spec.metadata.title)
            self.assertEqual(loaded.slide_count(), 2)
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestSpecValidator(unittest.TestCase):
    """Tests for schema validation, text budget limits, and error diagnostics."""

    def test_sample_spec_yaml_validates_cleanly(self) -> None:
        sample_path = Path("sample_spec.yaml")
        self.assertTrue(sample_path.exists(), "sample_spec.yaml must exist")
        res = SpecValidator.validate(sample_path, strict=True)
        self.assertTrue(res.is_valid, f"sample_spec.yaml had validation errors:\n{res.summary()}")
        self.assertEqual(len(res.errors), 0)

    def test_empty_presentation_fails_validation(self) -> None:
        spec = PresentationSpec()
        res = SpecValidator.validate(spec)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("zero chapters" in e for e in res.errors))

    def test_unknown_archetype_fails_validation(self) -> None:
        slide = SlideSpec(
            archetype="non_existent_archetype",
            title="Invalid Slide",
            notes="Valid speaker notes for test slide exceeding 15 chars.",
        )
        res = SpecValidator.validate_slide(slide)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("unknown archetype" in e for e in res.errors))

    def test_speaker_notes_are_optional(self) -> None:
        # Empty notes
        slide_empty = SlideSpec(archetype="chapter_divider", title="Intro", notes="")
        res_empty = SpecValidator.validate_slide(slide_empty)
        self.assertTrue(res_empty.is_valid)
        self.assertFalse(any("notes" in w.lower() for w in res_empty.warnings))

        # Too short (< 15 chars)
        slide_short = SlideSpec(archetype="chapter_divider", title="Intro", notes="Too short")
        res_short = SpecValidator.validate_slide(slide_short)
        self.assertTrue(res_short.is_valid)
        self.assertFalse(any("notes" in w.lower() for w in res_short.warnings))

        # Valid notes
        slide_valid = SlideSpec(
            archetype="chapter_divider",
            title="Intro",
            notes="This is a valid comprehensive speaker note for presentation rehearsals.",
        )
        res_valid = SpecValidator.validate_slide(slide_valid)
        self.assertTrue(res_valid.is_valid)

    def test_slide_title_text_budget_limit(self) -> None:
        long_title = "This slide title is excessively long and significantly exceeds the sixty character budget limit"
        slide = SlideSpec(
            archetype="chapter_divider",
            title=long_title,
            notes="Valid speaker notes exceeding minimum length requirements.",
        )
        # Strict mode -> Error
        res_strict = SpecValidator.validate_slide(slide, strict=True)
        self.assertFalse(res_strict.is_valid)
        self.assertTrue(any("title exceeds 60" in e for e in res_strict.errors))

        # Non-strict mode -> Warning
        res_lenient = SpecValidator.validate_slide(slide, strict=False)
        self.assertTrue(res_lenient.is_valid)
        self.assertTrue(any("title exceeds 60" in w for w in res_lenient.warnings))

    def test_slide_subtitle_text_budget_limit(self) -> None:
        long_sub = "This subtitle is completely out of control and rambles on without any discipline or respect for slide typography and layout constraints whatsoever."
        slide = SlideSpec(
            archetype="chapter_divider",
            title="Valid Title",
            subtitle=long_sub,
            notes="Valid speaker notes exceeding minimum length requirements.",
        )
        res = SpecValidator.validate_slide(slide, strict=True)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("subtitle exceeds 120" in e for e in res.errors))

    def test_split_cards_validation(self) -> None:
        # Valid 2-card split
        valid_slide = SlideSpec(
            archetype="split_cards",
            title="Valid Split",
            cards=[
                CardSpec(title="Card 1", bullets=["Point A", "Point B"]),
                CardSpec(title="Card 2", bullets=["Point C", "Point D"]),
            ],
            notes="Valid speaker notes exceeding minimum length requirements.",
        )
        self.assertTrue(SpecValidator.validate_slide(valid_slide).is_valid)

        # Card title > 35 chars
        bad_title_slide = SlideSpec(
            archetype="split_cards",
            title="Split Test",
            cards=[
                CardSpec(title="This Card Header Is Far Too Long For A Single Pillar", bullets=["Bullet"]),
                CardSpec(title="Card 2", bullets=["Bullet"]),
            ],
            notes="Valid speaker notes exceeding minimum length requirements.",
        )
        res_bad_title = SpecValidator.validate_slide(bad_title_slide, strict=True)
        self.assertFalse(res_bad_title.is_valid)
        self.assertTrue(any("header exceeds 35" in e for e in res_bad_title.errors))

        # Bullet > 90 chars
        bad_bullet = "A" * 95
        bad_bullet_slide = SlideSpec(
            archetype="split_cards",
            title="Split Test",
            cards=[
                CardSpec(title="Card 1", bullets=[bad_bullet]),
                CardSpec(title="Card 2", bullets=["Normal bullet"]),
            ],
            notes="Valid speaker notes exceeding minimum length requirements.",
        )
        res_bad_bullet = SpecValidator.validate_slide(bad_bullet_slide, strict=True)
        self.assertFalse(res_bad_bullet.is_valid)
        self.assertTrue(any("Bullet 1 exceeds 90" in e for e in res_bad_bullet.errors))

    def test_code_terminal_validation(self) -> None:
        # Code > 16 lines
        long_code = "\n".join([f"line_{i} = {i}" for i in range(20)])
        bad_code_slide = SlideSpec(
            archetype="code_terminal",
            title="Code Test",
            terminals=[CodeBlockSpec(filename="test.py", code=long_code)],
            notes="Valid speaker notes exceeding minimum length requirements.",
        )
        res = SpecValidator.validate_slide(bad_code_slide, strict=True)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("code exceeds 16 lines" in e for e in res.errors))

    def test_hero_metrics_validation(self) -> None:
        # Stat > 12 chars
        bad_stat_slide = SlideSpec(
            archetype="hero_metrics",
            title="Metrics Test",
            metrics=[
                HeroMetricSpec(value="$123,456,789.00 USD", description="Huge number"),
                HeroMetricSpec(value="10x", description="Normal"),
            ],
            notes="Valid speaker notes exceeding minimum length requirements.",
        )
        res = SpecValidator.validate_slide(bad_stat_slide, strict=True)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("stat '$123,456,789.00 USD' exceeds 12" in e for e in res.errors))

    def test_ladder_hierarchy_validation(self) -> None:
        # < 3 steps
        too_few_steps = SlideSpec(
            archetype="ladder_hierarchy",
            title="Ladder Test",
            steps=[
                LadderStepSpec(step_number=1, title="Step 1", description="Desc"),
                LadderStepSpec(step_number=2, title="Step 2", description="Desc"),
            ],
            notes="Valid speaker notes exceeding minimum length requirements.",
        )
        res_few = SpecValidator.validate_slide(too_few_steps)
        self.assertFalse(res_few.is_valid)
        self.assertTrue(any("requires 3 to 5 steps" in e for e in res_few.errors))

        # > 5 steps
        too_many_steps = SlideSpec(
            archetype="ladder_hierarchy",
            title="Ladder Test",
            steps=[LadderStepSpec(step_number=i, title=f"Step {i}", description="Desc") for i in range(1, 7)],
            notes="Valid speaker notes exceeding minimum length requirements.",
        )
        res_many = SpecValidator.validate_slide(too_many_steps)
        self.assertFalse(res_many.is_valid)
        self.assertTrue(any("requires 3 to 5 steps" in e for e in res_many.errors))

    def test_executive_grid_validation(self) -> None:
        # != 4 quadrants
        bad_quads_slide = SlideSpec(
            archetype="executive_grid",
            title="Grid Test",
            quadrants=[
                QuadrantSpec(number="01", title="Q1", narrative="N1"),
                QuadrantSpec(number="02", title="Q2", narrative="N2"),
                QuadrantSpec(number="03", title="Q3", narrative="N3"),
            ],
            notes="Valid speaker notes exceeding minimum length requirements.",
        )
        res = SpecValidator.validate_slide(bad_quads_slide)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("requires exactly 4 quadrants" in e for e in res.errors))

    def test_dodont_checklist_validation(self) -> None:
        # Missing DO items
        missing_do = SlideSpec(
            archetype="dodont_checklist",
            title="Checklist Test",
            checklist=ChecklistSpec(dont_items=["Don't do this"], do_items=[]),
            notes="Valid speaker notes exceeding minimum length requirements.",
        )
        res = SpecValidator.validate_slide(missing_do)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("requires at least 1 DO item" in e for e in res.errors))

    def test_actionable_takeaways_validation(self) -> None:
        # Missing principles
        missing_principles = SlideSpec(
            archetype="actionable_takeaways",
            title="Takeaways Test",
            takeaway=TakeawaySpec(principles=[], roadmap_items=["Step 1"]),
            notes="Valid speaker notes exceeding minimum length requirements.",
        )
        res = SpecValidator.validate_slide(missing_principles)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("requires at least 1 action principle" in e for e in res.errors))

    def test_validation_result_methods(self) -> None:
        res1 = ValidationResult()
        self.assertTrue(bool(res1))
        self.assertIn("VALID", res1.summary())

        res1.add_error("Error 1")
        self.assertFalse(bool(res1))
        self.assertIn("INVALID", res1.summary())
        self.assertIn("Error 1", res1.summary())

        res1.add_warning("Warning 1")
        self.assertIn("Warning 1", res1.summary())

        res2 = ValidationResult()
        res2.add_error("Error 2")
        res1.merge(res2)
        self.assertEqual(len(res1.errors), 2)


class TestSpecScaffolder(unittest.TestCase):
    """Tests for SpecScaffolder preset generation and formatted YAML output."""

    def test_scaffold_all_presets_validate(self) -> None:
        presets = ["ai_factory", "executive_briefing", "product_launch", "minimal"]
        for preset in presets:
            spec = SpecScaffolder.scaffold_preset(preset)
            self.assertIsInstance(spec, PresentationSpec)
            self.assertGreater(spec.slide_count(), 0)

            # Validate each preset
            res = SpecValidator.validate(spec, strict=True)
            self.assertTrue(
                res.is_valid,
                f"Preset '{preset}' failed validation:\n{res.summary()}",
            )

    def test_scaffold_custom_parameters(self) -> None:
        spec = SpecScaffolder.scaffold(
            title="Custom AI Architecture",
            subtitle="Custom Subtitle for Enterprise Deployment",
            template_id="custom_template_123",
            target_audience="CTOs and Architects",
            preset="minimal",
        )
        self.assertEqual(spec.metadata.title, "Custom AI Architecture")
        self.assertEqual(spec.metadata.template_id, "custom_template_123")
        self.assertEqual(spec.metadata.target_audience, "CTOs and Architects")

    def test_save_to_yaml_includes_header_comments(self) -> None:
        spec = SpecScaffolder.scaffold_preset("minimal")
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as tf:
            temp_path = Path(tf.name)

        try:
            SpecScaffolder.save_to_yaml(spec, temp_path)
            content = temp_path.read_text(encoding="utf-8")
            self.assertIn("# AI FACTORY BLUEPRINT PRESENTATION SPECIFICATION", content)
            self.assertIn("Character Budgets", content)

            # Ensure it is still 100% valid YAML and parses back
            loaded = PresentationSpec.from_yaml(temp_path)
            self.assertEqual(loaded.slide_count(), 2)
            self.assertTrue(SpecValidator.validate(loaded).is_valid)
        finally:
            if temp_path.exists():
                temp_path.unlink()


class TestArchetypeEngineIntegration(unittest.TestCase):
    """Verifies that all slides in generated specs compile cleanly in ArchetypeEngine."""

    def test_compile_all_archetypes_from_sample_spec(self) -> None:
        spec = PresentationSpec.from_yaml("sample_spec.yaml")
        all_slides = spec.all_slides()
        self.assertEqual(len(all_slides), 10)

        for idx, slide in enumerate(all_slides, start=1):
            ops = ArchetypeEngine.generate_slide_ops(slide, slide_index=idx)
            self.assertIsInstance(ops, list)
            self.assertGreater(len(ops), 0)

            # Verify every operation has required target or identifier keys
            for op in ops:
                self.assertIn("op", op)
                self.assertTrue("slide" in op or "element" in op or "id" in op or "table" in op)


if __name__ == "__main__":
    unittest.main()

"""Tests for v1.1 features: TODO notes, tiers/skip, new archetypes, lints, audit, budgets."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

from preso.cli import main as cli_main
from preso.compiler.batch_generator import BatchCompiler, BatchCompilerConfig
from preso.engine import text_fit
from preso.engine.archetypes import ArchetypeEngine, generate_demo_pivot, generate_image_split
from preso.qa.audit import write_audit_checklist
from preso.spec.models import ChapterSpec, PresentationSpec, SlideSpec
from preso.spec.validator import SpecValidator


def _slide(**kw) -> SlideSpec:
    base = dict(archetype="split_cards", title="T", subtitle="A full takeaway sentence here.",
                notes="Real notes for the presenter to read.")
    base.update(kw)
    return SlideSpec.from_dict(base)


class TestTextFit(unittest.TestCase):

    def test_fit_and_excess(self) -> None:
        fit = text_fit.estimate_fit("x" * 30, box_width=648, box_height=28, font_size=22)
        self.assertFalse(fit.overflow)
        long = "word " * 40
        fit2 = text_fit.estimate_fit(long, box_width=172, box_height=26, font_size=15)
        self.assertTrue(fit2.overflow)
        self.assertGreater(text_fit.excess_chars(long, fit2), 0)


class TestNewArchetypes(unittest.TestCase):

    def test_demo_pivot_ops(self) -> None:
        ops = generate_demo_pivot("SLIDE_03_DEMO", "Watch it work", "Subtitle here",
                                  watch_for=["a", "b", "c", "d"], speaker_notes="n")
        chips = [o for o in ops if str(o.get("id", "")).startswith("CHIP_")]
        self.assertEqual(len(chips), 3)
        self.assertEqual(ops[1]["op"], "set-background")
        self.assertEqual(ops[-1]["op"], "set-notes")

    def test_image_split_url_vs_path(self) -> None:
        url_ops = generate_image_split("SLIDE_04_IMG", "T", "S", "", {"url": "https://x/y.png"}, ["b1"])
        self.assertTrue(any(o["op"] == "add-image" for o in url_ops))
        path_ops = generate_image_split("SLIDE_04_IMG", "T", "S", "", {"path": "/tmp/x.png"},
                                        image_layout="full")
        self.assertTrue(any(o["op"] == "_pending-image" for o in path_ops))
        self.assertFalse(any(str(o.get("id", "")).startswith("BODY_") for o in path_ops))

    def test_engine_aliases(self) -> None:
        ops = ArchetypeEngine.generate_slide_ops({"archetype": "demo", "title": "X", "id": "SLIDE_01_D"})
        self.assertTrue(any(o.get("id") == "TITL_S01_DEMO" for o in ops))

    def test_compiler_lifts_pending_images(self) -> None:
        res = BatchCompiler().compile_slides([
            {"archetype": "image_split", "id": "SLIDE_01_IMG", "title": "T",
             "image": {"path": "/tmp/a.png"}, "bullets": ["x"]},
        ])
        self.assertEqual(len(res.pending_images), 1)
        self.assertEqual(res.pending_images[0]["slide"], "SLIDE_01_IMG")
        self.assertFalse(any(o["op"] == "_pending-image" for o in res.operations))


class TestCompilerNotesAndTiers(unittest.TestCase):

    def test_auto_divider_has_no_notes_and_hidden_when_chapter_hidden(self) -> None:
        spec = PresentationSpec(chapters=[ChapterSpec(number=1, title="Appx", slides=[
            _slide(tier="appendix"),
        ])])
        res = BatchCompiler().compile(spec)
        notes = [o["text"] for o in res.operations if o["op"] == "set-notes"]
        self.assertFalse(any("TODO" in n for n in notes))  # nothing is invented
        self.assertEqual(len(res.skipped_slide_ids), 2)

    def test_duration_visible_tiers(self) -> None:
        slides = [_slide(tier="core").to_dict(), _slide(tier="explain").to_dict()]
        res15 = BatchCompiler(BatchCompilerConfig(visible_tiers=("core", "explain"))).compile_slides(slides)
        self.assertEqual(res15.skipped_slide_ids, [])
        res5 = BatchCompiler(BatchCompilerConfig(visible_tiers=("core",))).compile_slides(slides)
        self.assertEqual(len(res5.skipped_slide_ids), 1)


class TestValidatorLints(unittest.TestCase):

    def test_tier_roundtrip_and_unknown(self) -> None:
        s = _slide(tier="detail", skip=True)
        self.assertEqual(SlideSpec.from_dict(s.to_dict()).tier, "detail")
        self.assertTrue(SlideSpec.from_dict(s.to_dict()).skip)
        res = SpecValidator.validate_slide(_slide(tier="bogus", cards=[{"title": "a", "bullets": ["b"]}]))
        self.assertTrue(any("unknown tier" in e for e in res.errors))

    def test_subtitle_and_citation_lints(self) -> None:
        res = SpecValidator.validate_slide(_slide(subtitle="Topic label",
                                                  cards=[{"title": "a", "bullets": ["done [cite: 4]"]}]))
        self.assertTrue(any("takeaway" in w for w in res.warnings))
        self.assertTrue(any("citation artifact" in w for w in res.warnings))

    def test_layout_variety(self) -> None:
        cards = [{"title": "a", "bullets": ["b"]}, {"title": "c", "bullets": ["d"]}]
        spec = PresentationSpec(chapters=[ChapterSpec(number=1, title="C", slides=[
            _slide(title=f"S{i}", cards=cards) for i in range(4)
        ])])
        res = SpecValidator.validate(spec)
        self.assertTrue(any("consecutive 'split_cards'" in w for w in res.warnings))

    def test_geometry_pass_reports_cut(self) -> None:
        cards = [{"title": "An extremely long card title that cannot fit", "bullets": ["b"]},
                 {"title": "x", "bullets": ["y"]}, {"title": "z", "bullets": ["w"]}]
        spec = PresentationSpec(chapters=[ChapterSpec(number=1, title="C", include_divider=False,
                                                      slides=[_slide(cards=cards)])])
        res = SpecValidator.validate(spec, strict=False, geometry=True)
        self.assertTrue(any("cut ~" in w for w in res.warnings))

    def test_image_split_requires_image(self) -> None:
        res = SpecValidator.validate_slide(_slide(archetype="image_split"))
        self.assertFalse(res.is_valid)


class TestAuditAndBudgets(unittest.TestCase):

    def test_audit_checklist(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            thumb = Path(tmp) / "slide_01_abc.png"
            thumb.write_bytes(b"png")
            spec = PresentationSpec(chapters=[ChapterSpec(number=1, title="C", include_divider=False,
                                                          slides=[_slide(title="Hello", notes="")])])
            out = write_audit_checklist([thumb], Path(tmp) / "audit.md", spec=spec)
            text = out.read_text()
            self.assertIn("Hello", text)
            self.assertNotIn("notes TODO", text)
            self.assertIn("Stop after 2 fix rounds", text)

    def test_budgets_cli(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cli_main(["budgets"])
        self.assertEqual(rc, 0)
        self.assertIn("3-card title", buf.getvalue())




class TestEmptyTextboxGuard(unittest.TestCase):

    def test_hero_metric_without_unit_emits_no_empty_textbox(self) -> None:
        """Slides rejects styling an empty text box (HTTP 400), so none may be emitted."""
        res = BatchCompiler().compile_slides([{
            "archetype": "hero_metrics", "title": "Numbers", "subtitle": "A full takeaway sentence here.",
            "metrics": [{"value": "10", "label": "A"}, {"value": "20", "label": "B"}],
        }])
        empty = [o for o in res.operations
                 if o["op"] == "add-textbox" and not str(o.get("text") or "").strip()]
        self.assertEqual(empty, [])
        dropped_targets = [o for o in res.operations if str(o.get("element", "")).startswith("UNIT_")]
        self.assertEqual(dropped_targets, [])


class TestResolvedIds(unittest.TestCase):

    def test_resolved_ids_from_dict_response(self) -> None:
        """Live `execute_batch` returns a dict; local images must target the real slide ID."""
        from preso.cli import _resolved_ids
        res = {"resolved_ids": {"SLIDE_03_IMAGE_SPLIT": "slide_123_0"}}
        self.assertEqual(_resolved_ids(res), {"SLIDE_03_IMAGE_SPLIT": "slide_123_0"})
        self.assertEqual(_resolved_ids({}), {})
        self.assertEqual(_resolved_ids(None), {})


if __name__ == "__main__":
    unittest.main()

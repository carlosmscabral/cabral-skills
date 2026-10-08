"""Tests for Archetype 11: flow_diagram (native raw-batch diagrams)."""

import json
import unittest

from preso.compiler.batch_generator import BatchCompiler
from preso.engine.archetypes import ArchetypeEngine
from preso.engine.diagrams import (
    MIN_OBJECT_ID_LEN,
    RawCanvas,
    build_diagram_canvas,
    filter_requests_for,
    infer_layout,
    retarget_requests,
    u16,
    validate_diagram,
)
from preso.spec.models import PresentationSpec
from preso.spec.validator import SpecValidator

CYCLE = {
    "label": "Foundation",
    "stages": [
        {"kicker": "01 · DIAGNOSE", "title": "Reference calls", "lead": "800 calls", "body": "Signals.",
         "status": "done", "color": "red"},
        {"kicker": "02 · STRATEGY", "title": "Playbook", "lead": "Framework", "body": "Stages.",
         "status": "done", "color": "yellow"},
    ],
    "cycle": {
        "label": "03 · Continuous loop",
        "entry": {"title": "Write tests", "body": "personas"},
        "feeder": {"title": "New feature", "body": "needs tests"},
        "nodes": [{"title": "Run"}, {"title": "Analyse"}, {"title": "Adjust"}, {"title": "Re-test"}],
        "center": {"text": "each turn gets closer"},
    },
    "marker": {"text": "WE ARE HERE", "at": "entry"},
    "note": "Today: X mature · Y in progress",
}
TIMELINE = {"stages": [{"title": f"S{i}", "status": s} for i, s in enumerate(["done", "active", "next"])],
            "marker": {"text": "WE ARE HERE", "at": "stage:2"}}
FUNNEL = {"active": 2, "steps": [{"label": n, "title": n, "body": ["a", "b"]}
                                 for n in ("Welcome", "Fit", "Offer", "Close")]}


def _all(reqs, kind):
    return [r[kind] for r in reqs if kind in r]


class RawHelpersTest(unittest.TestCase):

    def test_u16_counts_surrogate_pairs(self):
        self.assertEqual(u16("abc"), 3)
        self.assertEqual(u16("✓"), 1)
        self.assertEqual(u16("📍"), 2)

    def test_object_ids_meet_minimum_length_and_are_unique(self):
        c = RawCanvas("P", "d")
        oid = c.oid("a")
        self.assertGreaterEqual(len(oid), MIN_OBJECT_ID_LEN)
        with self.assertRaises(ValueError):
            c.oid("a")

    def test_text_strips_non_bmp_and_skips_empty(self):
        c = RawCanvas("P", "dg01")
        c.box("pill", 0, 0, 100, 20, [("📍 HERE", 8, True, "#FFFFFF")])
        c.box("empty", 0, 0, 100, 20, [("", 8, True, "#FFFFFF")])
        inserts = _all(c.requests, "insertText")
        self.assertEqual([i["text"] for i in inserts], [" HERE"])
        style = _all(c.requests, "updateTextStyle")[0]
        self.assertEqual(style["textRange"]["endIndex"], u16(" HERE"))

    def test_multi_run_ranges_are_contiguous(self):
        c = RawCanvas("P", "dg01")
        c.box("card", 0, 0, 100, 80, [("Título\n", 13, True, "#202124"), ("corpo ✓", 8.5, False, "#5F6368")])
        ranges = [s["textRange"] for s in _all(c.requests, "updateTextStyle")]
        self.assertEqual(ranges[0]["startIndex"], 0)
        self.assertEqual(ranges[0]["endIndex"], ranges[1]["startIndex"])
        self.assertEqual(ranges[1]["endIndex"], u16("Título\ncorpo ✓"))

    def test_retarget_maps_pages_and_suffixes_elements(self):
        canvas = build_diagram_canvas("SLIDE_02", CYCLE, "dg02")
        out = retarget_requests(canvas.requests, {"SLIDE_02": "g123"}, "_ab")
        blob = json.dumps(out)
        self.assertNotIn('"SLIDE_02"', blob)
        create = _all(out, "createShape")[0]
        self.assertEqual(create["elementProperties"]["pageObjectId"], "g123")
        self.assertTrue(create["objectId"].endswith("_ab"))
        line = [l for l in _all(out, "updateLineProperties") if "startConnection" in l["lineProperties"]][0]
        self.assertTrue(line["lineProperties"]["startConnection"]["connectedObjectId"].endswith("_ab"))

    def test_filter_requests_for_patch(self):
        canvas = build_diagram_canvas("P", CYCLE, "dg02")
        patch = filter_requests_for(canvas.requests, {"dg02_here_pill"})
        self.assertEqual(patch[0], {"deleteObject": {"objectId": "dg02_here_pill"}})
        self.assertTrue(any("createShape" in r for r in patch))
        self.assertTrue(all(
            list(r.values())[0].get("objectId") == "dg02_here_pill" for r in patch))


class LayoutTest(unittest.TestCase):

    def test_infer_layout(self):
        self.assertEqual(infer_layout(CYCLE), "cycle")
        self.assertEqual(infer_layout(TIMELINE), "timeline")
        self.assertEqual(infer_layout(FUNNEL), "funnel")
        self.assertEqual(infer_layout({"stages": []}, "funnel"), "funnel")

    def test_cycle_has_curved_glued_connectors(self):
        reqs = build_diagram_canvas("P", CYCLE, "dg02").requests
        curved = [l for l in _all(reqs, "createLine") if l["lineCategory"] == "CURVED"]
        self.assertEqual(len(curved), 4)
        glued = [l for l in _all(reqs, "updateLineProperties") if "startConnection" in l["lineProperties"]]
        self.assertEqual(len(glued), 4)
        sites = {(g["lineProperties"]["startConnection"]["connectionSiteIndex"],
                  g["lineProperties"]["endConnection"]["connectionSiteIndex"]) for g in glued}
        self.assertEqual(sites, {(0, 1), (3, 0), (2, 3), (1, 2)})
        dashed = [u for u in _all(reqs, "updateShapeProperties")
                  if u["shapeProperties"].get("outline", {}).get("dashStyle") == "DASH"]
        self.assertEqual(len(dashed), 1)
        texts = " ".join(i["text"] for i in _all(reqs, "insertText"))
        for needle in ("WE ARE HERE", "✓ Done", "Today: X mature", "↻"):
            self.assertIn(needle, texts)

    def test_three_node_cycle(self):
        d = {"cycle": {"nodes": [{"title": "A"}, {"title": "B"}, {"title": "C"}]}}
        reqs = build_diagram_canvas("P", d, "dg02").requests
        self.assertEqual(len([l for l in _all(reqs, "createLine") if l["lineCategory"] == "CURVED"]), 3)

    def test_status_labels_override(self):
        d = dict(TIMELINE, status_labels={"done": "✓ Concluído"})
        texts = [i["text"] for i in _all(build_diagram_canvas("P", d, "dg03").requests, "insertText")]
        self.assertIn("✓ Concluído", texts)
        self.assertIn("● In progress", texts)

    def test_funnel_chevrons_and_active_highlight(self):
        reqs = build_diagram_canvas("P", FUNNEL, "dg04").requests
        kinds = [s["shapeType"] for s in _all(reqs, "createShape")]
        self.assertEqual(kinds.count("HOME_PLATE"), 1)
        self.assertEqual(kinds.count("CHEVRON"), 3)

    def test_all_elements_inside_canvas(self):
        for d in (CYCLE, TIMELINE, FUNNEL):
            for s in _all(build_diagram_canvas("P", d, "dg05").requests, "createShape"):
                ep = s["elementProperties"]
                x, y = ep["transform"]["translateX"], ep["transform"]["translateY"]
                w, h = ep["size"]["width"]["magnitude"], ep["size"]["height"]["magnitude"]
                self.assertGreaterEqual(x, 24, s["objectId"])
                self.assertLessEqual(x + w, 696, s["objectId"])
                self.assertGreaterEqual(y, 96, s["objectId"])
                self.assertLessEqual(y + h, 381, s["objectId"])


class ValidationTest(unittest.TestCase):

    def test_valid_diagrams(self):
        for d in (CYCLE, TIMELINE, FUNNEL):
            errors, _ = validate_diagram(d)
            self.assertEqual(errors, [])

    def test_structural_errors(self):
        self.assertTrue(validate_diagram({})[0])
        self.assertTrue(validate_diagram({"cycle": {"nodes": [{"title": "a"}]}})[0])
        self.assertTrue(validate_diagram({"stages": [{"title": "a"}]})[0])
        self.assertTrue(validate_diagram(dict(CYCLE, stages=CYCLE["stages"] * 2))[0])
        self.assertTrue(validate_diagram(dict(TIMELINE, marker={"text": "x", "at": "nowhere:1"}))[0])

    def test_fit_and_emoji_warnings(self):
        d = {"stages": [{"title": "A", "body": "x " * 2000}, {"title": "B 📍"}],
             "marker": {"text": "WE ARE HERE " * 10, "at": "stage:1"}}
        errors, warnings = validate_diagram(d)
        self.assertEqual(errors, [])
        joined = " | ".join(warnings)
        self.assertIn("overflows", joined)
        self.assertIn("non-BMP", joined)
        self.assertIn("will wrap", joined)


class IntegrationTest(unittest.TestCase):

    SPEC = {
        "version": "1.0",
        "metadata": {"title": "Diagrams"},
        "slides": [
            {"archetype": "cycle", "title": "Where we are", "kicker": "STATUS",
             "subtitle": "The loop turns strategy into measured improvements", "diagram": CYCLE},
            {"archetype": "flow_diagram", "title": "Funnel", "kicker": "JOURNEY",
             "subtitle": "Four steps with testable exit criteria each", "diagram": dict(FUNNEL)},
        ],
    }

    def test_engine_emits_raw_marker_and_header(self):
        ops = ArchetypeEngine.generate_slide_ops(self.SPEC["slides"][0], 2)
        names = [o["op"] for o in ops]
        self.assertEqual(names[0], "add-slide")
        self.assertIn("_raw-requests", names)
        self.assertIn("add-textbox", names)  # standard deck header

    def test_compiler_lifts_raw_requests(self):
        spec = PresentationSpec.from_dict(self.SPEC)
        result = BatchCompiler().compile(spec)
        self.assertEqual(len(result.raw_requests), 2)
        self.assertFalse(any(o.get("op") == "_raw-requests" for o in result.operations))
        for r in result.raw_requests:
            self.assertIn(r["slide"], result.slide_ids)
            self.assertTrue(r["requests"])

    def test_validator_accepts_spec(self):
        spec = PresentationSpec.from_dict(self.SPEC)
        res = SpecValidator.validate(spec)
        self.assertTrue(res.is_valid, res.errors)

    def test_validator_flags_bad_diagram(self):
        bad = {"version": "1.0", "metadata": {"title": "x"},
               "slides": [{"archetype": "timeline", "title": "t", "kicker": "K",
                           "subtitle": "a b c d e", "diagram": {"stages": [{"title": "only"}]}}]}
        res = SpecValidator.validate(PresentationSpec.from_dict(bad))
        self.assertFalse(res.is_valid)
        self.assertTrue(any("flow_diagram" in e for e in res.errors))

    def test_cli_retarget_uses_resolved_ids(self):
        from preso import cli  # pylint: disable=g-import-not-at-top
        result = BatchCompiler().compile(PresentationSpec.from_dict(self.SPEC))
        first = result.raw_requests[0]["slide"]
        flat = cli._retarget_raw_requests(result, {first: "real_slide_1"})  # pylint: disable=protected-access
        pages = {r["createShape"]["elementProperties"]["pageObjectId"] for r in flat if "createShape" in r}
        self.assertIn("real_slide_1", pages)


if __name__ == "__main__":
    unittest.main()

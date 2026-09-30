"""Unit and Integration Tests for Template Cloner & gslides Batch Compiler.

Tests:
1. GSlidesClient CLI wrapper (subprocess execution, mock runners, error handling, dry run).
2. BatchCompiler & Manifest models (SlideManifest, ChapterManifest, PresentationManifest).
3. Single-pass atomic batch payload generation across all 8 Blueprint archetypes.
4. Default template placeholder cleanup (i0, i1).
5. Deterministic ID generation and custom ID preservation.
6. Optional speaker notes pass-through (never synthesized).
7. End-to-end manifest compilation and batch execution workflow.
8. Large-scale multi-chapter batch compilation (50+ slides).
9. Strict schema compliance for all generated batch operations.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Optional
import unittest

from preso.compiler.batch_generator import (
    BatchCompiler,
    BatchCompilerConfig,
    BatchResult,
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
    GSlidesError,
    GSlidesNotFoundError,
    GSlidesTimeoutError,
)
from preso.engine.archetypes import CardSpec, MetricSpec, PrincipleSpec, StepSpec, TerminalSpec


class TestGSlidesClient(unittest.TestCase):
    """Test suite for GSlidesClient CLI wrapper and subprocess interaction."""

    def test_init_defaults(self) -> None:
        """Verifies default initialization parameters of GSlidesClient."""
        client = GSlidesClient()
        self.assertEqual(client.binary_path, DEFAULT_GSLIDES_BINARY)
        self.assertEqual(client.timeout, 120)
        self.assertFalse(client.dry_run)
        self.assertIsNone(client.runner)

    def test_init_custom_and_env(self) -> None:
        """Verifies custom binary path and environment variable resolution."""
        client = GSlidesClient(binary_path="/custom/path/gslides", timeout=60, dry_run=True)
        self.assertEqual(client.binary_path, "/custom/path/gslides")
        self.assertEqual(client.timeout, 60)
        self.assertTrue(client.dry_run)

        # Test environment variable override
        old_env = os.environ.get("GSLIDES_PATH")
        try:
            os.environ["GSLIDES_PATH"] = "/env/path/gslides"
            client_env = GSlidesClient()
            self.assertEqual(client_env.binary_path, "/env/path/gslides")
        finally:
            if old_env is not None:
                os.environ["GSLIDES_PATH"] = old_env
            else:
                os.environ.pop("GSLIDES_PATH", None)

    def test_is_binary_available(self) -> None:
        """Tests binary availability detection for existing and non-existing binaries."""
        client_mock = GSlidesClient(runner=lambda cmd, inp: subprocess.CompletedProcess(cmd, 0, "", ""))
        self.assertTrue(client_mock.is_binary_available())

        client_missing = GSlidesClient(binary_path="/nonexistent/path/to/gslides_binary_xyz")
        self.assertFalse(client_missing.is_binary_available())

    def test_copy_presentation_dry_run(self) -> None:
        """Tests copy_presentation in dry_run mode returning mock ID."""
        client = GSlidesClient(dry_run=True)
        deck_id = client.copy_presentation(template_id=DEFAULT_TEMPLATE_ID, title="AI Factory Deck")
        self.assertTrue(deck_id.startswith("mock_deck_copy_"))
        self.assertGreater(len(deck_id), 15)

    def test_create_presentation_dry_run(self) -> None:
        """Tests create_presentation in dry_run mode returning mock ID."""
        client = GSlidesClient(dry_run=True)
        deck_id = client.create_presentation(title="New Deck")
        self.assertTrue(deck_id.startswith("mock_deck_new_"))

    def test_execute_batch_dry_run(self) -> None:
        """Tests execute_batch in dry_run mode simulating ID resolution."""
        client = GSlidesClient(dry_run=True)
        ops = [
            {"op": "delete-element", "element": "i0"},
            {"op": "add-slide", "layout": "BLANK", "id": "SLIDE_01"},
            {"op": "set-background", "slide": "SLIDE_01", "color": "#1E2761"},
            {"op": "add-table", "slide": "SLIDE_01", "rows": 2, "cols": 2, "id": "TBL_01"},
            {"op": "set-notes", "slide": "SLIDE_01", "text": "Notes"},
        ]
        result = client.execute_batch(presentation_id="deck_123", operations=ops)
        self.assertEqual(result["presentation_id"], "deck_123")
        self.assertEqual(result["operations"], 5)
        self.assertTrue(result["dry_run"])
        self.assertIn("res_slide_01", result["created_slides"])
        self.assertIn("res_tbl_01", result["created_tables"])
        self.assertEqual(result["resolved_ids"]["SLIDE_01"], "res_slide_01")
        self.assertEqual(result["resolved_ids"]["TBL_01"], "res_tbl_01")

    def test_export_thumbnail_dry_run(self) -> None:
        """Tests export_thumbnail in dry_run mode creating dummy PNG artifact."""
        client = GSlidesClient(dry_run=True)
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "sub" / "slide_01.png"
            returned_path = client.export_thumbnail("deck_123", "SLIDE_01", out_file)
            self.assertEqual(returned_path, out_file)
            self.assertTrue(out_file.exists())
            self.assertGreater(out_file.stat().st_size, 0)

    def test_read_all_and_info_dry_run(self) -> None:
        """Tests read_all and info methods in dry_run mode."""
        client = GSlidesClient(dry_run=True)
        read_res = client.read_all("deck_123")
        self.assertEqual(read_res["presentation_id"], "deck_123")
        self.assertTrue(read_res["dry_run"])

        info_res = client.info("deck_123")
        self.assertEqual(info_res["presentationId"], "deck_123")
        self.assertEqual(info_res["pageSize"]["width"]["magnitude"], 720)
        self.assertEqual(info_res["pageSize"]["height"]["magnitude"], 405)

        slides_res = client.list_slides("deck_123")
        self.assertEqual(len(slides_res), 1)

        elem_res = client.list_elements("deck_123", "p")
        self.assertEqual(elem_res, [])

        del_res = client.delete_slide("deck_123", "p")
        self.assertTrue(del_res)

    def test_mock_runner_copy_presentation(self) -> None:
        """Tests copy_presentation invoking runner with correct CLI flags."""
        captured_cmds: list[list[str]] = []

        def mock_runner(cmd: list[str], inp: Optional[str]) -> subprocess.CompletedProcess[str]:
            captured_cmds.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps({"presentationId": "created_copy_deck_999"}),
                stderr="",
            )

        client = GSlidesClient(binary_path="/mock/gslides", runner=mock_runner)
        deck_id = client.copy_presentation(template_id="tmpl_abc", title="My Copied Deck")
        self.assertEqual(deck_id, "created_copy_deck_999")
        self.assertEqual(captured_cmds[0], ["/mock/gslides", "copy", "tmpl_abc", "My Copied Deck", "--json"])

    def test_mock_runner_create_presentation(self) -> None:
        """Tests create_presentation invoking runner with correct CLI flags."""
        captured_cmds: list[list[str]] = []

        def mock_runner(cmd: list[str], inp: Optional[str]) -> subprocess.CompletedProcess[str]:
            captured_cmds.append(cmd)
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps({"id": "created_new_deck_888"}),
                stderr="",
            )

        client = GSlidesClient(binary_path="/mock/gslides", runner=mock_runner)
        deck_id = client.create_presentation(title="My Fresh Deck")
        self.assertEqual(deck_id, "created_new_deck_888")
        self.assertEqual(captured_cmds[0], ["/mock/gslides", "create", "--title", "My Fresh Deck", "--json"])

    def test_mock_runner_execute_batch(self) -> None:
        """Tests execute_batch creating temporary JSON payload and parsing response."""
        captured_cmds: list[list[str]] = []
        captured_batch_json: list[dict[str, Any]] = []

        def mock_runner(cmd: list[str], inp: Optional[str]) -> subprocess.CompletedProcess[str]:
            captured_cmds.append(cmd)
            tmp_path = cmd[cmd.index("-f") + 1]
            with open(tmp_path, "r", encoding="utf-8") as f:
                captured_batch_json.extend(json.load(f))
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=json.dumps({
                    "operations": 2,
                    "api_requests": 4,
                    "created_slides": ["slide_xxx"],
                    "resolved_ids": {"SLIDE_1": "slide_xxx"},
                }),
                stderr="",
            )

        client = GSlidesClient(binary_path="/mock/gslides", runner=mock_runner)
        ops = [
            {"op": "add-slide", "layout": "BLANK", "id": "SLIDE_1"},
            {"op": "set-notes", "slide": "SLIDE_1", "text": "Notes text"},
        ]
        result = client.execute_batch("deck_real_123", ops)
        self.assertEqual(result["operations"], 2)
        self.assertEqual(result["resolved_ids"]["SLIDE_1"], "slide_xxx")
        self.assertEqual(len(captured_batch_json), 2)
        self.assertEqual(captured_batch_json[0]["op"], "add-slide")

    def test_mock_runner_export_thumbnail(self) -> None:
        """Tests export_thumbnail arguments with runner."""
        captured_cmds: list[list[str]] = []

        def mock_runner(cmd: list[str], inp: Optional[str]) -> subprocess.CompletedProcess[str]:
            captured_cmds.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="Thumbnail exported", stderr="")

        client = GSlidesClient(binary_path="/mock/gslides", runner=mock_runner)
        out_path = Path("/tmp/test_slide_thumb.png")
        client.export_thumbnail("deck_123", "slide_xyz", out_path)
        self.assertEqual(
            captured_cmds[0],
            ["/mock/gslides", "export-thumbnail", "deck_123", str(out_path.resolve()), "--slide", "slide_xyz"],
        )

    def test_error_handling_cli_error(self) -> None:
        """Tests GSlidesCLIError raised on non-zero exit code."""
        def mock_failing_runner(cmd: list[str], inp: Optional[str]) -> subprocess.CompletedProcess[str]:
            return subprocess.CompletedProcess(
                cmd,
                1,
                stdout="",
                stderr="PERMISSION_DENIED: presentation not accessible",
            )

        client = GSlidesClient(binary_path="/mock/gslides", runner=mock_failing_runner)
        with self.assertRaises(GSlidesCLIError) as ctx:
            client.info("forbidden_deck")

        self.assertEqual(ctx.exception.exit_code, 1)
        self.assertIn("PERMISSION_DENIED", ctx.exception.stderr)

    def test_error_handling_missing_binary(self) -> None:
        """Tests GSlidesNotFoundError raised when binary is nonexistent."""
        client = GSlidesClient(binary_path="/invalid/nonexistent/bin/gslides")
        with self.assertRaises(GSlidesNotFoundError):
            client._run_command(["info", "test"])

    def test_batch_execution_result_dataclass(self) -> None:
        """Tests BatchExecutionResult helper methods."""
        res = BatchExecutionResult(
            presentation_id="deck_1",
            operations_count=10,
            api_requests=5,
            created_slides=["s1", "s2"],
            resolved_ids={"SLIDE_1": "s1", "SLIDE_2": "s2"},
            dry_run=True,
        )
        d = res.to_dict()
        self.assertEqual(d["presentation_id"], "deck_1")
        self.assertEqual(d["operations"], 10)
        self.assertEqual(d["created_slides"], ["s1", "s2"])
        self.assertTrue(d["dry_run"])


class TestManifestDataModels(unittest.TestCase):
    """Test suite for Manifest data models and YAML serialization."""

    def test_slide_manifest_serialization(self) -> None:
        """Tests SlideManifest to_dict and from_dict roundtrip."""
        manifest = SlideManifest(
            archetype="split_cards",
            id="SLIDE_01",
            title="Design Principles",
            subtitle="Core architectural foundations",
            kicker="FOUNDATION",
            notes="Speaker notes for foundations.",
            cards=[
                {"title": "Card 1", "bullets": ["Item A", "Item B"]},
                {"title": "Card 2", "bullets": ["Item C", "Item D"]},
            ],
        )
        data = manifest.to_dict()
        self.assertEqual(data["archetype"], "split_cards")
        self.assertEqual(data["title"], "Design Principles")
        self.assertEqual(data["id"], "SLIDE_01")
        self.assertEqual(len(data["cards"]), 2)

        reconstructed = SlideManifest.from_dict(data)
        self.assertEqual(reconstructed.archetype, manifest.archetype)
        self.assertEqual(reconstructed.title, manifest.title)
        self.assertEqual(reconstructed.id, manifest.id)
        self.assertEqual(reconstructed.get_notes(), "Speaker notes for foundations.")

    def test_chapter_manifest_serialization(self) -> None:
        """Tests ChapterManifest serialization with nested slides."""
        chapter = ChapterManifest(
            chapter_number=1,
            title="Introduction to AI Factories",
            subtitle="The developer blueprint",
            kicker="CHAPTER 01",
            slides=[
                SlideManifest(archetype="split_cards", title="Slide A"),
                SlideManifest(archetype="hero_metrics", title="Slide B"),
            ],
            include_divider=True,
        )
        d = chapter.to_dict()
        self.assertEqual(d["chapter_number"], 1)
        self.assertEqual(len(d["slides"]), 2)

        reconstructed = ChapterManifest.from_dict(d)
        self.assertEqual(reconstructed.title, chapter.title)
        self.assertEqual(len(reconstructed.slides), 2)
        self.assertTrue(isinstance(reconstructed.slides[0], SlideManifest))

    def test_presentation_manifest_yaml_roundtrip(self) -> None:
        """Tests PresentationManifest parsing from YAML string."""
        yaml_content = """
title: "The AI Factory Blueprint"
subtitle: "A developer's playbook for the agentic era"
template_id: "1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U"
target_audience: "Staff+ Engineers & Tech Leads"
core_thesis: "Deterministic harnesses unlock reliable autonomous execution."
chapters:
  - chapter_number: 1
    title: "Context & Harness Engineering"
    subtitle: "From Vague Prompts to Verified Loops"
    slides:
      - archetype: "split_cards"
        title: "2-Tier Architecture"
        cards:
          - title: "Maker Agent"
            bullets: ["Generates implementation", "Iterates rapidly"]
          - title: "Checker Agent"
            bullets: ["Validates against specs", "Runs adversarial tests"]
      - archetype: "code_terminal"
        title: "Ratchet Verification Loop"
        terminals:
          - filename: "test_harness.py"
            code: "def test_invariants():\n    assert model.verify()"
"""
        manifest = PresentationManifest.from_yaml(yaml_content)
        self.assertEqual(manifest.title, "The AI Factory Blueprint")
        self.assertEqual(manifest.template_id, "1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U")
        self.assertEqual(len(manifest.chapters), 1)
        self.assertEqual(len(manifest.chapters[0].slides), 2)
        self.assertEqual(manifest.chapters[0].slides[0].archetype, "split_cards")
        self.assertEqual(manifest.chapters[0].slides[1].archetype, "code_terminal")

    def test_presentation_manifest_from_yaml_file(self) -> None:
        """Tests loading PresentationManifest from a YAML file on disk."""
        yaml_content = """
title: "On-Disk Manifest Deck"
target_audience: "Executive Leadership"
slides:
  - archetype: "executive_grid"
    title: "Quarterly Highlights"
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            manifest = PresentationManifest.from_yaml(temp_path)
            self.assertEqual(manifest.title, "On-Disk Manifest Deck")
            self.assertEqual(manifest.target_audience, "Executive Leadership")
            self.assertEqual(len(manifest.slides), 1)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class TestBatchCompiler(unittest.TestCase):
    """Comprehensive test suite for BatchCompiler operations and edge cases."""

    def setUp(self) -> None:
        self.compiler = BatchCompiler()

    def test_compile_single_slide_all_8_archetypes(self) -> None:
        """Tests compile_slide across all 8 Blueprint archetypes producing valid operations."""
        archetype_specs: list[dict[str, Any]] = [
            # 1. Chapter Divider
            {
                "archetype": "chapter_divider",
                "chapter_number": 1,
                "title": "Autonomous Loops",
                "subtitle": "Closing the execution feedback loop",
            },
            # 2. Split Cards
            {
                "archetype": "split_cards",
                "title": "System Decomposition",
                "subtitle": "Card layout comparison",
                "cards": [
                    {"title": "Card 1", "bullets": ["Point A", "Point B"]},
                    {"title": "Card 2", "bullets": ["Point C", "Point D"]},
                ],
            },
            # 3. Code Terminal
            {
                "archetype": "code_terminal",
                "title": "Ratchet Loop Implementation",
                "subtitle": "Test verification harness",
                "terminals": [
                    {"filename": "harness.py", "code": "def verify(): return True", "badge_text": "✓ VERIFIED"}
                ],
            },
            # 4. Hero Metrics
            {
                "archetype": "hero_metrics",
                "title": "Economics & Latency",
                "subtitle": "Stat comparison",
                "metrics": [
                    {"value": "$1.20", "unit": "per feature", "delta": "+85% efficiency", "is_hero": True},
                    {"value": "45s", "unit": "mean duration", "delta": "-90% latency"},
                ],
            },
            # 5. Ladder Hierarchy
            {
                "archetype": "ladder_hierarchy",
                "title": "Engineering Maturity",
                "subtitle": "The 4 levels of agentic readiness",
                "steps": [
                    {"number": 1, "title": "Prompt Engineering", "description": "Raw zero-shot prompt design"},
                    {"number": 2, "title": "Context Engineering", "description": "Dynamic RAG and brief construction"},
                    {"number": 3, "title": "Harness Engineering", "description": "Deterministic test verification"},
                    {"number": 4, "title": "Loop Engineering", "description": "Autonomous self-critique cycles"},
                ],
            },
            # 6. Executive Grid
            {
                "archetype": "executive_grid",
                "title": "Strategic Imperatives",
                "subtitle": "4-quadrant executive summary",
                "quadrants": [
                    {"number": 1, "title": "Speed", "description": "Rapid iteration without regression"},
                    {"number": 2, "title": "Quality", "description": "Adversarial verification loops"},
                    {"number": 3, "title": "Cost", "description": "Sub-dollar token economics"},
                    {"number": 4, "title": "Safety", "description": "Strict boundary assertions"},
                ],
            },
            # 7. Do / Don't Checklist
            {
                "archetype": "dodont_checklist",
                "title": "Prompt Architecture",
                "subtitle": "Anti-patterns vs Best practices",
                "dont_items": ["Vague directives", "Unchecked assumptions"],
                "do_items": ["Explicit acceptance criteria", "Single-pass executable scripts"],
            },
            # 8. Actionable Takeaways
            {
                "archetype": "actionable_takeaways",
                "title": "Actionable Roadmap",
                "subtitle": "Next steps for production rollout",
                "principles": [
                    {"number": 1, "title": "Ground in specs", "description": "Every prompt must cite schemas"},
                    {"number": 2, "title": "Lock tests first", "description": "Verify before generating code"},
                    {"number": 3, "title": "Automate QA", "description": "Never ship uninspected artifacts"},
                ],
                "roadmap_items": ["Milestone M1: Engine", "Milestone M2: Compiler", "Milestone M3: Ingestion"],
                "cta_text": "COMMENCE PHASE 2 →",
            },
        ]

        for idx, spec in enumerate(archetype_specs, start=1):
            ops = self.compiler.compile_slide(spec, slide_index=idx)
            self.assertIsInstance(ops, list)
            self.assertGreater(len(ops), 3, f"Archetype {spec['archetype']} emitted too few ops")

            # Check that first op is add-slide
            self.assertEqual(ops[0]["op"], "add-slide")
            self.assertIn("id", ops[0])

            # Speaker notes are optional: set-notes only when the spec authored notes
            has_notes = bool((spec.get("notes") or spec.get("speaker_notes") or "").strip())
            note_ops = [o for o in ops if o["op"] == "set-notes"]
            self.assertEqual(len(note_ops), 1 if has_notes else 0)

    def test_clean_default_placeholders(self) -> None:
        """Tests that delete-element operations for i0 and i1 are added when clean_default_placeholders is True."""
        compiler_clean = BatchCompiler(config=BatchCompilerConfig(clean_default_placeholders=True))
        result = compiler_clean.compile_slides([
            {"archetype": "split_cards", "title": "Slide 1"},
        ])

        ops = result.operations
        self.assertEqual(ops[0], {"op": "delete-element", "element": "i0"})
        self.assertEqual(ops[1], {"op": "delete-element", "element": "i1"})
        self.assertEqual(ops[2]["op"], "add-slide")

        # When clean_default_placeholders is False, no delete-element ops should precede add-slide
        compiler_no_clean = BatchCompiler(config=BatchCompilerConfig(clean_default_placeholders=False))
        result_no_clean = compiler_no_clean.compile_slides([
            {"archetype": "split_cards", "title": "Slide 1"},
        ])
        self.assertEqual(result_no_clean.operations[0]["op"], "add-slide")

    def test_multi_chapter_manifest_compilation(self) -> None:
        """Tests compiling a full multi-chapter presentation with chapter dividers."""
        manifest = PresentationManifest(
            title="Complete AI Factory Deck",
            chapters=[
                ChapterManifest(
                    chapter_number=1,
                    title="Chapter 1: The AI Revolution",
                    subtitle="Context & Framing",
                    slides=[
                        SlideManifest(
                            archetype="split_cards",
                            title="Shift 1",
                            cards=[{"title": "Card A", "bullets": ["A1"]}],
                        ),
                        SlideManifest(
                            archetype="hero_metrics",
                            title="Metrics 1",
                            metrics=[{"value": "10x", "unit": "faster"}],
                        ),
                    ],
                    include_divider=True,
                ),
                ChapterManifest(
                    chapter_number=2,
                    title="Chapter 2: Architecture & Harness",
                    subtitle="Technical Blueprint",
                    slides=[
                        SlideManifest(
                            archetype="code_terminal",
                            title="Harness Code",
                            terminals=[{"filename": "t.py", "code": "pass"}],
                        ),
                        SlideManifest(
                            archetype="ladder_hierarchy",
                            title="Maturity Ladder",
                            steps=[
                                {"number": 1, "title": "S1", "description": "D1"},
                                {"number": 2, "title": "S2", "description": "D2"},
                            ],
                        ),
                    ],
                    include_divider=True,
                ),
            ],
        )

        result = self.compiler.compile(manifest)
        # Expected slides: Chapter 1 Divider + 2 slides + Chapter 2 Divider + 2 slides = 6 slides
        self.assertEqual(result.slide_count, 6)
        self.assertEqual(result.chapter_count, 2)
        self.assertEqual(len(result.slide_ids), 6)

        # Check slide IDs follow deterministic sequence
        self.assertEqual(result.slide_ids[0], "SLIDE_01_CHAPTER_DIVIDER")
        self.assertEqual(result.slide_ids[1], "SLIDE_02_SPLIT_CARDS")
        self.assertEqual(result.slide_ids[2], "SLIDE_03_HERO_METRICS")
        self.assertEqual(result.slide_ids[3], "SLIDE_04_CHAPTER_DIVIDER")
        self.assertEqual(result.slide_ids[4], "SLIDE_05_CODE_TERMINAL")
        self.assertEqual(result.slide_ids[5], "SLIDE_06_LADDER_HIERARCHY")

        # Check archetype distribution stats
        stats = result.stats
        self.assertEqual(stats["archetypes"]["chapter_divider"], 2)
        self.assertEqual(stats["archetypes"]["split_cards"], 1)
        self.assertEqual(stats["archetypes"]["hero_metrics"], 1)
        self.assertEqual(stats["archetypes"]["code_terminal"], 1)
        self.assertEqual(stats["archetypes"]["ladder_hierarchy"], 1)

    def test_custom_slide_id_preservation(self) -> None:
        """Tests that custom slide IDs specified in the manifest are preserved."""
        slides = [
            {"archetype": "chapter_divider", "id": "CUSTOM_DIVIDER_ID", "title": "Custom Div"},
            {"archetype": "split_cards", "id": "CUSTOM_SPLIT_ID", "title": "Custom Split"},
        ]
        result = self.compiler.compile_slides(slides)
        self.assertEqual(result.slide_ids, ["CUSTOM_DIVIDER_ID", "CUSTOM_SPLIT_ID"])
        self.assertEqual(result.operations[0]["id"], "CUSTOM_DIVIDER_ID")

    def test_speaker_notes_optional_passthrough(self) -> None:
        """Tests that missing notes emit no set-notes op and authored notes are preserved."""
        slides = [
            # Slide with no notes provided
            {
                "archetype": "split_cards",
                "title": "Autonomous Execution",
                "subtitle": "Deterministic verification",
                "kicker": "EXECUTION",
                "cards": [{"title": "Maker"}, {"title": "Checker"}],
            },
            # Slide with explicit notes provided
            {
                "archetype": "hero_metrics",
                "title": "Cost Efficiency",
                "notes": "Custom speaker notes provided by author.",
                "metrics": [{"value": "$0.50", "unit": "/ run"}],
            },
        ]

        result = self.compiler.compile_slides(slides)
        note_ops = [op for op in result.operations if op.get("op") == "set-notes"]
        # Notes are optional: the note-less slide gets no set-notes op at all
        self.assertEqual(len(note_ops), 1)
        self.assertEqual(note_ops[0]["text"], "Custom speaker notes provided by author.")

    def test_tier_and_skip_emit_skip_slide_ops(self) -> None:
        """Appendix / explicit skip / non-visible tiers are built then hidden via skip-slide."""
        slides = [
            {"archetype": "split_cards", "id": "S_CORE", "title": "Core"},
            {"archetype": "split_cards", "id": "S_APPX", "title": "Appendix", "tier": "appendix"},
            {"archetype": "split_cards", "id": "S_SKIP", "title": "Skipped", "skip": True},
            {"archetype": "split_cards", "id": "S_DETAIL", "title": "Detail", "tier": "detail"},
        ]
        result = self.compiler.compile_slides(slides)
        skipped = [op["slide"] for op in result.operations if op.get("op") == "skip-slide"]
        self.assertEqual(skipped, ["S_APPX", "S_SKIP"])
        self.assertEqual(result.slide_count, 4)

        five_min = BatchCompiler(BatchCompilerConfig(visible_tiers=("core",)))
        result5 = five_min.compile_slides(slides)
        skipped5 = [op["slide"] for op in result5.operations if op.get("op") == "skip-slide"]
        self.assertEqual(skipped5, ["S_APPX", "S_SKIP", "S_DETAIL"])

    def test_batch_result_json_export(self) -> None:
        """Tests BatchResult to_json and save_json methods."""
        result = self.compiler.compile_slides([
            {"archetype": "split_cards", "title": "Test Slide"},
        ])
        json_str = result.to_json()
        data = json.loads(json_str)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "batch_payload.json"
            saved_path = result.save_json(out_file)
            self.assertEqual(saved_path, out_file)
            self.assertTrue(out_file.exists())
            with open(out_file, "r", encoding="utf-8") as f:
                disk_data = json.load(f)
            self.assertEqual(len(disk_data), len(data))

    def test_invalid_archetype_raises_value_error(self) -> None:
        """Tests that invalid archetype raises ValueError."""
        with self.assertRaises(ValueError):
            self.compiler.compile_slide({"archetype": "unsupported_weird_archetype"})

    def test_end_to_end_compiler_and_client_execution(self) -> None:
        """Tests end-to-end integration: PresentationManifest -> BatchCompiler -> GSlidesClient."""
        yaml_manifest = """
title: "End-to-End Test Deck"
chapters:
  - chapter_number: 1
    title: "Foundations"
    slides:
      - archetype: "split_cards"
        title: "2-Card Architecture"
        cards:
          - title: "Left Card"
            bullets: ["Bullet 1", "Bullet 2"]
          - title: "Right Card"
            bullets: ["Bullet 3", "Bullet 4"]
      - archetype: "actionable_takeaways"
        title: "Closing Steps"
        principles:
          - number: 1
            title: "Rule 1"
            description: "Desc 1"
"""
        manifest = PresentationManifest.from_yaml(yaml_manifest)
        compiler = BatchCompiler(config=BatchCompilerConfig(clean_default_placeholders=True))
        batch_result = compiler.compile(manifest)

        client = GSlidesClient(dry_run=True)
        deck_id = client.create_presentation("AI Factory Executive Deck")
        self.assertTrue(deck_id.startswith("mock_deck_new_"))

        exec_result = client.execute_batch(deck_id, batch_result.operations)
        self.assertEqual(exec_result["presentation_id"], deck_id)
        self.assertEqual(exec_result["operations"], len(batch_result.operations))
        self.assertEqual(len(exec_result["created_slides"]), 3)  # 1 divider + 2 slides

    def test_large_scale_batch_compilation(self) -> None:
        """Tests compiling a large 10-chapter, 40-slide presentation."""
        chapters: list[ChapterManifest] = []
        archetypes = [
            "split_cards",
            "code_terminal",
            "hero_metrics",
            "ladder_hierarchy",
            "executive_grid",
            "dodont_checklist",
            "actionable_takeaways",
        ]
        for ch_idx in range(1, 11):
            slides = [
                SlideManifest(
                    archetype=archetypes[i % len(archetypes)],
                    title=f"Chapter {ch_idx} Slide {i + 1}",
                )
                for i in range(4)
            ]
            chapters.append(
                ChapterManifest(
                    chapter_number=ch_idx,
                    title=f"Chapter {ch_idx} Architecture",
                    slides=slides,
                    include_divider=True,
                )
            )

        manifest = PresentationManifest(title="Mega Blueprint Deck", chapters=chapters)
        result = self.compiler.compile(manifest)

        # 10 chapter dividers + 10 * 4 content slides = 50 slides
        self.assertEqual(result.slide_count, 50)
        self.assertEqual(result.chapter_count, 10)
        self.assertEqual(len(result.slide_ids), 50)
        self.assertGreater(len(result.operations), 300)

    def test_strict_batch_operation_schema_compliance(self) -> None:
        """Verifies that all operations generated conform to the documented gslides schema."""
        manifest = PresentationManifest(
            chapters=[
                ChapterManifest(
                    chapter_number=1,
                    title="Design Tokens & Layouts",
                    slides=[
                        SlideManifest(archetype="split_cards", title="Split"),
                        SlideManifest(archetype="code_terminal", title="Code"),
                        SlideManifest(archetype="hero_metrics", title="Metrics"),
                        SlideManifest(archetype="ladder_hierarchy", title="Ladder"),
                        SlideManifest(archetype="executive_grid", title="Grid"),
                        SlideManifest(archetype="dodont_checklist", title="Do/Don't"),
                        SlideManifest(archetype="actionable_takeaways", title="Takeaways"),
                    ],
                )
            ]
        )
        result = self.compiler.compile(manifest, clean_default_placeholders=True)

        valid_ops = {
            "delete-element",
            "add-slide",
            "set-background",
            "add-textbox",
            "add-shape",
            "add-line",
            "add-table",
            "set-table-cell",
            "style-text",
            "style-shape",
            "set-notes",
        }

        for op in result.operations:
            op_name = op.get("op")
            self.assertIn(op_name, valid_ops, f"Unexpected op name: {op_name}")

            # Check coordinate sanity
            for coord in ("x", "y", "width", "height"):
                if coord in op:
                    val = op[coord]
                    self.assertIsInstance(val, (int, float), f"Coordinate {coord} not numeric: {val}")
                    self.assertGreaterEqual(val, 0, f"Coordinate {coord} must be >= 0: {val}")


if __name__ == "__main__":
    unittest.main()

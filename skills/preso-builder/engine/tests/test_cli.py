"""Unit and Integration Tests for preso CLI Interface and Subcommands.

Tests:
1. `preso spec`: Scaffolding of presets, custom parameters, and file output.
2. `preso build`: Compilation, dry-run simulation, batch payload generation, deck ID export, and QA integration.
3. `preso inspect`: Specification schema inspection, live deck inspection, and JSON output mode.
4. `preso ingest`: Codebase scanning, slide deck ingestion, and Markdown parsing frontends.
5. `preso preview`: Interactive HTML gallery generation with CSS mockups.
6. `preso qa`: Multimodal QA execution, console summary, JSON output, and strict mode.
7. `preso.py` executable invocation and argument parser routing.
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from preso.cli import build_parser, main
from preso.compiler.gslides_client import DEFAULT_TEMPLATE_ID, GSlidesClient
from preso.spec.models import PresentationSpec
from preso.spec.scaffolder import SpecScaffolder


class TestCLISpec(unittest.TestCase):
    """Tests for the `preso spec` subcommand."""

    def test_spec_scaffold_default(self) -> None:
        """Verifies default spec scaffolding creates a valid YAML file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "preso_spec.yaml"
            ret = main(["spec", "--output", str(out_file)])
            self.assertEqual(ret, 0)
            self.assertTrue(out_file.exists())

            spec = PresentationSpec.from_yaml(out_file)
            self.assertEqual(spec.metadata.title, "The AI Factory Blueprint")
            self.assertGreater(spec.slide_count(), 0)

    def test_spec_scaffold_preset_minimal(self) -> None:
        """Verifies spec scaffolding with minimal preset."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "minimal_spec.yaml"
            ret = main(["spec", "--preset", "minimal", "--title", "Custom Minimal", "--output", str(out_file)])
            self.assertEqual(ret, 0)
            self.assertTrue(out_file.exists())

            spec = PresentationSpec.from_yaml(out_file)
            self.assertEqual(spec.metadata.title, "Custom Minimal")
            self.assertEqual(spec.slide_count(), 2)

    def test_spec_scaffold_preset_executive_briefing(self) -> None:
        """Verifies spec scaffolding with executive_briefing preset."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "exec_spec.yaml"
            ret = main(["spec", "--preset", "executive_briefing", "--output", str(out_file)])
            self.assertEqual(ret, 0)
            self.assertTrue(out_file.exists())

            spec = PresentationSpec.from_yaml(out_file)
            self.assertGreaterEqual(spec.slide_count(), 4)


class TestCLIBuild(unittest.TestCase):
    """Tests for the `preso build` subcommand."""

    def setUp(self) -> None:
        self.tmp_dir_obj = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self.tmp_dir_obj.name)
        self.spec_file = self.tmp_dir / "sample_spec.yaml"
        spec = SpecScaffolder.scaffold_preset("minimal")
        spec.to_yaml(self.spec_file)

    def tearDown(self) -> None:
        self.tmp_dir_obj.cleanup()

    def test_build_dry_run_basic(self) -> None:
        """Verifies basic dry-run compilation and execution."""
        ret = main(["build", "--spec", str(self.spec_file), "--dry-run", "--no-qa"])
        self.assertEqual(ret, 0)

    def test_build_dry_run_with_artifacts_export(self) -> None:
        """Verifies dry-run build saves batch payload, deck ID, and QA reports."""
        batch_file = self.tmp_dir / "batch_ops.json"
        deck_id_file = self.tmp_dir / "deck_id.txt"
        report_file = self.tmp_dir / "report.md"
        preview_file = self.tmp_dir / "preview.html"

        ret = main([
            "build",
            "--spec", str(self.spec_file),
            "--dry-run",
            "--output-batch", str(batch_file),
            "--output-deck-id", str(deck_id_file),
            "--export-report", str(report_file),
            "--preview", str(preview_file),
            "--clean-placeholders",
        ])
        self.assertEqual(ret, 0)
        self.assertTrue(batch_file.exists())
        self.assertTrue(deck_id_file.exists())
        self.assertTrue(report_file.exists())
        self.assertTrue(preview_file.exists())

        # Check batch file content
        batch_data = json.loads(batch_file.read_text(encoding="utf-8"))
        self.assertIsInstance(batch_data, list)
        self.assertGreater(len(batch_data), 0)

        # Check deck ID content
        deck_id = deck_id_file.read_text(encoding="utf-8").strip()
        self.assertTrue(deck_id.startswith("mock_deck_copy_"))

    def test_build_missing_spec_returns_error(self) -> None:
        """Verifies build returns non-zero when spec file does not exist."""
        ret = main(["build", "--spec", str(self.tmp_dir / "non_existent.yaml"), "--dry-run"])
        self.assertEqual(ret, 1)

    def test_build_blank_presentation(self) -> None:
        """Verifies build --blank flag creates a blank presentation instead of copying template."""
        deck_id_file = self.tmp_dir / "blank_deck_id.txt"
        ret = main([
            "build",
            "--spec", str(self.spec_file),
            "--blank",
            "--title", "Blank Blueprint",
            "--dry-run",
            "--output-deck-id", str(deck_id_file),
            "--no-qa",
        ])
        self.assertEqual(ret, 0)
        deck_id = deck_id_file.read_text(encoding="utf-8").strip()
        self.assertTrue(deck_id.startswith("mock_deck_new_"))


class TestCLIInspect(unittest.TestCase):
    """Tests for the `preso inspect` subcommand."""

    def setUp(self) -> None:
        self.tmp_dir_obj = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self.tmp_dir_obj.name)
        self.spec_file = self.tmp_dir / "inspect_spec.yaml"
        spec = SpecScaffolder.scaffold_preset("minimal")
        spec.to_yaml(self.spec_file)

    def tearDown(self) -> None:
        self.tmp_dir_obj.cleanup()

    def test_inspect_spec_text_output(self) -> None:
        """Verifies text summary output when inspecting a spec."""
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            ret = main(["inspect", "--spec", str(self.spec_file)])
        self.assertEqual(ret, 0)
        output = stdout_capture.getvalue()
        self.assertIn("SPECIFICATION INSPECTION:", output)
        self.assertIn("Blueprint Presentation", output)
        self.assertIn("SLIDE OUTLINE:", output)

    def test_inspect_spec_json_output(self) -> None:
        """Verifies JSON output mode when inspecting a spec."""
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            ret = main(["inspect", "--spec", str(self.spec_file), "--json"])
        self.assertEqual(ret, 0)
        output = stdout_capture.getvalue().strip()
        data = json.loads(output)
        self.assertIn("metadata", data)
        self.assertIn("slides", data)
        self.assertEqual(data["slides_count"], 2)

    def test_inspect_spec_verbose_output(self) -> None:
        """Verifies verbose slide details in text output."""
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            ret = main(["inspect", "--spec", str(self.spec_file), "--verbose"])
        self.assertEqual(ret, 0)
        output = stdout_capture.getvalue()
        self.assertIn("Notes:", output)

    def test_inspect_mock_live_deck(self) -> None:
        """Verifies inspecting a live Google Slides presentation ID using mock GSlidesClient."""
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            with patch.object(
                GSlidesClient,
                "info",
                return_value={
                    "title": "Mock Production Presentation",
                    "slides": [{"objectId": "s1"}, {"objectId": "s2"}],
                },
            ):
                ret = main(["inspect", "--deck", "1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U"])
        self.assertEqual(ret, 0)
        output = stdout_capture.getvalue()
        self.assertIn("LIVE GOOGLE SLIDES DECK INSPECTION:", output)
        self.assertIn("Mock Production Presentation", output)


class TestCLIIngest(unittest.TestCase):
    """Tests for the `preso ingest` subcommand."""

    def setUp(self) -> None:
        self.tmp_dir_obj = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self.tmp_dir_obj.name)

    def tearDown(self) -> None:
        self.tmp_dir_obj.cleanup()

    def test_ingest_codebase(self) -> None:
        """Verifies `preso ingest --repo` scans repo and writes valid spec."""
        # Create small test repo structure
        repo_dir = self.tmp_dir / "test_repo"
        repo_dir.mkdir()
        (repo_dir / "README.md").write_text("# Project Titan\nAutonomous AI Factory Engine.\n")
        (repo_dir / "app.py").write_text("class TitanEngine:\n    def build(self):\n        pass\n")

        out_spec = self.tmp_dir / "ingested_repo.yaml"
        ret = main(["ingest", "--repo", str(repo_dir), "--output", str(out_spec)])
        self.assertEqual(ret, 0)
        self.assertTrue(out_spec.exists())

        spec = PresentationSpec.from_yaml(out_spec)
        self.assertIn("Titan", spec.metadata.title)
        self.assertGreater(spec.slide_count(), 0)

    def test_ingest_markdown_doc(self) -> None:
        """Verifies `preso ingest --markdown` parses Markdown document into spec."""
        md_file = self.tmp_dir / "DESIGN.md"
        md_file.write_text(
            "# Autonomous Presentation Engine\n"
            "## Architecture\n"
            "### Component Overview\n"
            "- Compiler Engine\n"
            "- Coordinate Calculator\n"
            "- Ingestion Pipeline\n"
            "### Core Ratchet Gate\n"
            "```python\n"
            "def verify_pre_commit():\n"
            "    assert tests_pass()\n"
            "```\n"
        )
        out_spec = self.tmp_dir / "ingested_md.yaml"
        ret = main(["ingest", "--markdown", str(md_file), "--output", str(out_spec)])
        self.assertEqual(ret, 0)
        self.assertTrue(out_spec.exists())

        spec = PresentationSpec.from_yaml(out_spec)
        self.assertGreater(spec.slide_count(), 0)

    def test_ingest_missing_source_returns_error(self) -> None:
        """Verifies that non-existent input sources return exit code 1."""
        ret = main(["ingest", "--repo", str(self.tmp_dir / "ghost_repo")])
        self.assertEqual(ret, 1)


class TestCLIPreviewAndQA(unittest.TestCase):
    """Tests for `preso preview` and `preso qa` subcommands."""

    def setUp(self) -> None:
        self.tmp_dir_obj = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self.tmp_dir_obj.name)
        self.spec_file = self.tmp_dir / "preview_spec.yaml"
        spec = SpecScaffolder.scaffold_preset("minimal")
        spec.to_yaml(self.spec_file)

    def tearDown(self) -> None:
        self.tmp_dir_obj.cleanup()

    def test_preview_command(self) -> None:
        """Verifies `preso preview` generates interactive HTML preview."""
        out_html = self.tmp_dir / "preview.html"
        ret = main(["preview", "--spec", str(self.spec_file), "--output", str(out_html), "--dry-run"])
        self.assertEqual(ret, 0)
        self.assertTrue(out_html.exists())
        content = out_html.read_text(encoding="utf-8")
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("The AI Factory Blueprint", content)

    def test_qa_command(self) -> None:
        """Verifies `preso qa` executes QA battery and generates report artifacts."""
        qa_out_dir = self.tmp_dir / "qa_output"
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            ret = main(["qa", "--spec", str(self.spec_file), "--output-dir", str(qa_out_dir)])
        self.assertEqual(ret, 0)
        self.assertTrue((qa_out_dir / "qa_report.md").exists())
        self.assertTrue((qa_out_dir / "preview.html").exists())
        output = stdout_capture.getvalue()
        self.assertIn("QA VERIFICATION REPORT: PASS", output)

    def test_qa_command_json_output(self) -> None:
        """Verifies `preso qa --json` outputs raw QA report JSON."""
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            ret = main(["qa", "--spec", str(self.spec_file), "--json"])
        self.assertEqual(ret, 0)
        output = stdout_capture.getvalue().strip()
        data = json.loads(output)
        self.assertIn("is_passing", data)
        self.assertTrue(data["is_passing"])
        self.assertIn("metrics", data)


class TestCLIRootShim(unittest.TestCase):
    """Tests executable shim preso.py and parser top-level routing."""

    def test_cli_help(self) -> None:
        """Verifies help output when called with --help."""
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            with self.assertRaises(SystemExit) as cm:
                main(["--help"])
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("usage: preso", stdout_capture.getvalue())

    def test_cli_no_args_shows_help(self) -> None:
        """Verifies calling preso without arguments prints help and returns 0."""
        stdout_capture = io.StringIO()
        with patch("sys.stdout", stdout_capture):
            ret = main([])
        self.assertEqual(ret, 0)
        self.assertIn("usage: preso", stdout_capture.getvalue())

    def test_executable_shim_process(self) -> None:
        """Verifies root preso.py executes cleanly as a standalone process."""
        preso_executable = Path("./preso.py").resolve()
        res = subprocess.run(
            [sys.executable, str(preso_executable), "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("preso 1.1.0", res.stdout)


if __name__ == "__main__":
    unittest.main()

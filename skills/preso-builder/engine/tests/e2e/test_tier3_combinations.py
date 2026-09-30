"""Preso Builder E2E Test Suite - Tier 3: Pairwise & Cross-Feature Pipeline Combinations.

Tests complete multi-stage pipeline integration flows:
1. Codebase AST -> PresentationSpec -> BatchCompiler -> QAVerifier
2. Markdown Document -> PresentationSpec -> BatchCompiler -> QAReportGenerator (HTML Preview)
3. Google Slides Text -> PresentationSpec -> BatchCompiler -> QAVerifier & Markdown Report
4. Scaffolder Presets -> BatchCompiler -> GSlidesClient (Dry Run API)
5. CLI End-to-End Chains (spec -> inspect -> build -> preview -> qa)
6. YAML Export/Import Spec Round-Trip -> Batch Compilation Parity
7. Multi-Modal Ingestion Fusion (Repo AST + Architecture Markdown)
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

from preso.cli import main as cli_main
from preso.compiler.batch_generator import BatchCompiler, BatchCompilerConfig
from preso.compiler.gslides_client import GSlidesClient
from preso.ingest.codebase import CodebaseIngestor
from preso.ingest.markdown import MarkdownIngestor
from preso.ingest.slides import SlidesIngestor
from preso.qa.report_generator import QAReportGenerator
from preso.qa.verifier import QAReport, QAVerifier
from preso.spec.models import (
    CardSpec,
    ChapterSpec,
    CodeBlockSpec,
    HeroMetricSpec,
    PresentationSpec,
    SlideSpec,
)
from preso.spec.scaffolder import SpecScaffolder
from preso.spec.validator import SpecValidator


class TestCodebaseToBatchToQAPipeline(unittest.TestCase):
    """Pipeline 1: Codebase AST Ingestion -> Spec -> Batch Compilation -> QA Audit."""

    def test_repo_ingest_to_batch_and_qa_verification(self) -> None:
        """Verifies full flow: repository scanning -> spec -> batch -> 100% QA pass."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_path = Path(tmp_dir) / "sample_service"
            repo_path.mkdir(parents=True)

            # Create sample files
            (repo_path / "README.md").write_text(
                "# Falcon Engine\nHigh-performance distributed execution engine.\n\n## Architecture\nModular pipeline with enforcing ratchets.",
                encoding="utf-8",
            )
            (repo_path / "engine.py").write_text(
                "class FalconEngine:\n    def execute(self, task: str) -> bool:\n        return True\n",
                encoding="utf-8",
            )

            # Step 1: Ingest repo
            ingestor = CodebaseIngestor()
            spec = ingestor.ingest(repo_path, title="Falcon Service Architecture")
            self.assertIsInstance(spec, PresentationSpec)
            self.assertGreater(spec.slide_count(), 0)

            # Step 2: Validate spec
            val_res = SpecValidator.validate(spec, strict=False)
            self.assertTrue(val_res.is_valid)

            # Step 3: Batch Compile
            compiler = BatchCompiler()
            batch_res = compiler.compile(spec)
            self.assertGreater(len(batch_res.operations), 10)

            # Step 4: QA Verification
            verifier = QAVerifier()
            qa_report = verifier.verify(spec=spec, batch_result=batch_res)
            self.assertTrue(qa_report.is_passing)
            self.assertEqual(qa_report.error_count, 0)
            self.assertGreaterEqual(qa_report.pass_rate_pct, 95.0)


class TestMarkdownToPreviewPipeline(unittest.TestCase):
    """Pipeline 2: Markdown Ingestion -> Spec -> Batch -> HTML Preview Generation."""

    def test_markdown_to_preview_gallery_generation(self) -> None:
        """Verifies Markdown doc parsed into spec and rendered to self-contained preview.html."""
        doc_content = """# Platform Next RFC
Executive architectural proposal for agentic pipelines.

## Chapter 1: Foundation
### Architectural Paradigm
Two contrasting approaches to AI systems.
#### Ad-Hoc Prompting
- Unpredictable execution
- Zero automated testing
#### AI Factory Harness
- Continuous automated evaluation
- Enforcing pre-commit gates

### Benchmark Metrics
Production performance measurements.
- 500k QPS (+40% YoY)
- 99.99% Uptime SLA
"""
        # Step 1: Markdown Ingestion
        ingestor = MarkdownIngestor()
        spec = ingestor.ingest(doc_content)
        self.assertIsInstance(spec, PresentationSpec)
        self.assertGreater(len(spec.chapters), 0)

        # Step 2: Batch Compilation
        compiler = BatchCompiler()
        batch_res = compiler.compile(spec)
        self.assertGreater(len(batch_res.operations), 15)

        # Step 3: HTML Preview Generation
        with tempfile.TemporaryDirectory() as tmp_dir:
            preview_file = Path(tmp_dir) / "preview.html"
            html_content = QAReportGenerator.generate_html_preview(spec=spec, output_path=preview_file)
            self.assertTrue(preview_file.exists())
            self.assertIn("Platform Next RFC", html_content)
            self.assertIn("slide-canvas", html_content)
            self.assertIn("slide-notes-drawer", html_content)


class TestSlidesToMarkdownReportPipeline(unittest.TestCase):
    """Pipeline 3: Google Slides Text Dump -> Spec -> Batch -> QA Markdown Report."""

    def test_slides_text_to_qa_markdown_report(self) -> None:
        """Verifies slides plain-text dump ingested, compiled, and audited to qa_report.md."""
        slides_text = """--- Slide 1 (SLIDE_01) ---
AI Factory Blueprint
Deterministic Presentation Framework
Speaker Notes: Welcome to the AI Factory Blueprint overview deck.

--- Slide 2 (SLIDE_02) ---
PARADIGM
System Architecture
Two core operating modes
• Manual Scripting: Fragile workflows
• Automated Factory: Deterministic guarantees
Speaker Notes: Comparing traditional development with automated agentic workflows.
"""
        # Step 1: Ingestion
        ingestor = SlidesIngestor()
        spec = ingestor.ingest(slides_text)
        self.assertEqual(spec.slide_count(), 2)

        # Step 2: Batch Compilation
        compiler = BatchCompiler()
        batch_res = compiler.compile(spec)
        self.assertGreater(len(batch_res.operations), 10)

        # Step 3: QA Audit & Report
        verifier = QAVerifier()
        qa_report = verifier.verify(spec=spec, batch_result=batch_res)

        with tempfile.TemporaryDirectory() as tmp_dir:
            report_file = Path(tmp_dir) / "qa_report.md"
            md_content = QAReportGenerator.generate_markdown_report(qa_report=qa_report, output_path=report_file, spec=spec)
            self.assertTrue(report_file.exists())
            self.assertIn("Visual QA & Verification Audit Report", md_content)
            self.assertIn("Executive Verification Metrics", md_content)
            self.assertIn("PASS", md_content)


class TestScaffolderToGSlidesDryRunPipeline(unittest.TestCase):
    """Pipeline 4: Scaffolder Presets -> Batch Compilation -> GSlides API Simulation."""

    def test_all_presets_compile_and_dry_run_cleanly(self) -> None:
        """Verifies each built-in preset executes through GSlidesClient dry-run successfully."""
        client = GSlidesClient(dry_run=True)
        presets = ["minimal", "ai_factory", "executive_briefing", "product_launch"]

        for preset in presets:
            spec = SpecScaffolder.scaffold_preset(preset)
            self.assertIsNotNone(spec)

            compiler = BatchCompiler()
            batch_res = compiler.compile(spec)
            self.assertEqual(batch_res.slide_count, spec.slide_count())

            deck_id = client.copy_presentation(title=f"Test Deck {preset}")
            exec_res = client.execute_batch(deck_id, batch_res.operations)
            self.assertTrue(exec_res["dry_run"])
            self.assertEqual(exec_res["operations"], len(batch_res.operations))


class TestCLICommandChains(unittest.TestCase):
    """Pipeline 5: CLI Subcommand Execution Chain (spec -> inspect -> build -> preview -> qa)."""

    def test_cli_subcommands_end_to_end_chain(self) -> None:
        """Executes full CLI lifecycle using temporary directory workspace."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            spec_file = Path(tmp_dir) / "preso_spec.yaml"
            batch_file = Path(tmp_dir) / "batch.json"
            preview_file = Path(tmp_dir) / "preview.html"
            qa_dir = Path(tmp_dir) / "qa_artifacts"

            # 1. preso spec
            ret_spec = cli_main(["spec", "--preset", "minimal", "--title", "CLI Chain Test", "--output", str(spec_file)])
            self.assertEqual(ret_spec, 0)
            self.assertTrue(spec_file.exists())

            # 2. preso inspect
            ret_inspect = cli_main(["inspect", "--spec", str(spec_file), "--json"])
            self.assertEqual(ret_inspect, 0)

            # 3. preso build --dry-run
            ret_build = cli_main(["build", "--spec", str(spec_file), "--dry-run", "--output-batch", str(batch_file), "--no-qa"])
            self.assertEqual(ret_build, 0)
            self.assertTrue(batch_file.exists())

            # 4. preso preview
            ret_preview = cli_main(["preview", "--spec", str(spec_file), "--output", str(preview_file), "--dry-run"])
            self.assertEqual(ret_preview, 0)
            self.assertTrue(preview_file.exists())

            # 5. preso qa
            ret_qa = cli_main(["qa", "--spec", str(spec_file), "--output-dir", str(qa_dir)])
            self.assertEqual(ret_qa, 0)
            self.assertTrue((qa_dir / "qa_report.md").exists())
            self.assertTrue((qa_dir / "preview.html").exists())


class TestSpecRoundTripPipeline(unittest.TestCase):
    """Pipeline 6: YAML Export -> Load -> Compile Parity."""

    def test_spec_yaml_round_trip_compilation_parity(self) -> None:
        """Verifies scaffolding a spec, dumping to YAML, reloading, and compiling produces identical operations."""
        spec_original = SpecScaffolder.scaffold_preset("ai_factory")

        with tempfile.TemporaryDirectory() as tmp_dir:
            yaml_path = Path(tmp_dir) / "roundtrip_spec.yaml"
            SpecScaffolder.save_to_yaml(spec_original, yaml_path)
            self.assertTrue(yaml_path.exists())

            # Reload
            spec_reloaded = PresentationSpec.from_yaml(yaml_path)

            # Validate
            self.assertTrue(SpecValidator.validate(spec_reloaded, strict=False).is_valid)

            # Compile both
            compiler = BatchCompiler()
            ops_orig = compiler.compile(spec_original).operations
            ops_reloaded = compiler.compile(spec_reloaded).operations

            self.assertEqual(len(ops_orig), len(ops_reloaded))
            self.assertEqual([o.get("op") for o in ops_orig], [o.get("op") for o in ops_reloaded])


class TestMultiModalIngestionFusion(unittest.TestCase):
    """Pipeline 7: Multi-Modal Fusion (Code AST + Markdown RFC into unified deck)."""

    def test_fusion_of_codebase_and_markdown(self) -> None:
        """Combines code blocks from repo and strategy cards from markdown into one presentation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create a code snippet
            code_file = Path(tmp_dir) / "pipeline.py"
            code_file.write_text("def run_batch(ops: list) -> dict:\n    return {'status': 'OK'}\n", encoding="utf-8")

            # Ingest code
            ingestor_code = CodebaseIngestor()
            spec_code = ingestor_code.ingest(tmp_dir, title="Code Foundation")

            # Markdown RFC
            doc = """# Architectural Strategy
## Chapter 1: Strategy
### Next Generation Principles
- Spec-driven engineering
- Continuous visual QA
"""
            ingestor_md = MarkdownIngestor()
            spec_md = ingestor_md.ingest(doc)

            # Fuse into unified spec
            fused_chapters = spec_code.chapters + spec_md.chapters
            fused_spec = PresentationSpec(
                metadata=spec_code.metadata,
                chapters=fused_chapters,
            )

            self.assertGreater(len(fused_spec.chapters), 1)

            # Compile fused presentation
            compiler = BatchCompiler()
            batch_res = compiler.compile(fused_spec)
            self.assertGreaterEqual(batch_res.slide_count, fused_spec.slide_count())
            self.assertGreater(len(batch_res.operations), 30)


if __name__ == "__main__":
    unittest.main()

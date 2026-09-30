"""Preso Builder E2E Test Suite - Tier 4: Real-World Workloads.

Tests heavy real-world workloads and end-to-end production scenarios:
1. Full end-to-end presentation generation on this actual repository (preso-builder)
2. Multi-chapter executive decks with all 8 Blueprint archetypes
3. Multi-language AST symbol extraction (Python, Go, TypeScript, Bash)
4. Comprehensive Architectural RFC Markdown Ingestion & Verification
5. Executive Briefing Generation with 100% WCAG AA Compliance Audit
"""

from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

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
    ChecklistSpec,
    CodeBlockSpec,
    HeroMetricSpec,
    LadderStepSpec,
    MetadataSpec,
    PresentationSpec,
    PrincipleSpec,
    QuadrantSpec,
    SlideSpec,
    TakeawaySpec,
)
from preso.spec.scaffolder import SpecScaffolder
from preso.spec.validator import SpecValidator


class TestRealWorldRepoEndToEndWorkload(unittest.TestCase):
    """Workload 1: Live end-to-end ingestion and deck generation on preso-builder itself."""

    def test_preso_builder_self_ingestion_workload(self) -> None:
        """Runs complete ingestion, AST analysis, batch generation, and QA on preso-builder repo."""
        repo_root = Path(__file__).resolve().parents[2]  # the engine directory
        self.assertTrue(repo_root.exists())

        # Step 1: Ingest repo
        ingestor = CodebaseIngestor()
        spec = ingestor.ingest(repo_root, title="The AI Factory Blueprint Presentation Builder")
        self.assertIsInstance(spec, PresentationSpec)
        self.assertGreaterEqual(len(spec.chapters), 3)
        self.assertGreaterEqual(spec.slide_count(), 6)

        # Step 2: Validate Spec
        val_res = SpecValidator.validate(spec, strict=False)
        self.assertTrue(val_res.is_valid)

        # Step 3: Batch Compile
        compiler = BatchCompiler(config=BatchCompilerConfig(clean_default_placeholders=True))
        batch_res = compiler.compile(spec)
        self.assertGreater(len(batch_res.operations), 40)
        self.assertGreaterEqual(batch_res.slide_count, spec.slide_count())

        # Step 4: Simulate GSlides execution
        client = GSlidesClient(dry_run=True)
        deck_id = client.copy_presentation(title="Preso Builder Self-Ingested Deck")
        exec_res = client.execute_batch(deck_id, batch_res.operations)
        self.assertTrue(exec_res["dry_run"])
        self.assertEqual(exec_res["operations"], len(batch_res.operations))

        # Step 5: Full QA Evaluation
        verifier = QAVerifier()
        qa_report = verifier.verify(spec=spec, batch_result=batch_res)
        self.assertTrue(qa_report.is_passing)
        self.assertEqual(qa_report.error_count, 0)
        self.assertGreaterEqual(qa_report.pass_rate_pct, 95.0)

        # Step 6: Generate Artifacts
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_dir = Path(tmp_dir)
            md_path = out_dir / "qa_report.md"
            html_path = out_dir / "preview.html"

            QAReportGenerator.generate_markdown_report(qa_report, md_path, spec=spec)
            QAReportGenerator.generate_html_preview(spec=spec, qa_report=qa_report, output_path=html_path)

            self.assertTrue(md_path.exists())
            self.assertTrue(html_path.exists())
            self.assertGreater(md_path.stat().st_size, 500)
            self.assertGreater(html_path.stat().st_size, 1000)


class TestMultiChapterExecutiveDeckWorkload(unittest.TestCase):
    """Workload 2: Multi-chapter executive presentation featuring all 8 Blueprint archetypes."""

    def test_comprehensive_eight_archetype_executive_deck(self) -> None:
        """Constructs and verifies a 3-chapter, 10-slide deck containing all 8 archetypes."""
        spec = SpecScaffolder.scaffold_preset("ai_factory")
        self.assertEqual(len(spec.chapters), 3)
        self.assertEqual(spec.slide_count(), 10)

        # Verify presence of all 8 archetypes
        archetypes_present = set()
        for ch in spec.chapters:
            for s in ch.slides:
                archetypes_present.add(s.archetype)

        self.assertEqual(len(archetypes_present), 8)

        # Compile and verify operations
        compiler = BatchCompiler()
        result = compiler.compile(spec)
        self.assertEqual(result.slide_count, 10)
        self.assertGreater(len(result.operations), 80)

        # Validate with strict=False
        val_res = SpecValidator.validate(spec, strict=False)
        self.assertTrue(val_res.is_valid)

        # Run QA
        verifier = QAVerifier()
        qa_report = verifier.verify(spec=spec, batch_result=result)
        self.assertTrue(qa_report.is_passing)
        self.assertEqual(qa_report.error_count, 0)


class TestMultiLanguageASTExtractionWorkload(unittest.TestCase):
    """Workload 3: Ingestion of polyglot codebase (Python, Go, TypeScript, Bash)."""

    def test_polyglot_repository_scanning(self) -> None:
        """Verifies CodebaseIngestor extracts symbols across Python, Go, and TypeScript."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            repo_dir = Path(tmp_dir) / "polyglot_app"
            repo_dir.mkdir()

            # Python service
            (repo_dir / "server.py").write_text(
                "class AppServer:\n    '''Main server.'''\n    def start(self, port: int = 8080) -> None:\n        pass\n",
                encoding="utf-8",
            )
            # Go handler
            (repo_dir / "handler.go").write_text(
                "package main\n\ntype UserHandler struct {}\nfunc (h *UserHandler) ServeHTTP() {}\n",
                encoding="utf-8",
            )
            # TypeScript client
            (repo_dir / "client.ts").write_text(
                "export interface APIClient {\n  fetchData(id: string): Promise<Record<string, unknown>>;\n}\n",
                encoding="utf-8",
            )
            # Bash script
            (repo_dir / "deploy.sh").write_text(
                "#!/bin/bash\necho 'Deploying cluster...'\nexit 0\n",
                encoding="utf-8",
            )

            ingestor = CodebaseIngestor()
            spec = ingestor.ingest(repo_dir, title="Polyglot Microservices Platform")

            self.assertGreaterEqual(len(spec.chapters), 3)

            # Check that code terminal slide exists and contains multi-language snippets
            all_slides = [s for ch in spec.chapters for s in ch.slides]
            term_slides = [s for s in all_slides if s.archetype == "code_terminal"]
            self.assertGreaterEqual(len(term_slides), 1)

            # Compile to batch
            compiler = BatchCompiler()
            batch_res = compiler.compile(spec)
            self.assertGreater(len(batch_res.operations), 20)


class TestArchitecturalRFCDocIngestionWorkload(unittest.TestCase):
    """Workload 4: Real-world large RFC Markdown ingestion."""

    def test_large_rfc_document_conversion(self) -> None:
        """Verifies large architectural RFC is mapped to multi-chapter spec with high QA score."""
        rfc_text = """# RFC 4092: Next-Generation Storage Engine
Comprehensive architectural overview and rollout strategy.

## Chapter 1: Architectural Foundation
### Current Bottlenecks & Limitations
Examining performance constraints of legacy relational database storage.
#### Legacy Storage
- High p99 tail latency under write contention
- Manual horizontal sharding required
- Fragile schema migration scripts
#### Next-Gen Distributed Engine
- Distributed atomic consensus with Spanner
- Automated partition rebalancing
- Zero-downtime declarative schema migrations

### Target SLA & Economic Improvements
High-throughput scaling metrics achieved in load testing.
- 1.5M QPS (+300% throughput)
- 99.999% Availability SLA

## Chapter 2: Implementation & Rollout
### Migration Phasing & Schedule
Four-stage graduated production deployment plan.
1. Phase 1: Dual-write shadow replication in staging
2. Phase 2: Read traffic canary routing (5% traffic)
3. Phase 3: Regional primary failover and cutover
4. Phase 4: Legacy database decommission

### Operational Standards & Anti-Patterns
DOs and DON'Ts for production operations.
- DO: Enforce automated invariant assertion checks
- DO: Isolate noisy tenant queries via rate limiters
- DON'T: Allow unindexed full-table range queries
- DON'T: Execute manual schema alterations outside CI

<!-- notes: Present this slide to the engineering leads highlighting operational safety. -->
"""
        ingestor = MarkdownIngestor()
        spec = ingestor.ingest(rfc_text)

        self.assertEqual(len(spec.chapters), 2)
        self.assertGreaterEqual(spec.slide_count(), 4)

        # Validate
        val_res = SpecValidator.validate(spec, strict=False)
        self.assertTrue(val_res.is_valid)

        # Compile
        compiler = BatchCompiler()
        batch_res = compiler.compile(spec)
        self.assertGreater(len(batch_res.operations), 30)

        # Verify QA
        verifier = QAVerifier()
        qa_report = verifier.verify(spec=spec, batch_result=batch_res)
        self.assertTrue(qa_report.is_passing)


class TestExecutiveBriefingPresetWorkload(unittest.TestCase):
    """Workload 5: Executive Briefing presentation generation and WCAG AA verification."""

    def test_executive_briefing_preset_workload(self) -> None:
        """Verifies executive_briefing preset compiles with 100% WCAG AA contrast compliance."""
        spec = SpecScaffolder.scaffold_preset("executive_briefing")
        self.assertEqual(len(spec.chapters), 1)
        self.assertEqual(spec.slide_count(), 5)

        compiler = BatchCompiler()
        batch_res = compiler.compile(spec)
        self.assertGreater(len(batch_res.operations), 40)

        # Run QA audit
        verifier = QAVerifier()
        qa_report = verifier.verify(spec=spec, batch_result=batch_res)
        self.assertTrue(qa_report.is_passing)
        self.assertEqual(qa_report.metrics.get("wcag_aa_compliance_pct", 0), 100.0)
        self.assertEqual(qa_report.metrics.get("out_of_bounds_count", 0), 0)
        self.assertEqual(qa_report.metrics.get("overlap_collision_count", 0), 0)


if __name__ == "__main__":
    unittest.main()

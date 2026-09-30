"""Comprehensive Unit Tests for Codebase & Repository Ingestion (Milestone M4).

Tests:
1. Directory traversal and smart filtering (.git, node_modules, __pycache__, binaries).
2. ASCII directory tree generation with depth limits and branch pruning.
3. Documentation extraction from README, ARCHITECTURE, and design files.
4. Python AST parsing for classes, dataclasses, functions, docstrings, and signatures.
5. Multi-language symbol parsing (JS, TS, Go, Rust).
6. Code snippet trimming and bounding (<= 16 lines, max line length).
7. Best practice and anti-pattern extraction.
8. Full PresentationSpec emission with 3 chapters, archetypes, and speaker notes (>= 15 words).
9. Ingestion of the live preso-builder repository.
"""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from preso.ingest.codebase import (
    CodeSymbol,
    CodebaseIngestor,
    CodebaseSummary,
    DEFAULT_IGNORED_DIRS,
    DEFAULT_IGNORED_EXTENSIONS,
)
from preso.spec.models import PresentationSpec, SlideSpec


class TestCodebaseIngestion(unittest.TestCase):
    """Test suite for CodebaseIngestor."""

    def setUp(self) -> None:
        """Create a temporary multi-file, multi-language repository fixture."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)

        # 1. Create directory structure
        (self.repo_root / "src").mkdir(parents=True)
        (self.repo_root / "src" / "engine").mkdir(parents=True)
        (self.repo_root / "src" / "models").mkdir(parents=True)
        (self.repo_root / "tests").mkdir(parents=True)
        (self.repo_root / ".git").mkdir(parents=True)
        (self.repo_root / "node_modules").mkdir(parents=True)
        (self.repo_root / "__pycache__").mkdir(parents=True)
        (self.repo_root / "dist").mkdir(parents=True)

        # 2. Create README.md with architecture details
        readme_content = """# AI Engine Core
A high-performance pipeline for deterministic model evaluation and artifact generation.

## Overview
This platform automates presentation compilation and visual verification.

### Core Architecture
- **Engine Module**: Computes exact pixel geometry and coordinates.
- **Spec Module**: Strongly typed validation and text budget enforcement.
- **Ingest Pipeline**: Multi-modal AST and document parsing.

### Best Practices
- ✓ DO: Enforce immutable dataclasses and schema validation at boundaries.
- ✓ DO: Verify 100% unit test pass rates across all modules.
- ✗ DON'T: Pass loose unvalidated dictionaries across internal interfaces.
- ✗ DON'T: Hardcode fixed canvas coordinates.
"""
        (self.repo_root / "README.md").write_text(readme_content, encoding="utf-8")

        # 3. Create Python source files
        python_models = """\"\"\"Core data models.\"\"\"
from dataclasses import dataclass
from typing import Optional

@dataclass
class LayoutBounds:
    \"\"\"Represents coordinate boundaries.\"\"\"
    x: float
    y: float
    width: float
    height: float

    def get_area(self) -> float:
        \"\"\"Calculates area.\"\"\"
        return self.width * self.height


class PipelineEngine:
    \"\"\"Executes the compilation pipeline.\"\"\"
    
    def __init__(self, name: str) -> None:
        self.name = name

    def execute_stage(self, stage_id: int, payload: dict) -> bool:
        \"\"\"Executes a stage safely.\"\"\"
        return True


def helper_function(param_a: str, param_b: int = 10) -> str:
    \"\"\"A public helper function.\"\"\"
    return f"{param_a}_{param_b}"
"""
        (self.repo_root / "src" / "models" / "models.py").write_text(python_models, encoding="utf-8")

        # 4. Create Go source file
        go_source = """package main

import "fmt"

type ServiceConfig struct {
    Port int
    Host string
}

func StartServer(cfg ServiceConfig) error {
    fmt.Println("Server running")
    return nil
}
"""
        (self.repo_root / "src" / "engine" / "server.go").write_text(go_source, encoding="utf-8")

        # 5. Create TypeScript source file
        ts_source = """export interface RenderOptions {
    theme: string;
    showGrid: boolean;
}

export class CanvasRenderer {
    render(options: RenderOptions): void {
        console.log("Rendering canvas", options);
    }
}
"""
        (self.repo_root / "src" / "engine" / "renderer.ts").write_text(ts_source, encoding="utf-8")

        # 6. Create ignored files and binaries
        (self.repo_root / ".git" / "config").write_text("dummy git", encoding="utf-8")
        (self.repo_root / "node_modules" / "package.json").write_text("dummy npm", encoding="utf-8")
        (self.repo_root / "__pycache__" / "cached.pyc").write_bytes(b"\x00\x01\x02\x03")
        (self.repo_root / "dist" / "bundle.min.js").write_text("minified bundle", encoding="utf-8")
        (self.repo_root / "src" / "asset.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    def tearDown(self) -> None:
        """Clean up temporary directory."""
        self.temp_dir.cleanup()

    def test_directory_filtering(self) -> None:
        """Verifies that VCS, caches, build artifacts, and binary files are strictly filtered."""
        ingestor = CodebaseIngestor(self.repo_root)
        summary = ingestor.scan()

        # Should find: README.md, models.py, server.go, renderer.ts
        self.assertGreaterEqual(summary.total_files, 4)
        # Verify ignored extensions and directories are excluded
        self.assertNotIn(".png", summary.extension_counts)
        self.assertNotIn(".pyc", summary.extension_counts)
        self.assertIn(".py", summary.extension_counts)
        self.assertIn(".go", summary.extension_counts)
        self.assertIn(".ts", summary.extension_counts)

    def test_directory_tree_generation(self) -> None:
        """Verifies ASCII directory tree structure and formatting."""
        ingestor = CodebaseIngestor(self.repo_root)
        tree = ingestor.generate_directory_tree(max_depth=3, max_entries_per_dir=5)

        self.assertIn(f"{self.repo_root.name}/", tree)
        self.assertIn("src/", tree)
        self.assertIn("README.md", tree)
        # Verify ignored folders do NOT appear in tree
        self.assertNotIn(".git/", tree)
        self.assertNotIn("node_modules/", tree)
        self.assertNotIn("__pycache__/", tree)

    def test_documentation_extraction(self) -> None:
        """Verifies parsing of README and extraction of titles, thesis, and best practices."""
        ingestor = CodebaseIngestor(self.repo_root)
        summary = ingestor.scan()

        self.assertIn("README.md", summary.docs)
        self.assertEqual(summary.title, "AI Engine Core")
        self.assertIn("deterministic model evaluation", summary.subtitle.lower())
        self.assertGreaterEqual(len(summary.best_practices), 1)
        self.assertGreaterEqual(len(summary.antipatterns), 1)
        self.assertTrue(any("immutable dataclasses" in do.lower() for do in summary.best_practices))
        self.assertTrue(any("loose unvalidated dictionaries" in dont.lower() for dont in summary.antipatterns))

    def test_python_ast_parsing(self) -> None:
        """Verifies AST parsing extracts classes, dataclasses, methods, and functions."""
        ingestor = CodebaseIngestor(self.repo_root)
        summary = ingestor.scan()

        symbol_names = {s.name: s for s in summary.symbols}
        self.assertIn("LayoutBounds", symbol_names)
        self.assertEqual(symbol_names["LayoutBounds"].kind, "dataclass")
        self.assertIn("get_area", symbol_names["LayoutBounds"].methods)

        self.assertIn("PipelineEngine", symbol_names)
        self.assertEqual(symbol_names["PipelineEngine"].kind, "class")
        self.assertIn("execute_stage", symbol_names["PipelineEngine"].methods)

        self.assertIn("helper_function", symbol_names)
        self.assertEqual(symbol_names["helper_function"].kind, "function")

    def test_multilanguage_symbol_parsing(self) -> None:
        """Verifies regex symbol extraction for Go and TypeScript files."""
        ingestor = CodebaseIngestor(self.repo_root)
        summary = ingestor.scan()

        symbol_names = {s.name: s for s in summary.symbols}
        self.assertIn("ServiceConfig", symbol_names)
        self.assertIn("StartServer", symbol_names)
        self.assertIn("RenderOptions", symbol_names)
        self.assertIn("CanvasRenderer", symbol_names)

    def test_code_snippet_trimming(self) -> None:
        """Verifies code snippet line limits (<= 14-16 lines) and character bounding."""
        ingestor = CodebaseIngestor(self.repo_root)
        long_code = "\n".join([f"line_{i} = 'x' * 100" for i in range(30)])
        trimmed = ingestor._trim_code_snippet(long_code, max_lines=14, max_line_len=50)

        lines = trimmed.splitlines()
        self.assertLessEqual(len(lines), 14)
        for line in lines:
            self.assertLessEqual(len(line), 50)

    def test_full_presentation_spec_generation(self) -> None:
        """Verifies complete 3-chapter PresentationSpec emission with archetypes and speaker notes."""
        ingestor = CodebaseIngestor(self.repo_root)
        spec = ingestor.ingest()

        self.assertIsInstance(spec, PresentationSpec)
        self.assertEqual(len(spec.chapters), 3)

        # Chapter 1
        ch1 = spec.chapters[0]
        self.assertEqual(ch1.number, 1)
        self.assertEqual(ch1.slides[0].archetype, "chapter_divider")
        self.assertEqual(ch1.slides[1].archetype, "split_cards")
        self.assertEqual(ch1.slides[2].archetype, "code_terminal")

        # Chapter 2
        ch2 = spec.chapters[1]
        self.assertEqual(ch2.number, 2)
        self.assertEqual(ch2.slides[0].archetype, "chapter_divider")
        self.assertEqual(ch2.slides[1].archetype, "code_terminal")
        self.assertEqual(ch2.slides[2].archetype, "ladder_hierarchy")
        self.assertEqual(ch2.slides[3].archetype, "executive_grid")

        # Chapter 3
        ch3 = spec.chapters[2]
        self.assertEqual(ch3.number, 3)
        self.assertEqual(ch3.slides[0].archetype, "chapter_divider")
        self.assertEqual(ch3.slides[1].archetype, "dodont_checklist")
        self.assertEqual(ch3.slides[2].archetype, "actionable_takeaways")

        # Speaker notes validation across ALL slides
        all_slides = [s for ch in spec.chapters for s in ch.slides]
        for idx, slide in enumerate(all_slides, start=1):
            notes = slide.notes or slide.speaker_notes
            self.assertTrue(notes, f"Slide {idx} ({slide.archetype}) missing speaker notes")
            word_count = len(notes.split())
            self.assertGreaterEqual(
                word_count,
                15,
                f"Slide {idx} ({slide.archetype}) notes has {word_count} words (< 15 words): '{notes}'",
            )

    def test_live_preso_builder_ingestion(self) -> None:
        """Tests ingestion on the actual preso-builder repository."""
        actual_repo = Path(__file__).resolve().parent.parent
        ingestor = CodebaseIngestor(actual_repo)
        spec = ingestor.ingest()

        self.assertIsInstance(spec, PresentationSpec)
        self.assertEqual(len(spec.chapters), 3)
        self.assertIn("preso", spec.metadata.title.lower().replace("-", "").replace(" ", "").replace("_", ""))
        self.assertGreaterEqual(len(spec.chapters[0].slides), 3)


if __name__ == "__main__":
    unittest.main()

"""Codebase & Local Repository Multi-Modal Ingestion Module.

Scans local repositories, filters noise/build artifacts, generates clean ASCII
directory trees, extracts architecture patterns from README/design docs, parses
AST symbols and signatures across Python and other languages, and compiles
them into an executive-ready 8-archetype PresentationSpec.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Any, Optional, Union

from preso.spec.models import (
    CardSpec,
    ChapterSpec,
    ChecklistSpec,
    CodeBlockSpec,
    HeroMetricSpec,
    LadderStepSpec,
    MetadataSpec,
    PresentationSpec,
    QuadrantSpec,
    SlideSpec,
    TakeawaySpec,
)


# Default directories to ignore during traversal
DEFAULT_IGNORED_DIRS: set[str] = {
    ".git",
    ".hg",
    ".svn",
    ".agents",
    ".idea",
    ".vscode",
    ".gemini",
    "node_modules",
    "venv",
    ".venv",
    ".env",
    "env",
    "dist",
    "build",
    "target",
    "out",
    "blaze-bin",
    "blaze-out",
    "blaze-genfiles",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".ruff_cache",
    "coverage",
    ".coverage",
    ".next",
    ".nuxt",
}

# Binary and non-source file extensions to skip
DEFAULT_IGNORED_EXTENSIONS: set[str] = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".webp",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    ".bin",
    ".exe",
    ".so",
    ".dylib",
    ".dll",
    ".wasm",
    ".pyc",
    ".pyo",
    ".pyd",
    ".class",
    ".jar",
    ".o",
    ".a",
    ".obj",
    ".mp4",
    ".mov",
    ".mp3",
    ".wav",
    ".ogg",
    ".pkl",
    ".pickle",
    ".sqlite",
    ".sqlite3",
    ".db",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".map",
    ".min.js",
    ".min.css",
}

# Maximum file size for AST / symbol scanning (500 KB)
MAX_FILE_SIZE_BYTES = 500 * 1024


@dataclass
class CodeSymbol:
    """Extracted code symbol (class, function, interface, model)."""

    name: str
    kind: str  # "class", "function", "dataclass", "interface", "struct"
    file_path: str
    signature: str
    docstring: str = ""
    methods: list[str] = field(default_factory=list)
    line_number: int = 1
    code_snippet: str = ""


@dataclass
class CodebaseSummary:
    """Summary of scanned codebase structure, metrics, and documentation."""

    root_path: Path
    name: str
    total_files: int = 0
    total_lines: int = 0
    extension_counts: dict[str, int] = field(default_factory=dict)
    primary_language: str = "Python"
    tree_text: str = ""
    docs: dict[str, str] = field(default_factory=dict)
    title: str = ""
    subtitle: str = ""
    core_thesis: str = ""
    symbols: list[CodeSymbol] = field(default_factory=list)
    key_modules: list[dict[str, Any]] = field(default_factory=list)
    best_practices: list[str] = field(default_factory=list)
    antipatterns: list[str] = field(default_factory=list)
    code_snippets: list[dict[str, Any]] = field(default_factory=list)


class CodebaseIngestor:
    """Ingests local codebases and repositories into structured Blueprint presentations.

    Capabilities:
    - Robust directory traversal with configurable filtering of VCS/build artifacts.
    - Clean ASCII tree generation with depth and branch pruning.
    - Markdown documentation & architecture extractor (README, ARCHITECTURE, SKILL, etc.).
    - AST & symbol parser for Python and regex parser for JS/TS/Go/Rust.
    - Code trimmer that bounds snippets to <= 16 lines for terminal boxes.
    - Automated mapping to the 8 AI Factory Blueprint slide archetypes.
    """

    def __init__(
        self,
        repo_path: Union[str, Path] = ".",
        ignored_dirs: Optional[set[str]] = None,
        ignored_extensions: Optional[set[str]] = None,
        max_file_size: int = MAX_FILE_SIZE_BYTES,
    ) -> None:
        self.repo_path = Path(repo_path).resolve()
        self.ignored_dirs = set(ignored_dirs) if ignored_dirs is not None else set(DEFAULT_IGNORED_DIRS)
        self.ignored_extensions = (
            set(ignored_extensions) if ignored_extensions is not None else set(DEFAULT_IGNORED_EXTENSIONS)
        )
        self.max_file_size = max_file_size

    def should_ignore_dir(self, dir_name: str) -> bool:
        """Determines if a directory name should be ignored."""
        return dir_name in self.ignored_dirs or dir_name.startswith(".")

    def should_ignore_file(self, file_path: Path) -> bool:
        """Determines if a file should be ignored based on extension or size."""
        ext = file_path.suffix.lower()
        if ext in self.ignored_extensions:
            return True
        if file_path.name.startswith("."):
            # Allow .env.example or specific configs if needed, but skip hidden metadata
            if file_path.name in (".gitignore", ".dockerignore"):
                return False
            return True
        try:
            if file_path.is_file() and file_path.stat().st_size > self.max_file_size:
                return True
        except (OSError, PermissionError):
            return True
        return False

    def scan(self) -> CodebaseSummary:
        """Performs a comprehensive scan of the codebase."""
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Codebase path does not exist: {self.repo_path}")

        repo_name = self.repo_path.name
        summary = CodebaseSummary(
            root_path=self.repo_path,
            name=repo_name if repo_name != "." else "Project",
        )

        all_files: list[Path] = []
        ext_counts: dict[str, int] = {}
        total_lines = 0

        for root, dirs, files in os.walk(self.repo_path, topdown=True):
            # Prune ignored directories in place
            dirs[:] = [d for d in dirs if not self.should_ignore_dir(d)]

            rel_root = Path(root).relative_to(self.repo_path)
            for file_name in sorted(files):
                file_path = Path(root) / file_name
                if self.should_ignore_file(file_path):
                    continue

                all_files.append(file_path)
                ext = file_path.suffix.lower() or file_name
                ext_counts[ext] = ext_counts.get(ext, 0) + 1

                # Count lines of code safely
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = len(f.readlines())
                        total_lines += lines
                except (OSError, PermissionError):
                    pass

        summary.total_files = len(all_files)
        summary.total_lines = total_lines
        summary.extension_counts = ext_counts

        # Determine primary language
        summary.primary_language = self._detect_primary_language(ext_counts)

        # Generate ASCII directory tree
        summary.tree_text = self.generate_directory_tree()

        # Extract Documentation
        summary.docs = self.extract_docs()
        self._populate_metadata_from_docs(summary)

        # Parse Source Symbols & Code Snippets
        symbols, modules, snippets = self._extract_code_symbols_and_modules(all_files)
        summary.symbols = symbols
        summary.key_modules = modules
        summary.code_snippets = snippets

        # Extract Best Practices & Anti-patterns
        best_practices, antipatterns = self.extract_best_practices_and_antipatterns(summary)
        summary.best_practices = best_practices
        summary.antipatterns = antipatterns

        return summary

    def _detect_primary_language(self, ext_counts: dict[str, int]) -> str:
        """Infers the primary programming language from file extensions."""
        lang_map = {
            ".py": "Python",
            ".ts": "TypeScript",
            ".js": "JavaScript",
            ".tsx": "TypeScript/React",
            ".jsx": "JavaScript/React",
            ".go": "Go",
            ".rs": "Rust",
            ".java": "Java",
            ".cpp": "C++",
            ".cc": "C++",
            ".c": "C",
            ".rb": "Ruby",
            ".php": "PHP",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".cs": "C#",
        }
        scored_langs: dict[str, int] = {}
        for ext, count in ext_counts.items():
            lang = lang_map.get(ext)
            if lang:
                scored_langs[lang] = scored_langs.get(lang, 0) + count

        if scored_langs:
            return max(scored_langs.items(), key=lambda x: x[1])[0]
        return "Python"

    def generate_directory_tree(
        self,
        max_depth: int = 3,
        max_entries_per_dir: int = 8,
    ) -> str:
        """Generates a clean, bounded ASCII directory tree suitable for slide presentation."""
        lines: list[str] = [f"{self.repo_path.name}/"]

        def _build_tree(current_dir: Path, prefix: str, depth: int) -> None:
            if depth > max_depth:
                return

            try:
                entries = sorted(
                    list(current_dir.iterdir()),
                    key=lambda p: (not p.is_dir(), p.name.lower()),
                )
            except (OSError, PermissionError):
                return

            # Filter entries
            filtered = []
            for entry in entries:
                if entry.is_dir():
                    if not self.should_ignore_dir(entry.name):
                        filtered.append(entry)
                else:
                    if not self.should_ignore_file(entry):
                        filtered.append(entry)

            total = len(filtered)
            display_entries = filtered[:max_entries_per_dir]
            omitted = total - len(display_entries)

            for i, entry in enumerate(display_entries):
                is_last = (i == len(display_entries) - 1) and (omitted == 0)
                connector = "└── " if is_last else "├── "
                suffix = "/" if entry.is_dir() else ""
                lines.append(f"{prefix}{connector}{entry.name}{suffix}")

                if entry.is_dir() and depth < max_depth:
                    sub_prefix = prefix + ("    " if is_last else "│   ")
                    _build_tree(entry, sub_prefix, depth + 1)

            if omitted > 0:
                lines.append(f"{prefix}└── ... ({omitted} more files/folders)")

        _build_tree(self.repo_path, "", 1)
        # Limit tree text to 16 lines for slide terminal display
        if len(lines) > 16:
            lines = lines[:15] + ["└── ... [truncated for presentation]"]
        return "\n".join(lines)

    def extract_docs(self) -> dict[str, str]:
        """Extracts text from primary architectural documentation files."""
        doc_names = [
            "README.md",
            "ARCHITECTURE.md",
            "DESIGN.md",
            "SKILL.md",
            "PROJECT.md",
            "CONTRIBUTING.md",
            "AGENTS.md",
            "docs/README.md",
            "docs/ARCHITECTURE.md",
        ]
        docs: dict[str, str] = {}
        for name in doc_names:
            doc_path = self.repo_path / name
            if doc_path.is_file():
                try:
                    with open(doc_path, "r", encoding="utf-8", errors="ignore") as f:
                        docs[name] = f.read()
                except (OSError, PermissionError):
                    pass
        return docs

    def _populate_metadata_from_docs(self, summary: CodebaseSummary) -> None:
        """Extracts title, subtitle, and core thesis from scanned markdown docs."""
        readme = summary.docs.get("README.md") or summary.docs.get("PROJECT.md") or ""

        title = ""
        subtitle = ""
        thesis = ""

        if readme:
            # Extract first top-level header # Title
            match_h1 = re.search(r"^#\s+(.+)$", readme, re.MULTILINE)
            if match_h1:
                raw_h1 = match_h1.group(1).strip()
                raw_h1 = re.sub(r"^(?:Project|Repository|Repo)[:\s]+", "", raw_h1, flags=re.IGNORECASE).strip()
                title = raw_h1

            # Extract first non-header text lines as subtitle and thesis
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", readme) if p.strip()]
            for p in paragraphs:
                lines = [l.strip() for l in p.splitlines() if l.strip()]
                # Filter out lines that are headers, html comments, code fences, badges, or lists
                non_header_lines = [
                    l for l in lines
                    if not l.startswith("#")
                    and not l.startswith("<!--")
                    and not l.startswith("```")
                    and not l.startswith(("-", "*", "+", "1.", "2.", "3."))
                ]
                if not non_header_lines:
                    continue

                clean_text = " ".join(non_header_lines)
                clean_text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", clean_text)
                clean_text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", clean_text).strip()
                if clean_text and len(clean_text) > 10:
                    if not subtitle:
                        subtitle = clean_text
                        if len(subtitle) > 120:
                            subtitle = subtitle[:117] + "..."
                    elif not thesis:
                        thesis = clean_text
                        if len(thesis) > 140:
                            thesis = thesis[:137] + "..."
                        break

        summary.title = title or summary.name.replace("-", " ").replace("_", " ").title()
        summary.subtitle = subtitle or f"Automated Architecture Blueprint for {summary.name}"
        summary.core_thesis = (
            thesis
            or f"Deterministic architectural patterns and modular interfaces powering {summary.name}."
        )

    def _extract_code_symbols_and_modules(
        self, files: list[Path]
    ) -> tuple[list[CodeSymbol], list[dict[str, Any]], list[dict[str, Any]]]:
        """Extracts classes, functions, and key module structures."""
        symbols: list[CodeSymbol] = []
        modules_map: dict[str, list[str]] = {}
        snippets: list[dict[str, Any]] = []

        # Find key source files (Python first, then other languages)
        source_files = [
            f
            for f in files
            if f.suffix.lower() in (".py", ".ts", ".js", ".go", ".rs", ".java", ".cpp")
            and not f.name.startswith("test_")
            and not f.name.endswith("_test.py")
        ]

        for file_path in source_files:
            rel_path = str(file_path.relative_to(self.repo_path))
            top_dir = rel_path.split(os.sep)[0] if os.sep in rel_path else "root"

            if file_path.suffix == ".py":
                file_symbols, snippet = self._parse_python_file(file_path, rel_path)
                symbols.extend(file_symbols)
                if snippet:
                    snippets.append(snippet)
                if top_dir not in modules_map:
                    modules_map[top_dir] = []
                for sym in file_symbols:
                    modules_map[top_dir].append(f"{sym.name} ({sym.kind})")
            else:
                file_symbols, snippet = self._parse_generic_code_file(file_path, rel_path)
                symbols.extend(file_symbols)
                if snippet:
                    snippets.append(snippet)
                if top_dir not in modules_map:
                    modules_map[top_dir] = []
                for sym in file_symbols:
                    modules_map[top_dir].append(f"{sym.name} ({sym.kind})")

        # Format key modules
        key_modules = []
        for mod_name, sym_list in modules_map.items():
            if mod_name in (".", "root"):
                mod_name = "Core Entrypoints"
            key_modules.append({
                "name": mod_name.capitalize(),
                "symbols": sym_list[:4],
                "count": len(sym_list),
            })

        return symbols, key_modules, snippets

    def _parse_python_file(
        self, file_path: Path, rel_path: str
    ) -> tuple[list[CodeSymbol], Optional[dict[str, Any]]]:
        """Parses a Python file using the ast module."""
        symbols: list[CodeSymbol] = []
        snippet_dict: Optional[dict[str, Any]] = None

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            tree = ast.parse(content, filename=str(file_path))
        except (SyntaxError, ValueError, OSError):
            return symbols, None

        raw_lines = content.splitlines()

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node) or ""
                methods = [
                    n.name
                    for n in node.body
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not n.name.startswith("_")
                ]
                kind = "class"
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "dataclass":
                        kind = "dataclass"

                # Extract concise snippet
                start_line = node.lineno - 1
                end_line = min(start_line + 14, len(raw_lines))
                class_snippet = "\n".join(raw_lines[start_line:end_line])

                sym = CodeSymbol(
                    name=node.name,
                    kind=kind,
                    file_path=rel_path,
                    signature=f"class {node.name}:",
                    docstring=doc.split("\n")[0] if doc else "",
                    methods=methods[:5],
                    line_number=node.lineno,
                    code_snippet=class_snippet,
                )
                symbols.append(sym)

                if not snippet_dict and len(raw_lines) >= 4:
                    snippet_dict = {
                        "filename": rel_path,
                        "code": self._trim_code_snippet(class_snippet, max_lines=14),
                        "language": "python",
                        "status": "do",
                        "badge_text": "✓ VERIFIED INTERFACE",
                        "title": f"Interface: {node.name}",
                    }

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                doc = ast.get_docstring(node) or ""
                args = [a.arg for a in node.args.args]
                sig = f"def {node.name}({', '.join(args[:3])}{'...' if len(args) > 3 else ''})"

                sym = CodeSymbol(
                    name=node.name,
                    kind="function",
                    file_path=rel_path,
                    signature=sig,
                    docstring=doc.split("\n")[0] if doc else "",
                    line_number=node.lineno,
                )
                symbols.append(sym)

        return symbols, snippet_dict

    def _parse_generic_code_file(
        self, file_path: Path, rel_path: str
    ) -> tuple[list[CodeSymbol], Optional[dict[str, Any]]]:
        """Parses non-Python files using regex symbol extraction."""
        symbols: list[CodeSymbol] = []
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except OSError:
            return symbols, None

        lines = content.splitlines()
        ext = file_path.suffix.lower()
        lang = "javascript" if ext in (".js", ".ts", ".tsx", ".jsx") else "go" if ext == ".go" else "rust"

        # Regex patterns for symbols
        patterns = [
            (r"(?:export\s+)?class\s+([A-Za-z0-9_]+)", "class"),
            (r"(?:export\s+)?interface\s+([A-Za-z0-9_]+)", "interface"),
            (r"type\s+([A-Za-z0-9_]+)\s+struct", "struct"),
            (r"func\s+([A-Za-z0-9_]+)\s*\(", "function"),
            (r"fn\s+([A-Za-z0-9_]+)\s*\(", "function"),
        ]

        for i, line in enumerate(lines):
            for pat, kind in patterns:
                m = re.search(pat, line)
                if m:
                    name = m.group(1)
                    sym = CodeSymbol(
                        name=name,
                        kind=kind,
                        file_path=rel_path,
                        signature=line.strip(),
                        line_number=i + 1,
                    )
                    symbols.append(sym)
                    break

        snippet_dict = None
        if lines:
            snippet_dict = {
                "filename": rel_path,
                "code": self._trim_code_snippet("\n".join(lines[:14]), max_lines=14),
                "language": lang,
                "status": "do",
                "badge_text": "✓ VERIFIED CODE",
                "title": f"Source: {Path(rel_path).name}",
            }

        return symbols, snippet_dict

    def _trim_code_snippet(self, code: str, max_lines: int = 14, max_line_len: int = 56) -> str:
        """Trims code snippet to bounded lines and character width."""
        lines = code.splitlines()
        trimmed_lines = []
        for line in lines[:max_lines]:
            if len(line) > max_line_len:
                line = line[: max_line_len - 3] + "..."
            trimmed_lines.append(line)
        return "\n".join(trimmed_lines)

    def extract_best_practices_and_antipatterns(
        self, summary: CodebaseSummary
    ) -> tuple[list[str], list[str]]:
        """Extracts or synthesizes Do's and Don'ts grounded in codebase conventions."""
        dos = [
            "Use typed data models and strict schema validation at entry boundaries.",
            "Enforce deterministic coordinate geometry to prevent visual clipping.",
            "Write comprehensive hermetic unit tests with 100% pass verification.",
            "Structure codebase into decoupled engine, spec, and ingest modules.",
        ]

        donts = [
            "Passing loose unvalidated dictionaries across internal API boundaries.",
            "Hardcoding fixed screen coordinates or ignoring container bounding boxes.",
            "Using mock facades or test shortcuts that bypass real execution paths.",
            "Creating monolithic single-file scripts without clean interfaces.",
        ]

        # Scan README / docs for direct mentions of best practices
        for doc_text in summary.docs.values():
            do_matches = re.findall(r"(?:✓|DO|Do:|Best Practice:?)\s*([^\n\.]+)", doc_text)
            dont_matches = re.findall(r"(?:✗|DON'T|Don't:|Anti-Pattern:?)\s*([^\n\.]+)", doc_text)
            if do_matches:
                dos = [m.strip()[:85] for m in do_matches[:4] if len(m.strip()) > 10] or dos
            if dont_matches:
                donts = [m.strip()[:85] for m in dont_matches[:4] if len(m.strip()) > 10] or donts

        return dos[:4], donts[:4]

    def ingest(
        self,
        repo_path: Optional[Union[str, Path]] = None,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
    ) -> PresentationSpec:
        """Ingests the codebase and generates a complete, structured PresentationSpec."""
        if repo_path:
            self.repo_path = Path(repo_path).resolve()

        summary = self.scan()
        preso_title = title or summary.title or "System Architecture Blueprint"
        preso_subtitle = subtitle or summary.subtitle or f"A Deep-Dive into {summary.name}"

        # ---------------------------------------------------------------------
        # CHAPTER 1: Overview & Directory Architecture
        # ---------------------------------------------------------------------
        ch1_slides: list[SlideSpec] = []

        # Slide 1: Chapter 1 Divider
        ch1_slides.append(
            SlideSpec(
                archetype="chapter_divider",
                title=preso_title,
                subtitle=preso_subtitle,
                kicker="CHAPTER 01",
                chapter_number=1,
                notes=(
                    f"Welcome to the architectural overview of {summary.name}. In this first chapter, "
                    f"we examine the structural foundation, directory layout, and overarching system design."
                ),
            )
        )

        # Slide 2: 2-Card Split Comparison / Architecture Pillars
        card1_bullets = [
            f"Primary Language: {summary.primary_language}",
            f"Total Source Lines: {summary.total_lines:,} LOC",
            f"Active File Count: {summary.total_files} tracked files",
        ]
        card2_bullets = [
            "Modular package separation for scalability",
            "Single-pass deterministic batch generators",
            "Comprehensive automated test verification",
        ]
        if summary.key_modules:
            mod_names = [m["name"] for m in summary.key_modules[:3]]
            card2_bullets = [f"Module: {m}" for m in mod_names]
            card2_bullets.append("Grounded schema validation & QA")

        ch1_slides.append(
            SlideSpec(
                archetype="split_cards",
                title="System Architecture & Core Dimensions",
                subtitle="High-level metrics and architectural component breakdown",
                kicker="FOUNDATION",
                cards=[
                    CardSpec(
                        title="Codebase Dimensions",
                        kicker="METRICS",
                        bullets=card1_bullets,
                        theme="#1A73E8",
                    ),
                    CardSpec(
                        title="Architectural Modules",
                        kicker="COMPONENTS",
                        bullets=card2_bullets,
                        theme="#1E8E3E",
                    ),
                ],
                notes=(
                    f"This slide provides an executive summary of {summary.name}. On the left are key codebase "
                    f"dimensions totaling {summary.total_lines:,} lines of code. On the right are the primary modules."
                ),
            )
        )

        # Slide 3: Code Terminal with Directory Tree
        tree_snippet = summary.tree_text or self.generate_directory_tree()
        ch1_slides.append(
            SlideSpec(
                archetype="code_terminal",
                title="Directory Hierarchy & Layout",
                subtitle="Clean structural organization of source packages and test suites",
                kicker="REPOSITORY TREE",
                terminals=[
                    CodeBlockSpec(
                        filename=f"{summary.name}/",
                        code=tree_snippet,
                        language="bash",
                        status="do",
                        badge_text="✓ CLEAN TREE",
                    )
                ],
                notes=(
                    f"Here is the directory tree for {summary.name}. Notice the clean hierarchy separating core "
                    f"models, coordinate math, and multi-modal ingestion modules from extraneous build artifacts."
                ),
            )
        )

        chapter1 = ChapterSpec(
            number=1,
            title="Foundation & Architecture",
            subtitle=preso_subtitle,
            slides=ch1_slides,
            notes="Chapter 1 establishes the codebase structure and high-level architectural metrics.",
        )

        # ---------------------------------------------------------------------
        # CHAPTER 2: Core Interfaces & Implementation Flow
        # ---------------------------------------------------------------------
        ch2_slides: list[SlideSpec] = []

        # Slide 4: Chapter 2 Divider
        ch2_slides.append(
            SlideSpec(
                archetype="chapter_divider",
                title="Core Interfaces & Data Contracts",
                subtitle="Examining data pipelines, symbols, and runtime models",
                kicker="CHAPTER 02",
                chapter_number=2,
                notes=(
                    "In Chapter 2, we delve into the core interfaces, typing models, and execution "
                    "pipelines that drive deterministic processing across the codebase."
                ),
            )
        )

        # Slide 5: Representative Code Terminal
        sample_code = (
            summary.code_snippets[0]["code"]
            if summary.code_snippets
            else (
                "class PresentationEngine:\n"
                "    def __init__(self, spec: PresentationSpec) -> None:\n"
                "        self.spec = spec\n\n"
                "    def compile_batch(self) -> list[dict]:\n"
                "        return ArchetypeEngine.generate(self.spec)"
            )
        )
        sample_filename = (
            summary.code_snippets[0]["filename"] if summary.code_snippets else "preso/engine.py"
        )
        ch2_slides.append(
            SlideSpec(
                archetype="code_terminal",
                title="Core Data Contract Implementation",
                subtitle="Verified class definitions and method signatures extracted via AST",
                kicker="TYPED INTERFACE",
                terminals=[
                    CodeBlockSpec(
                        filename=sample_filename,
                        code=sample_code,
                        language="python",
                        status="do",
                        badge_text="✓ IMMUTABLE MODEL",
                    )
                ],
                notes=(
                    "This slide showcases a representative typed interface from the codebase. By enforcing "
                    "strict data models and pure functions, we eliminate implicit bugs and runtime regressions."
                ),
            )
        )

        # Slide 6: Ladder Hierarchy Pipeline
        ch2_slides.append(
            SlideSpec(
                archetype="ladder_hierarchy",
                title="Execution Pipeline Flow",
                subtitle="Four deterministic stages transforming source inputs into slides",
                kicker="PIPELINE",
                steps=[
                    LadderStepSpec(
                        step_number=1,
                        title="Multi-Modal Ingestion",
                        description="Scan repositories, existing decks, and markdown into uniform models.",
                    ),
                    LadderStepSpec(
                        step_number=2,
                        title="Spec Validation",
                        description="Enforce schema types, character budgets, and speaker note mandates.",
                    ),
                    LadderStepSpec(
                        step_number=3,
                        title="Coordinate Generation",
                        description="Calculate exact bounding boxes and colors across 8 archetypes.",
                    ),
                    LadderStepSpec(
                        step_number=4,
                        title="Batch Compilation",
                        description="Emit atomic single-pass gslides batch operations for rendering.",
                    ),
                ],
                notes=(
                    "Our processing pipeline operates in 4 sequential stages: Ingestion, Validation, "
                    "Coordinate Generation, and Batch Compilation. Each stage enforces hermetic invariants."
                ),
            )
        )

        # Slide 7: Executive 2x2 Grid
        ch2_slides.append(
            SlideSpec(
                archetype="executive_grid",
                title="Architectural Pillars in One Line Each",
                subtitle="Executive summary of modular system boundaries",
                kicker="ARCHITECTURE",
                quadrants=[
                    QuadrantSpec(
                        number="01",
                        title="Ingest Engine",
                        narrative="Extracts structure and AST symbols from repos and markdown.",
                    ),
                    QuadrantSpec(
                        number="02",
                        title="Spec Validator",
                        narrative="Guarantees zero text overflow and strict character limits.",
                    ),
                    QuadrantSpec(
                        number="03",
                        title="Archetype Math",
                        narrative="Calculates 16:9 canvas coordinates with WCAG AA compliance.",
                    ),
                    QuadrantSpec(
                        number="04",
                        title="GSlides Batch",
                        narrative="Generates single-pass atomic JSON payloads with placeholder IDs.",
                    ),
                ],
                notes=(
                    "This 2x2 grid summarizes the four architectural pillars of the system. "
                    "Each quadrant operates independently with clear contract boundaries."
                ),
            )
        )

        chapter2 = ChapterSpec(
            number=2,
            title="Core Interfaces & Pipeline Flow",
            subtitle="Deep dive into symbols, models, and data contracts",
            slides=ch2_slides,
            notes="Chapter 2 covers interface contracts, pipeline steps, and quadrant summaries.",
        )

        # ---------------------------------------------------------------------
        # CHAPTER 3: Engineering Standards & Execution
        # ---------------------------------------------------------------------
        ch3_slides: list[SlideSpec] = []

        # Slide 8: Chapter 3 Divider
        ch3_slides.append(
            SlideSpec(
                archetype="chapter_divider",
                title="Engineering Standards & Roadmap",
                subtitle="Best practices, anti-patterns, and actionable takeaways",
                kicker="CHAPTER 03",
                chapter_number=3,
                notes=(
                    "In our final chapter, we review the engineering standards, Do and Don't best "
                    "practices, and actionable roadmap for production deployment."
                ),
            )
        )

        # Slide 9: Do / Don't Checklist
        ch3_slides.append(
            SlideSpec(
                archetype="dodont_checklist",
                title="Engineering Practices: Do's and Don'ts",
                subtitle="Blueprint standards vs common anti-patterns in system design",
                kicker="STANDARDS",
                checklist=ChecklistSpec(
                    do_items=summary.best_practices,
                    dont_items=summary.antipatterns,
                    do_title="BLUEPRINT STANDARD (DO)",
                    dont_title="COMMON TRAPS (DON'T)",
                    takeaway="Engineering discipline compounds across every automated iteration.",
                ),
                notes=(
                    "Here we compare recommended engineering standards against common anti-patterns. "
                    "Following these guidelines ensures predictable performance and maintainability."
                ),
            )
        )

        # Slide 10: Actionable Takeaways & Next Steps
        ch3_slides.append(
            SlideSpec(
                archetype="actionable_takeaways",
                title="Actionable Takeaways & Next Steps",
                subtitle="Core principles and milestone delivery roadmap",
                kicker="NEXT STEPS",
                takeaway=TakeawaySpec(
                    thesis="Automate presentation generation with deterministic engineering standards.",
                    principles=[
                        "Enforce strict schema validation before compilation.",
                        "Ground visual elements in WCAG AA compliant palettes.",
                        "Verify 100% unit test pass rates across all modules.",
                    ],
                    roadmap_title="DEPLOYMENT ROADMAP",
                    roadmap_items=[
                        "Phase 1: Ingest repository AST & specs",
                        "Phase 2: Compile atomic gslides batch payload",
                        "Phase 3: Automated visual QA and gallery export",
                    ],
                    cta_text="GENERATE SLIDES NOW →",
                    contact_info="go/preso-builder · feedback@google.com",
                ),
                notes=(
                    "To conclude, our three core principles focus on validation, design compliance, "
                    "and automated verification. Follow the 3-phase roadmap to build executive decks."
                ),
            )
        )

        chapter3 = ChapterSpec(
            number=3,
            title="Standards & Roadmap",
            subtitle="Best practices and deployment roadmap",
            slides=ch3_slides,
            notes="Chapter 3 details best practice checklists and the deployment roadmap.",
        )

        # Build complete PresentationSpec
        metadata = MetadataSpec(
            title=preso_title,
            subtitle=preso_subtitle,
            target_audience="Executive Leadership & Senior Staff Engineers",
            core_thesis=summary.core_thesis,
            template_id="1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U",
        )

        return PresentationSpec(
            metadata=metadata,
            chapters=[chapter1, chapter2, chapter3],
        )

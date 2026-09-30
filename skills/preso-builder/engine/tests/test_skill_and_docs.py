"""Documentation tests: the parent SKILL.md frontmatter and the engine README."""

from __future__ import annotations

from pathlib import Path
import unittest

import yaml

ENGINE_ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ENGINE_ROOT.parent / "SKILL.md"
README_PATH = ENGINE_ROOT / "README.md"

ARCHETYPES = [
    "chapter_divider",
    "split_cards",
    "code_terminal",
    "hero_metrics",
    "ladder_hierarchy",
    "executive_grid",
    "dodont_checklist",
    "actionable_takeaways",
]


class TestSkillAndDocs(unittest.TestCase):
    """The engine ships inside the preso-builder skill; keep its docs coherent."""

    def test_skill_frontmatter_valid(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---"))
        frontmatter = yaml.safe_load(content.split("---", 2)[1])
        self.assertEqual(frontmatter["name"], "preso-builder")
        self.assertGreater(len(frontmatter["description"]), 50)

    def test_readme_sections(self) -> None:
        content = README_PATH.read_text(encoding="utf-8")
        for section in [
            "Architecture Flow",
            "Key Features",
            "The 10 Blueprint Slide Archetypes",
            "Design Tokens & Visual Standards",
            "Installation & Prerequisites",
            "Quickstart & CLI Reference",
            "Running the Test Suite",
            "Agent Skill Integration",
        ]:
            self.assertIn(section, content, f"README.md must contain section '{section}'")

    def test_readme_includes_cli_and_archetypes(self) -> None:
        content = README_PATH.read_text(encoding="utf-8")
        for cmd in ["preso.py spec", "preso.py ingest", "preso.py build", "preso.py preview", "preso.py qa"]:
            self.assertIn(cmd, content)
        for arc in ARCHETYPES:
            self.assertIn(arc, content)


if __name__ == "__main__":
    unittest.main()

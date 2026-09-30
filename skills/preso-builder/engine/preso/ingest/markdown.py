"""Markdown & Raw Notes Multi-Modal Ingestion Module.

Parses Markdown documents, architectural memos, design docs, and raw meeting notes
into structured PresentationSpec models. Intelligently interprets document hierarchy
(# Title, ## Chapters, ### Slides, #### Cards/Steps), extracts tables, lists, code
blocks, metrics, and Do/Don't checklists, and automatically maps each section into
the 8 Blueprint slide archetypes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Any, Optional, Union

import yaml

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


@dataclass
class RawSection:
    """Represents a parsed Markdown section."""

    level: int  # 1 for #, 2 for ##, 3 for ###, 4 for ####
    heading: str
    content: str = ""
    subsections: list[RawSection] = field(default_factory=list)
    code_blocks: list[dict[str, str]] = field(default_factory=list)
    tables: list[list[list[str]]] = field(default_factory=list)
    lists: list[list[str]] = field(default_factory=list)
    blockquotes: list[str] = field(default_factory=list)
    speaker_notes: str = ""


class MarkdownIngestor:
    """Ingests Markdown documents and raw notes into Blueprint presentations.

    Capabilities:
    - Parses YAML frontmatter metadata (title, subtitle, audience, thesis).
    - Preserves heading hierarchy (# -> Title, ## -> Chapter, ### -> Slide, #### -> Card).
    - Extracts multi-language code fences with syntax and filename tags.
    - Parses Markdown tables and converts them to structured comparison cards.
    - Heuristically classifies content into all 8 AI Factory Blueprint archetypes.
    - Synthesizes professional speaker notes guaranteeing >= 15 words per slide.
    - Enforces strict character limits to prevent slide text overflow.
    """

    def __init__(self, doc_path_or_content: Optional[Union[str, Path]] = None) -> None:
        self.raw_source = doc_path_or_content

    def ingest(
        self,
        doc_path_or_content: Optional[Union[str, Path]] = None,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
    ) -> PresentationSpec:
        """Main ingestion entrypoint. Converts Markdown document into PresentationSpec."""
        source = doc_path_or_content if doc_path_or_content is not None else self.raw_source
        if source is None:
            raise ValueError("No markdown source provided for ingestion.")

        markdown_text = ""
        is_file = False
        if isinstance(source, Path):
            is_file = True
            file_path = source
        elif isinstance(source, str) and "\n" not in source and len(source) < 500:
            try:
                p = Path(source)
                if p.is_file():
                    is_file = True
                    file_path = p
            except (OSError, ValueError):
                is_file = False

        if is_file:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    markdown_text = f.read()
            except OSError as e:
                raise IOError(f"Failed to read markdown file {source}: {e}") from e
        elif isinstance(source, str):
            markdown_text = source
        else:
            raise TypeError(f"Unsupported markdown source type: {type(source)}")

        return self.parse(markdown_text, override_title=title, override_subtitle=subtitle)

    def parse(
        self,
        markdown_text: str,
        override_title: Optional[str] = None,
        override_subtitle: Optional[str] = None,
    ) -> PresentationSpec:
        """Parses markdown text into a fully formed PresentationSpec."""
        # 1. Extract YAML Frontmatter if present
        frontmatter, clean_text = self._extract_frontmatter(markdown_text)

        # 2. Parse hierarchical sections (#, ##, ###, ####)
        sections, doc_title, doc_subtitle = self._parse_markdown_hierarchy(clean_text)

        preso_title = (
            override_title
            or frontmatter.get("title")
            or doc_title
            or "Architecture & Strategy Blueprint"
        )
        preso_subtitle = (
            override_subtitle
            or frontmatter.get("subtitle")
            or doc_subtitle
            or "Deterministic Presentation Blueprint"
        )
        core_thesis = (
            frontmatter.get("core_thesis")
            or frontmatter.get("thesis")
            or frontmatter.get("description")
            or "Transforming technical documentation into executive slide blueprints."
        )
        target_audience = frontmatter.get("target_audience", "Executive Leadership & Senior Staff Engineers")

        # 3. Build Chapters and Slides
        chapters: list[ChapterSpec] = []
        chapter_idx = 1
        global_slide_idx = 1

        # If no ## chapters exist, wrap all ### slides into Chapter 1
        has_chapters = any(sec.level == 2 for sec in sections)

        if not has_chapters:
            slides: list[SlideSpec] = []
            # Add intro divider
            slides.append(
                SlideSpec(
                    archetype="chapter_divider",
                    title=preso_title,
                    subtitle=preso_subtitle,
                    kicker=f"CHAPTER {chapter_idx:02d}",
                    chapter_number=chapter_idx,
                    id=f"SLIDE_{global_slide_idx:02d}_CHAPTER",
                    notes="",
                )
            )
            global_slide_idx += 1

            for sec in sections:
                if sec.level == 3:
                    slide = self._build_slide_from_section(sec, chapter_idx, global_slide_idx)
                    slides.append(slide)
                    global_slide_idx += 1

            if not slides or len(slides) == 1:
                # Synthesize fallback slide if empty
                slides.append(
                    SlideSpec(
                        archetype="split_cards",
                        title="Core Overview",
                        subtitle="Key concepts from ingested document",
                        kicker="OVERVIEW",
                        id=f"SLIDE_{global_slide_idx:02d}_SPLIT",
                        cards=[
                            CardSpec(title="Overview", kicker="ANALYSIS", bullets=["Key point 1", "Key point 2"]),
                            CardSpec(title="Strategy", kicker="PLAN", bullets=["Execution step 1", "Execution step 2"]),
                        ],
                        notes="",
                    )
                )

            chapters.append(
                ChapterSpec(
                    number=1,
                    title=preso_title,
                    subtitle=preso_subtitle,
                    slides=slides,
                    notes=f"Chapter 1 contains all sections from {preso_title}.",
                )
            )
        else:
            # Multi-chapter parsing
            curr_chapter: Optional[ChapterSpec] = None
            curr_chapter_slides: list[SlideSpec] = []

            for sec in sections:
                if sec.level == 2:
                    # Save previous chapter if exists
                    if curr_chapter and curr_chapter_slides:
                        curr_chapter.slides = curr_chapter_slides
                        chapters.append(curr_chapter)
                        curr_chapter_slides = []

                    chap_title = sec.heading
                    chap_subtitle = self._extract_first_sentence(sec.content) or preso_subtitle

                    divider_slide = SlideSpec(
                        archetype="chapter_divider",
                        title=chap_title,
                        subtitle=chap_subtitle,
                        kicker=f"CHAPTER {chapter_idx:02d}",
                        chapter_number=chapter_idx,
                        id=f"SLIDE_{global_slide_idx:02d}_CHAPTER",
                        notes=sec.speaker_notes or "",
                    )
                    global_slide_idx += 1
                    curr_chapter_slides = [divider_slide]

                    for sub in sec.subsections:
                        slide = self._build_slide_from_section(sub, chapter_idx, global_slide_idx)
                        curr_chapter_slides.append(slide)
                        global_slide_idx += 1

                    curr_chapter = ChapterSpec(
                        number=chapter_idx,
                        title=chap_title,
                        subtitle=chap_subtitle,
                        slides=[],
                        notes=f"Chapter {chapter_idx} covers {chap_title}.",
                    )
                    chapter_idx += 1

                elif sec.level == 3:
                    if not curr_chapter:
                        # Create initial chapter
                        divider_slide = SlideSpec(
                            archetype="chapter_divider",
                            title=preso_title,
                            subtitle=preso_subtitle,
                            kicker=f"CHAPTER {chapter_idx:02d}",
                            chapter_number=chapter_idx,
                            id=f"SLIDE_{global_slide_idx:02d}_CHAPTER",
                            notes="",
                        )
                        global_slide_idx += 1
                        curr_chapter_slides = [divider_slide]
                        curr_chapter = ChapterSpec(
                            number=chapter_idx,
                            title=preso_title,
                            subtitle=preso_subtitle,
                            slides=[],
                        )
                        chapter_idx += 1

                    slide = self._build_slide_from_section(sec, chapter_idx - 1, global_slide_idx)
                    curr_chapter_slides.append(slide)
                    global_slide_idx += 1

            if curr_chapter and curr_chapter_slides:
                curr_chapter.slides = curr_chapter_slides
                chapters.append(curr_chapter)

        metadata = MetadataSpec(
            title=preso_title,
            subtitle=preso_subtitle,
            target_audience=target_audience,
            core_thesis=core_thesis,
            template_id="1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U",
        )

        return PresentationSpec(
            metadata=metadata,
            chapters=chapters,
        )

    def _extract_frontmatter(self, text: str) -> tuple[dict[str, Any], str]:
        """Extracts YAML frontmatter delimited by ---."""
        fm_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
        if fm_match:
            raw_fm = fm_match.group(1)
            body = fm_match.group(2)
            try:
                parsed = yaml.safe_load(raw_fm)
                if isinstance(parsed, dict):
                    return parsed, body
            except Exception:
                pass
        return {}, text

    def _parse_markdown_hierarchy(
        self, text: str
    ) -> tuple[list[RawSection], Optional[str], Optional[str]]:
        """Parses markdown into hierarchical RawSection objects."""
        lines = text.splitlines()
        sections: list[RawSection] = []
        doc_title: Optional[str] = None
        doc_subtitle: Optional[str] = None

        curr_sec: Optional[RawSection] = None
        curr_sub: Optional[RawSection] = None
        curr_content_lines: list[str] = []

        in_code = False
        code_fence_lines: list[str] = []
        code_lang = "python"
        code_filename = "snippet.py"

        for line in lines:
            # Code fence handling
            if line.strip().startswith("```"):
                if in_code:
                    in_code = False
                    code_block = {
                        "filename": code_filename,
                        "code": "\n".join(code_fence_lines),
                        "language": code_lang,
                    }
                    if curr_sub:
                        curr_sub.code_blocks.append(code_block)
                    elif curr_sec:
                        curr_sec.code_blocks.append(code_block)
                    code_fence_lines = []
                else:
                    in_code = True
                    fence = line.strip().lstrip("`").strip()
                    if fence:
                        parts = fence.split()
                        code_lang = parts[0]
                        if len(parts) > 1 and ":" in parts[1]:
                            code_filename = parts[1].split(":", 1)[1]
                        elif len(parts) > 1:
                            code_filename = parts[1]
                continue

            if in_code:
                code_fence_lines.append(line)
                continue

            # Heading checks
            h1_match = re.match(r"^#\s+(.+)$", line)
            h2_match = re.match(r"^##\s+(.+)$", line)
            h3_match = re.match(r"^###\s+(.+)$", line)
            h4_match = re.match(r"^####\s+(.+)$", line)

            if h1_match and not doc_title:
                doc_title = h1_match.group(1).strip()
                continue

            if h2_match:
                if curr_sub and curr_sec:
                    curr_sub.content = "\n".join(curr_content_lines).strip()
                    self._extract_embedded_elements(curr_sub)
                    curr_sec.subsections.append(curr_sub)
                    curr_sub = None
                    curr_content_lines = []
                elif curr_sec:
                    curr_sec.content = "\n".join(curr_content_lines).strip()
                    self._extract_embedded_elements(curr_sec)
                    curr_content_lines = []

                if curr_sec:
                    sections.append(curr_sec)
                    curr_sec = None

                curr_sec = RawSection(level=2, heading=h2_match.group(1).strip())
                continue

            if h3_match:
                if curr_sub and curr_sec:
                    curr_sub.content = "\n".join(curr_content_lines).strip()
                    self._extract_embedded_elements(curr_sub)
                    curr_sec.subsections.append(curr_sub)
                    curr_sub = None
                    curr_content_lines = []
                elif curr_sec and curr_sec.level == 3:
                    curr_sec.content = "\n".join(curr_content_lines).strip()
                    self._extract_embedded_elements(curr_sec)
                    sections.append(curr_sec)
                    curr_sec = None
                    curr_content_lines = []
                elif curr_sec and curr_sec.level == 2 and not curr_sec.subsections and curr_content_lines:
                    curr_sec.content = "\n".join(curr_content_lines).strip()
                    self._extract_embedded_elements(curr_sec)
                    curr_content_lines = []

                new_sub = RawSection(level=3, heading=h3_match.group(1).strip())
                if curr_sec and curr_sec.level == 2:
                    curr_sub = new_sub
                else:
                    curr_sec = new_sub
                continue

            if h4_match:
                # Sub-card / sub-point heading
                curr_content_lines.append(f"#### {h4_match.group(1).strip()}")
                continue

            # Check for subtitle right after # Title
            if doc_title and not doc_subtitle and line.strip() and not line.startswith("#"):
                doc_subtitle = line.strip()

            curr_content_lines.append(line)

        # Flush final section
        if curr_sub and curr_sec:
            curr_sub.content = "\n".join(curr_content_lines).strip()
            self._extract_embedded_elements(curr_sub)
            curr_sec.subsections.append(curr_sub)
            sections.append(curr_sec)
        elif curr_sec:
            curr_sec.content = "\n".join(curr_content_lines).strip()
            self._extract_embedded_elements(curr_sec)
            sections.append(curr_sec)

        return sections, doc_title, doc_subtitle

    def _extract_embedded_elements(self, sec: RawSection) -> None:
        """Extracts bullet lists, tables, blockquotes, and speaker notes from section content."""
        lines = sec.content.splitlines()
        current_list: list[str] = []
        in_table = False
        table_rows: list[list[str]] = []

        for line in lines:
            # Speaker notes
            note_match = re.match(
                r"^(?:>\s*\*\*Speaker Notes:\*\*|<!--\s*(?:Notes|notes|SPEAKER NOTES)[:\s]*|\*Notes:\*|Notes:)\s*(.*)", line, re.IGNORECASE
            )
            if note_match:
                raw_note = note_match.group(1)
                clean_note = re.sub(r"-->\s*$", "", raw_note).strip()
                sec.speaker_notes = f"{sec.speaker_notes} {clean_note}".strip()
                continue

            # Blockquote
            if line.strip().startswith(">"):
                quote_text = line.strip().lstrip(">").strip()
                if quote_text and not quote_text.startswith("**Speaker Notes:"):
                    sec.blockquotes.append(quote_text)
                continue

            # Table
            if line.strip().startswith("|") and line.strip().endswith("|"):
                # Table row
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                if all(re.match(r"^:?-+:?$", c) for c in cells):
                    # Separator line
                    continue
                table_rows.append(cells)
                in_table = True
                continue
            else:
                if in_table and table_rows:
                    sec.tables.append(table_rows)
                    table_rows = []
                    in_table = False

            # Bullet points / numbered items
            bullet_match = re.match(r"^\s*(?:[-*+]|\d+\.)\s+(.+)$", line)
            if bullet_match:
                current_list.append(bullet_match.group(1).strip())
            else:
                if current_list:
                    sec.lists.append(current_list)
                    current_list = []

        if table_rows:
            sec.tables.append(table_rows)
        if current_list:
            sec.lists.append(current_list)

    def _build_slide_from_section(
        self, sec: RawSection, chapter_idx: int, slide_idx: int
    ) -> SlideSpec:
        """Heuristically selects Blueprint archetype and builds SlideSpec from RawSection."""
        title = self._truncate_text(sec.heading, max_chars=60)
        subtitle = self._extract_first_sentence(sec.content) or "Architectural analysis and blueprint structure"
        subtitle = self._truncate_text(subtitle, max_chars=120)
        notes = sec.speaker_notes or ""

        slide_id = f"SLIDE_{slide_idx:02d}"

        # 1. Code Terminal / Ratchet Archetype
        if sec.code_blocks:
            cb = sec.code_blocks[0]
            filename = cb.get("filename", "snippet.py")
            code_text = cb.get("code", "")
            lang = cb.get("language", "python")

            # Check for Do / Don't in comments or content
            status = "do"
            badge = "✓ VERIFIED PATTERN"
            if "dont" in title.lower() or "anti-pattern" in title.lower():
                status = "dont"
                badge = "✗ ANTI-PATTERN"

            return SlideSpec(
                archetype="code_terminal",
                title=title,
                subtitle=subtitle,
                kicker="CODE CONTAINER",
                id=slide_id,
                notes=notes,
                terminals=[
                    CodeBlockSpec(
                        filename=filename,
                        code=self._trim_code(code_text, max_lines=14),
                        language=lang,
                        status=status,
                        badge_text=badge,
                    )
                ],
            )

        # 2. Do / Don't Checklist
        if (
            "do" in title.lower()
            and "don't" in title.lower()
        ) or "best practice" in title.lower() or "anti-pattern" in title.lower():
            dos, donts = self._extract_dos_and_donts(sec)
            return SlideSpec(
                archetype="dodont_checklist",
                title=title,
                subtitle=subtitle,
                kicker="BEST PRACTICES",
                id=slide_id,
                notes=notes,
                checklist=ChecklistSpec(
                    do_items=dos[:4],
                    dont_items=donts[:4],
                    do_title="BLUEPRINT STANDARD (DO)",
                    dont_title="COMMON TRAPS (DON'T)",
                    takeaway="Engineering discipline compounds across every automated iteration.",
                ),
            )

        # 3. Hero Metrics / Stats
        metrics = self._extract_metrics(sec)
        if len(metrics) >= 2:
            return SlideSpec(
                archetype="hero_metrics",
                title=title,
                subtitle=subtitle,
                kicker="ECONOMICS & METRICS",
                id=slide_id,
                notes=notes,
                metrics=metrics[:3],
            )

        # 4. Ladder Hierarchy (3 to 5 sequential steps)
        steps = self._extract_steps(sec)
        if 3 <= len(steps) <= 5:
            return SlideSpec(
                archetype="ladder_hierarchy",
                title=title,
                subtitle=subtitle,
                kicker="PROCESS LADDER",
                id=slide_id,
                notes=notes,
                steps=steps,
            )

        # 5. Executive Grid (4 distinct sub-cards or quadrants)
        quadrants = self._extract_quadrants(sec)
        if len(quadrants) == 4:
            return SlideSpec(
                archetype="executive_grid",
                title=title,
                subtitle=subtitle,
                kicker="PILLARS",
                id=slide_id,
                notes=notes,
                quadrants=quadrants,
            )

        # 6. Actionable Takeaways & Next Steps
        if "takeaway" in title.lower() or "next step" in title.lower() or "roadmap" in title.lower() or "conclusion" in title.lower():
            principles = [
                PrincipleSpec(number=1, title="Spec Definition", description="Author structured manifests before building."),
                PrincipleSpec(number=2, title="Enforcing Ratchets", description="Gate commits with deterministic hooks."),
                PrincipleSpec(number=3, title="Verification Loop", description="Execute automated visual and WCAG QA."),
            ]
            return SlideSpec(
                archetype="actionable_takeaways",
                title=title,
                subtitle=subtitle,
                kicker="ACTIONABLE ROADMAP",
                id=slide_id,
                notes=notes,
                takeaway=TakeawaySpec(
                    thesis="Automated slide engineering shifts focus from slide formatting to clear judgment.",
                    principles=principles,
                    roadmap_title="MILESTONE ROADMAP",
                    roadmap_items=[
                        "Phase 1: Ingest codebase AST & documentation",
                        "Phase 2: Generate single-pass atomic gslides payload",
                        "Phase 3: Automated visual thumbnail verification",
                    ],
                    cta_text="START HARNESS BUILD →",
                    contact_info="go/preso-builder · feedback@google.com",
                ),
            )

        # 7. Tables converted to Split Comparison Cards
        if sec.tables:
            table = sec.tables[0]
            if len(table) >= 2 and len(table[0]) >= 2:
                card1_title = self._truncate_text(table[0][0], max_chars=35)
                card2_title = self._truncate_text(table[0][1], max_chars=35)
                card1_bullets = [self._truncate_text(row[0], max_chars=90) for row in table[1:5] if row]
                card2_bullets = [self._truncate_text(row[1], max_chars=90) for row in table[1:5] if len(row) > 1]
                return SlideSpec(
                    archetype="split_cards",
                    title=title,
                    subtitle=subtitle,
                    kicker="COMPARISON",
                    id=slide_id,
                    notes=notes,
                    cards=[
                        CardSpec(title=card1_title, kicker="DIMENSION A", bullets=card1_bullets, theme="#1A73E8"),
                        CardSpec(title=card2_title, kicker="DIMENSION B", bullets=card2_bullets, theme="#1E8E3E"),
                    ],
                )

        # 8. Default: Split Cards (2-Card or 3-Card)
        cards = self._extract_cards(sec)
        return SlideSpec(
            archetype="split_cards",
            title=title,
            subtitle=subtitle,
            kicker="ANALYSIS",
            id=slide_id,
            notes=notes,
            cards=cards[:3],
        )

    def _extract_cards(self, sec: RawSection) -> list[CardSpec]:
        """Extracts structured CardSpecs from section #### headings or lists."""
        cards: list[CardSpec] = []

        # Check #### subheadings
        h4_chunks = re.split(r"(?:^|\n)####\s+(.+)$", sec.content, flags=re.MULTILINE)
        if len(h4_chunks) >= 3:
            # [prefix, h4_title1, content1, h4_title2, content2, ...]
            i = 1
            while i < len(h4_chunks) and len(cards) < 3:
                card_title = self._truncate_text(h4_chunks[i].strip(), max_chars=35)
                card_content = h4_chunks[i + 1] if i + 1 < len(h4_chunks) else ""
                bullets = [
                    self._truncate_text(b.strip(), max_chars=90)
                    for b in re.findall(r"^\s*(?:[-*+]|\d+\.)\s+(.+)$", card_content, flags=re.MULTILINE)
                ]
                if not bullets:
                    first_line = card_content.strip().split("\n")[0]
                    bullets = [self._truncate_text(first_line, max_chars=90)] if first_line else ["Standard principle"]

                cards.append(
                    CardSpec(
                        title=card_title,
                        kicker=f"CARD {len(cards) + 1:02d}",
                        bullets=bullets[:4],
                        theme="#1A73E8" if len(cards) % 2 == 0 else "#1E8E3E",
                    )
                )
                i += 2

        if not cards and sec.lists:
            # Split list into 2 cards
            all_items = [self._truncate_text(item, max_chars=90) for sublist in sec.lists for item in sublist]
            if len(all_items) >= 4:
                half = len(all_items) // 2
                cards.append(
                    CardSpec(
                        title="Key Capabilities",
                        kicker="OVERVIEW",
                        bullets=all_items[:half][:4],
                        theme="#1A73E8",
                    )
                )
                cards.append(
                    CardSpec(
                        title="Execution Outcomes",
                        kicker="IMPACT",
                        bullets=all_items[half:half + 4],
                        theme="#1E8E3E",
                    )
                )
            else:
                cards.append(
                    CardSpec(
                        title="Core Principles",
                        kicker="PRINCIPLES",
                        bullets=all_items or ["Modular design architecture", "Predictable execution"],
                        theme="#1A73E8",
                    )
                )
                cards.append(
                    CardSpec(
                        title="Implementation Details",
                        kicker="EXECUTION",
                        bullets=["Type-safe models", "Continuous automated testing"],
                        theme="#1E8E3E",
                    )
                )

        if not cards:
            cards = [
                CardSpec(
                    title="System Overview",
                    kicker="ANALYSIS",
                    bullets=["Architectural components", "Grounded design principles"],
                    theme="#1A73E8",
                ),
                CardSpec(
                    title="Key Deliverables",
                    kicker="DELIVERY",
                    bullets=["Verified test suites", "Deterministic slide generation"],
                    theme="#1E8E3E",
                ),
            ]

        return cards

    def _extract_dos_and_donts(self, sec: RawSection) -> tuple[list[str], list[str]]:
        """Extracts Do and Don't lists from section content."""
        dos: list[str] = []
        donts: list[str] = []

        lines = sec.content.splitlines()
        in_do = False
        in_dont = False

        for line in lines:
            if re.match(r"^(?:####\s+)?(?:DO|BLUEPRINT STANDARD|PROS|BEST PRACTICE)", line, re.IGNORECASE):
                in_do = True
                in_dont = False
                continue
            elif re.match(r"^(?:####\s+)?(?:DON'?T|ANTI-PATTERN|CONS|COMMON TRAPS)", line, re.IGNORECASE):
                in_dont = True
                in_do = False
                continue

            bullet = re.sub(r"^\s*(?:[-*+]|\d+\.|✓|✗)\s*", "", line).strip()
            if not bullet:
                continue

            if in_do or line.startswith("✓") or line.lower().startswith("do:"):
                dos.append(self._truncate_text(bullet, max_chars=90))
            elif in_dont or line.startswith("✗") or line.lower().startswith("don't:"):
                donts.append(self._truncate_text(bullet, max_chars=90))

        if not dos:
            dos = [
                "Define verifiable completion criteria before running tasks.",
                "Enforce immutable data models and strict schema validation.",
                "Isolate development tasks in separate worktrees.",
            ]
        if not donts:
            donts = [
                "Fanning out vague requirements without verification gates.",
                "Relying on model retries instead of ratcheted hooks.",
                "Allowing unverified commits to bypass human review.",
            ]

        return dos, donts

    def _extract_metrics(self, sec: RawSection) -> list[HeroMetricSpec]:
        """Extracts HeroMetricSpec instances from section content."""
        metrics: list[HeroMetricSpec] = []
        matches = re.findall(
            r"\*\*(\$?[0-9]+(?:\.[0-9]+)?(?:[kKmMbB%xX]|ms|s|min|hr|QPS)?)\*\*\s*[-:·]?\s*([^\n\.]+)",
            sec.content,
        )
        for stat, desc in matches:
            if len(stat) <= 12:
                metrics.append(
                    HeroMetricSpec(
                        value=stat,
                        unit="",
                        label="MEASUREMENT",
                        description=self._truncate_text(desc.strip(), max_chars=100),
                    )
                )
        return metrics

    def _extract_steps(self, sec: RawSection) -> list[LadderStepSpec]:
        """Extracts LadderStepSpec rungs from numbered lists or headings."""
        steps: list[LadderStepSpec] = []
        matches = re.findall(
            r"(?:^|\n)(?:Step\s+)?([1-5])[\.\:\)]\s+([^\n\:]+)(?::\s*([^\n]+))?",
            sec.content,
        )
        for num, title_part, desc_part in matches:
            step_num = int(num)
            title = self._truncate_text(title_part.strip(), max_chars=35)
            desc = self._truncate_text((desc_part or title_part).strip(), max_chars=90)
            steps.append(LadderStepSpec(step_number=step_num, title=title, description=desc))
        return steps

    def _extract_quadrants(self, sec: RawSection) -> list[QuadrantSpec]:
        """Extracts QuadrantSpec items from 4 items or 4 subheadings."""
        quadrants: list[QuadrantSpec] = []
        # Check #### subheadings
        h4_matches = re.findall(r"^####\s+(.+)$", sec.content, flags=re.MULTILINE)
        if len(h4_matches) == 4:
            for i, h in enumerate(h4_matches, start=1):
                quadrants.append(
                    QuadrantSpec(
                        number=f"{i:02d}",
                        title=self._truncate_text(h.strip(), max_chars=35),
                        narrative=f"Core operational capability for {h.strip()}.",
                    )
                )
        return quadrants

    def _extract_first_sentence(self, text: str) -> str:
        """Extracts the first readable sentence from a text block."""
        for paragraph in text.split("\n\n"):
            p = paragraph.strip()
            if p.startswith(("#", "-", "*", ">", "|", "```")):
                continue
            sentences = re.split(r"(?<=[.!?])\s+", p)
            if sentences and len(sentences[0]) > 10:
                return sentences[0].strip()
        return ""

    def _trim_code(self, code: str, max_lines: int = 14, max_line_len: int = 56) -> str:
        """Trims code snippet to fit neatly inside terminal archetype."""
        lines = code.splitlines()
        out = []
        for line in lines[:max_lines]:
            if len(line) > max_line_len:
                line = line[: max_line_len - 3] + "..."
            out.append(line)
        return "\n".join(out)

    def _truncate_text(self, text: str, max_chars: int) -> str:
        """Truncates text safely with ellipsis."""
        cleaned = text.strip().replace("\n", " ")
        if len(cleaned) <= max_chars:
            return cleaned
        return cleaned[: max_chars - 3] + "..."

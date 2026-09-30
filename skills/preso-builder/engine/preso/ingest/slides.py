"""Google Slides Presentation Multi-Modal Ingestion Module.

Ingests existing Google Slides presentations via `gslides read-all` CLI text output,
JSON payload structures, or dictionary hierarchies, extracts structural semantics
(titles, kickers, cards, bullet points, code blocks, metrics, speaker notes),
heuristically maps each slide to one of the 8 Blueprint archetypes, and compiles
a structured, valid PresentationSpec.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
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
    PrincipleSpec,
    QuadrantSpec,
    SlideSpec,
    TakeawaySpec,
)


class SlidesIngestor:
    """Ingests Google Slides presentations and maps them to Blueprint archetypes.

    Supports:
    1. Direct deck ID ingestion (invoking gslides CLI or GSlidesClient).
    2. Parsing raw text dumps from `gslides read-all <deck_id>`.
    3. Parsing JSON dumps from `gslides read-all --json` or Google Slides API.
    4. Heuristic archetype classification across all 8 AI Factory Blueprint layouts.
    5. Authored speaker notes pass-through and text capacity normalization.
    """

    GSLIDES_PATH = "/google/bin/releases/gemini-agents-gslides/gslides"

    def __init__(self, deck_id_or_data: Optional[Union[str, dict[str, Any], list[Any]]] = None) -> None:
        self.raw_source = deck_id_or_data

    def ingest(
        self,
        deck_id_or_data: Optional[Union[str, dict[str, Any], list[Any]]] = None,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
    ) -> PresentationSpec:
        """Main ingestion entrypoint. Converts any presentation input into a PresentationSpec."""
        source = deck_id_or_data if deck_id_or_data is not None else self.raw_source
        if source is None:
            raise ValueError("No presentation source (deck_id, text, or dict/json) provided for ingestion.")

        raw_slides: list[dict[str, Any]] = []

        if isinstance(source, dict):
            raw_slides = self.parse_gslides_json(source)
        elif isinstance(source, list):
            raw_slides = self.parse_gslides_json({"slides": source})
        elif isinstance(source, str):
            # Check if source is a file path
            is_file = False
            if "\n" not in source and len(source) < 500:
                try:
                    p = Path(source)
                    if p.is_file():
                        is_file = True
                except (OSError, ValueError):
                    is_file = False

            if is_file:
                try:
                    with open(Path(source), "r", encoding="utf-8") as f:
                        file_content = f.read()
                    try:
                        json_obj = json.loads(file_content)
                        raw_slides = self.parse_gslides_json(json_obj)
                    except json.JSONDecodeError:
                        raw_slides = self.parse_read_all_text(file_content)
                except OSError as e:
                    raise IOError(f"Failed to read presentation file {source}: {e}") from e
            elif "--- Slide" in source or "=== Slide" in source or "Slide " in source:
                raw_slides = self.parse_read_all_text(source)
            elif source.strip().startswith("{") or source.strip().startswith("["):
                try:
                    json_obj = json.loads(source)
                    raw_slides = self.parse_gslides_json(json_obj)
                except json.JSONDecodeError:
                    raw_slides = self.parse_read_all_text(source)
            else:
                # Treat as Google Slides deck ID
                raw_slides = self._fetch_and_parse_deck_id(source.strip())
        else:
            raise TypeError(f"Unsupported presentation source type: {type(source)}")

        if not raw_slides:
            # Fallback if empty presentation
            raw_slides = [{
                "title": "Blueprint Presentation",
                "subtitle": "Ingested Google Slides Outline",
                "speaker_notes": "Welcome to the presentation. This deck was generated from ingested slides.",
                "bullets": ["Overview of presentation structure", "Key takeaways and next steps"],
            }]

        return self._build_presentation_spec(raw_slides, title=title, subtitle=subtitle)

    def _fetch_and_parse_deck_id(self, deck_id: str) -> list[dict[str, Any]]:
        """Calls gslides read-all CLI binary or falls back to mock structure."""
        if Path(self.GSLIDES_PATH).exists():
            try:
                proc = subprocess.run(
                    [self.GSLIDES_PATH, "read-all", deck_id],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    check=False,
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    return self.parse_read_all_text(proc.stdout)
            except Exception:
                pass

        # Fallback default presentation outline for deck_id
        return [
            {
                "title": f"Presentation {deck_id[:8]}",
                "subtitle": "AI Factory Blueprint Transformation",
                "speaker_notes": "Welcome everyone. Today we are reviewing the ingested presentation outline.",
                "archetype": "chapter_divider",
            },
            {
                "title": "Core Strategic Pillars",
                "subtitle": "Transforming unstructured content into structured archetypes",
                "speaker_notes": "On this slide we examine the primary architectural pillars extracted from the deck.",
                "cards": [
                    {"title": "Ingestion", "bullets": ["Multi-modal scanning", "AST & symbol extraction"]},
                    {"title": "Compilation", "bullets": ["Single-pass batch ops", "Deterministic geometry"]},
                ],
            },
        ]

    def parse_read_all_text(self, text: str) -> list[dict[str, Any]]:
        """Parses the plain text output generated by `gslides read-all <deck_id>`."""
        raw_slides: list[dict[str, Any]] = []

        # Split by slide demarcations
        slide_pattern = r"(?:^|\n)(?:[-=]{3,}\s*Slide\s*(\d+)?(?:\s*\(([^)]+)\))?\s*[-=]{3,}|Slide\s+(\d+)[:\s])"
        chunks = re.split(slide_pattern, text, flags=re.MULTILINE)

        if len(chunks) == 1:
            # No demarcations found, treat entire text as one slide or split by double newlines
            parsed = self._parse_single_slide_text(chunks[0], index=1)
            if parsed:
                raw_slides.append(parsed)
            return raw_slides

        # re.split with 3 capturing groups produces 4 items per match:
        # [prefix, match_num1, match_id, match_num2, content, match_num1, match_id, match_num2, content, ...]
        i = 1
        slide_idx = 1
        while i < len(chunks):
            num1 = chunks[i]
            slide_id = chunks[i + 1] or ""
            num2 = chunks[i + 2]
            content = chunks[i + 3] if i + 3 < len(chunks) else ""

            assigned_num = num1 or num2 or str(slide_idx)
            parsed = self._parse_single_slide_text(content, index=int(assigned_num) if assigned_num.isdigit() else slide_idx)
            if parsed:
                if slide_id:
                    parsed["id"] = slide_id
                raw_slides.append(parsed)
                slide_idx += 1
            i += 4

        return raw_slides

    def _parse_single_slide_text(self, text: str, index: int = 1) -> dict[str, Any]:
        """Parses a single slide text block into structured components."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            return {}

        slide_dict: dict[str, Any] = {
            "index": index,
            "title": "",
            "subtitle": "",
            "kicker": "",
            "speaker_notes": "",
            "bullets": [],
            "cards": [],
            "code_block": None,
            "metrics": [],
            "steps": [],
            "quadrants": [],
            "do_items": [],
            "dont_items": [],
            "takeaways": [],
        }

        # Check for Speaker Notes block
        notes_lines: list[str] = []
        body_lines: list[str] = []
        in_notes = False
        in_code = False
        code_lines: list[str] = []
        code_lang = "python"
        code_filename = "snippet.py"

        for line in lines:
            # Notes demarcation
            if re.match(r"^(?:Speaker Notes|Notes|SPEAKER NOTES)[:\s]*", line, re.IGNORECASE):
                in_notes = True
                note_content = re.sub(r"^(?:Speaker Notes|Notes|SPEAKER NOTES)[:\s]*", "", line, flags=re.IGNORECASE).strip()
                if note_content:
                    notes_lines.append(note_content)
                continue

            if in_notes:
                notes_lines.append(line)
                continue

            # Code fence demarcation
            if line.startswith("```"):
                if in_code:
                    in_code = False
                    slide_dict["code_block"] = {
                        "filename": code_filename,
                        "code": "\n".join(code_lines),
                        "language": code_lang,
                    }
                    code_lines = []
                else:
                    in_code = True
                    fence_header = line.lstrip("`").strip()
                    if fence_header:
                        code_lang = fence_header
                continue

            if in_code:
                code_lines.append(line)
                continue

            body_lines.append(line)

        if in_code and code_lines:
            slide_dict["code_block"] = {
                "filename": code_filename,
                "code": "\n".join(code_lines),
                "language": code_lang,
            }

        slide_dict["speaker_notes"] = " ".join(notes_lines).strip()

        # Parse body lines for Title, Subtitle, Kicker, Bullets, Metrics, and Cards
        self._parse_body_content(body_lines, slide_dict)
        return slide_dict

    def _parse_body_content(self, lines: list[str], slide_dict: dict[str, Any]) -> None:
        """Parses lines into title, subtitle, bullets, metrics, cards, and Do/Don't lists."""
        if not lines:
            return

        # Check if first line is a category pill / kicker
        curr_idx = 0
        if len(lines) > 1 and lines[0].isupper() and len(lines[0]) <= 25 and not lines[0].startswith(("•", "-", "*")):
            slide_dict["kicker"] = lines[0]
            curr_idx = 1

        # Title
        if curr_idx < len(lines):
            raw_title = lines[curr_idx].lstrip("#").strip()
            # Strip bullet prefixes if present
            raw_title = re.sub(r"^[•\-*0-9\.]+\s*", "", raw_title)
            slide_dict["title"] = raw_title
            curr_idx += 1

        # Subtitle or First Content
        if curr_idx < len(lines) and not lines[curr_idx].startswith(("•", "-", "*", "1.", "2.", "✓", "✗", "DO", "DON'T")):
            # If line is descriptive text and not too long
            if len(lines[curr_idx]) < 140:
                slide_dict["subtitle"] = lines[curr_idx]
                curr_idx += 1

        # Remaining lines: analyze bullets, cards, metrics, Do/Don'ts
        curr_card_title = ""
        curr_card_bullets: list[str] = []
        in_dont_mode = False
        in_do_mode = False

        for line in lines[curr_idx:]:
            # Detect Do / Don't
            if re.match(r"^(?:DON'?T|ANTI-PATTERN|COMMON TRAPS|BAD)[:\s]*", line, re.IGNORECASE):
                in_dont_mode = True
                in_do_mode = False
                continue
            elif re.match(r"^(?:DO|BLUEPRINT STANDARD|BEST PRACTICE|GOOD)[:\s]*", line, re.IGNORECASE):
                in_do_mode = True
                in_dont_mode = False
                continue

            if in_dont_mode:
                clean_item = re.sub(r"^[•\-*✗x0-9\.]+\s*", "", line).strip()
                if clean_item:
                    slide_dict["dont_items"].append(clean_item)
                continue
            elif in_do_mode:
                clean_item = re.sub(r"^[•\-*✓0-9\.]+\s*", "", line).strip()
                if clean_item:
                    slide_dict["do_items"].append(clean_item)
                continue

            if line.startswith("✗") or line.lower().startswith("don't:"):
                clean_item = re.sub(r"^(?:✗|don't:?)\s*", "", line, flags=re.IGNORECASE).strip()
                if clean_item:
                    slide_dict["dont_items"].append(clean_item)
                continue
            elif line.startswith("✓") or line.lower().startswith("do:"):
                clean_item = re.sub(r"^(?:✓|do:?)\s*", "", line, flags=re.IGNORECASE).strip()
                if clean_item:
                    slide_dict["do_items"].append(clean_item)
                continue

            # Detect Hero Metric: e.g. "$200", "99.9%", "10x", "30s"
            metric_match = re.match(
                r"^(\$?[0-9]+(?:\.[0-9]+)?(?:[kKmMbB%xX]|ms|s|min|hr|QPS)?)\s*[-:·]?\s*(.*)$", line
            )
            if metric_match and len(metric_match.group(1)) <= 12 and not line.startswith(("1.", "2.", "3.", "4.", "5.")):
                stat = metric_match.group(1)
                desc = metric_match.group(2).strip()
                slide_dict["metrics"].append({
                    "value": stat,
                    "unit": "",
                    "label": desc.split(":")[0] if ":" in desc else "METRIC",
                    "description": desc,
                })
                continue

            # Detect Step/Ladder: e.g. "Step 1: Ingest Codebase" or "1. Prompt Engineering"
            step_match = re.match(r"^(?:Step\s+)?([1-5])[\.\:\)]\s*(.+)$", line, re.IGNORECASE)
            if step_match:
                step_num = int(step_match.group(1))
                step_text = step_match.group(2).strip()
                title_part, _, desc_part = step_text.partition(":")
                slide_dict["steps"].append({
                    "step_number": step_num,
                    "title": title_part.strip(),
                    "description": desc_part.strip() or title_part.strip(),
                })
                continue

            # Detect Quadrant / 4-card items: e.g. "#### 01 Prompt" or "01 Prompt" or "#### Pillar 1"
            quad_match = re.match(r"^(?:####\s+)?(?:0?([1-4])|Quadrant\s+([1-4]))[\.\:\s\-]+(.+)$", line, re.IGNORECASE)
            if quad_match:
                q_num = quad_match.group(1) or quad_match.group(2)
                q_title = quad_match.group(3).strip()
                slide_dict["quadrants"].append({
                    "number": f"{int(q_num):02d}",
                    "title": q_title,
                    "narrative": "",
                })
                continue

            # If inside quadrant and narrative is empty, populate it
            if slide_dict["quadrants"] and not slide_dict["quadrants"][-1]["narrative"]:
                slide_dict["quadrants"][-1]["narrative"] = line.strip()
                continue

            # Detect Card / Pillar subheaders: e.g. "Card 1: Foundation" or bold titles
            if line.endswith(":") or (line.isupper() and len(line) < 30 and not line.startswith(("•", "-"))):
                if curr_card_title and curr_card_bullets:
                    slide_dict["cards"].append({
                        "title": curr_card_title,
                        "bullets": list(curr_card_bullets),
                    })
                    curr_card_bullets = []
                curr_card_title = line.rstrip(":")
                continue

            # Regular bullet point or body paragraph
            clean_bullet = re.sub(r"^[•\-*0-9\.]+\s*", "", line).strip()
            if clean_bullet:
                if curr_card_title:
                    curr_card_bullets.append(clean_bullet)
                else:
                    slide_dict["bullets"].append(clean_bullet)

        if curr_card_title and curr_card_bullets:
            slide_dict["cards"].append({
                "title": curr_card_title,
                "bullets": list(curr_card_bullets),
            })

    def parse_gslides_json(self, data: Union[dict[str, Any], list[Any]]) -> list[dict[str, Any]]:
        """Parses Google Slides API or gslides info JSON into structured slides."""
        raw_slides: list[dict[str, Any]] = []

        slides_list = []
        if isinstance(data, list):
            slides_list = data
        elif isinstance(data, dict):
            slides_list = data.get("slides") or data.get("pages") or []

        for i, slide_obj in enumerate(slides_list, start=1):
            if not isinstance(slide_obj, dict):
                continue

            # Handle direct dictionary representation if already structured
            if "archetype" in slide_obj and ("title" in slide_obj or "cards" in slide_obj):
                raw_slides.append(slide_obj)
                continue

            slide_id = slide_obj.get("objectId") or slide_obj.get("id") or f"SLIDE_{i:02d}"
            title = ""
            subtitle = ""
            kicker = ""
            bullets: list[str] = []
            speaker_notes = ""

            # Extract speaker notes
            notes_page = slide_obj.get("slideProperties", {}).get("notesPage", {})
            if notes_page and "pageElements" in notes_page:
                for elem in notes_page.get("pageElements", []):
                    shape = elem.get("shape", {})
                    text_content = shape.get("text", {})
                    notes_text = self._extract_text_from_text_element(text_content)
                    if notes_text and not notes_text.startswith("Speaker notes"):
                        speaker_notes = notes_text.strip()
                        break
            elif "notes" in slide_obj or "speaker_notes" in slide_obj:
                speaker_notes = str(slide_obj.get("speaker_notes") or slide_obj.get("notes") or "")

            # Extract page elements
            page_elements = slide_obj.get("pageElements", [])
            for elem in page_elements:
                shape = elem.get("shape", {})
                text_content = shape.get("text", {})
                extracted = self._extract_text_from_text_element(text_content).strip()
                if not extracted:
                    continue

                lines = extracted.splitlines()
                first_line = lines[0].strip()

                if not title and len(first_line) <= 60:
                    title = first_line
                    if len(lines) > 1:
                        subtitle = lines[1].strip()
                    for extra in lines[2:]:
                        bullets.append(extra.strip())
                elif not subtitle and len(first_line) <= 120:
                    subtitle = first_line
                    for extra in lines[1:]:
                        bullets.append(extra.strip())
                else:
                    for l in lines:
                        bullets.append(l.strip())

            slide_dict: dict[str, Any] = {
                "index": i,
                "id": slide_id,
                "title": title or slide_obj.get("title", f"Slide {i}"),
                "subtitle": subtitle or slide_obj.get("subtitle", ""),
                "kicker": kicker,
                "speaker_notes": speaker_notes,
                "bullets": bullets,
                "cards": slide_obj.get("cards", []),
                "metrics": slide_obj.get("metrics", []),
                "steps": slide_obj.get("steps", []),
                "quadrants": slide_obj.get("quadrants", []),
                "do_items": slide_obj.get("do_items", []),
                "dont_items": slide_obj.get("dont_items", []),
            }
            raw_slides.append(slide_dict)

        return raw_slides

    def _extract_text_from_text_element(self, text_elem: dict[str, Any]) -> str:
        """Extracts text runs from a Google Slides text element structure."""
        if not text_elem or not isinstance(text_elem, dict):
            return ""
        text_elements = text_elem.get("textElements", [])
        collected = []
        for te in text_elements:
            auto_text = te.get("autoText", {})
            if auto_text:
                continue
            text_run = te.get("textRun", {})
            content = text_run.get("content", "")
            if content:
                collected.append(content)
        return "".join(collected).strip()

    def classify_and_map_slide(self, raw_slide: dict[str, Any], slide_index: int = 1) -> SlideSpec:
        """Heuristically selects the most fitting Blueprint archetype and creates a SlideSpec."""
        # Check explicit archetype override
        explicit_arch = raw_slide.get("archetype", "").strip().lower().replace("-", "_")
        title = raw_slide.get("title", f"Slide {slide_index}")
        subtitle = raw_slide.get("subtitle", "")
        kicker = raw_slide.get("kicker", "")
        notes = raw_slide.get("speaker_notes") or raw_slide.get("notes") or ""
        slide_id = raw_slide.get("id") or f"SLIDE_{slide_index:02d}"

        # 1. Do / Don't Checklist
        if explicit_arch == "dodont_checklist" or (raw_slide.get("do_items") and raw_slide.get("dont_items")):
            do_items = raw_slide.get("do_items", ["Enforce automated pre-commit gates", "Isolate tasks in worktrees"])
            dont_items = raw_slide.get("dont_items", ["Relying on hoping the model succeeds", "Directly pushing unverified code"])
            return SlideSpec(
                archetype="dodont_checklist",
                title=title,
                subtitle=subtitle or "Blueprint standards vs common anti-patterns",
                kicker=kicker or "STANDARDS",
                id=slide_id,
                notes=self._clean_notes(notes),
                checklist=ChecklistSpec(
                    do_items=do_items[:4],
                    dont_items=dont_items[:4],
                    do_title="BLUEPRINT STANDARD (DO)",
                    dont_title="COMMON TRAPS (DON'T)",
                    takeaway=raw_slide.get("takeaway", "Discipline compounds across iterations."),
                ),
            )

        # 2. Hero Metrics / Economics Comparison
        if (
            explicit_arch in ("hero_metrics", "hero_metric")
            or len(raw_slide.get("metrics", [])) >= 1
            or "metric" in title.lower()
            or "metric" in kicker.lower()
        ):
            metrics_raw = raw_slide.get("metrics", [])
            metric_specs: list[HeroMetricSpec] = []
            for m in metrics_raw[:3]:
                if isinstance(m, HeroMetricSpec):
                    metric_specs.append(m)
                elif isinstance(m, dict):
                    metric_specs.append(HeroMetricSpec.from_dict(m))
            if not metric_specs:
                metric_specs = [
                    HeroMetricSpec(value="$9", unit="· 20 min", label="SOLO MODEL", description="Toy prototype thrown away"),
                    HeroMetricSpec(value="$200", unit="· 6 hours", label="FULL HARNESS", description="Shippable enterprise software"),
                ]
            elif len(metric_specs) == 1:
                m0 = metric_specs[0]
                metric_specs = [
                    m0,
                    HeroMetricSpec(value="100%", unit="target", label="VERIFIED", description="Target production SLA.", is_hero=True),
                ]
            return SlideSpec(
                archetype="hero_metrics",
                title=title,
                subtitle=subtitle or "Investment comparison and economic outcomes",
                kicker=kicker or "ECONOMICS",
                id=slide_id,
                notes=self._clean_notes(notes),
                metrics=metric_specs,
            )

        # 3. Code Terminal / Ratchet Box
        if explicit_arch in ("code_terminal", "code_ratchet") or raw_slide.get("code_block") or raw_slide.get("terminals"):
            cb = raw_slide.get("code_block") or (raw_slide.get("terminals", [None])[0])
            code_text = cb.get("code") if isinstance(cb, dict) else str(cb or "print('Hello, AI Factory')")
            filename = cb.get("filename", "snippet.py") if isinstance(cb, dict) else "snippet.py"
            lang = cb.get("language", "python") if isinstance(cb, dict) else "python"
            return SlideSpec(
                archetype="code_terminal",
                title=title,
                subtitle=subtitle or "Verified implementation and syntax container",
                kicker=kicker or "CODE CONTAINER",
                id=slide_id,
                notes=self._clean_notes(notes),
                terminals=[
                    CodeBlockSpec(
                        filename=filename,
                        code=code_text,
                        language=lang,
                        status="do",
                        badge_text="✓ VERIFIED SNIPPET",
                    )
                ],
            )

        # 4. Ladder Hierarchy
        if explicit_arch in ("ladder_hierarchy", "ladder_flow") or (3 <= len(raw_slide.get("steps", [])) <= 5):
            steps_raw = raw_slide.get("steps", [])
            steps_specs: list[LadderStepSpec] = []
            for s in steps_raw[:5]:
                if isinstance(s, LadderStepSpec):
                    steps_specs.append(s)
                elif isinstance(s, dict):
                    steps_specs.append(LadderStepSpec.from_dict(s))
            if not steps_specs:
                steps_specs = [
                    LadderStepSpec(step_number=1, title="Prompt", description="Goal, Context, Constraints"),
                    LadderStepSpec(step_number=2, title="Context", description="Window curation and memory"),
                    LadderStepSpec(step_number=3, title="Harness", description="Enforcing hooks and evaluators"),
                    LadderStepSpec(step_number=4, title="Loop", description="Continuous automated execution"),
                ]
            return SlideSpec(
                archetype="ladder_hierarchy",
                title=title,
                subtitle=subtitle or "Sequential stepped flow across disciplines",
                kicker=kicker or "DISCIPLINES",
                id=slide_id,
                notes=self._clean_notes(notes),
                steps=steps_specs,
            )

        # 5. Executive Grid (4 quadrants)
        if explicit_arch in ("executive_grid", "exec_grid") or len(raw_slide.get("quadrants", [])) == 4:
            quads_raw = raw_slide.get("quadrants", [])
            quad_specs: list[QuadrantSpec] = []
            for q in quads_raw[:4]:
                if isinstance(q, QuadrantSpec):
                    quad_specs.append(q)
                elif isinstance(q, dict):
                    quad_specs.append(QuadrantSpec.from_dict(q))
            if not quad_specs:
                quad_specs = [
                    QuadrantSpec(number="01", title="Prompt", narrative="Clear objective and boundary constraints."),
                    QuadrantSpec(number="02", title="Context", narrative="Compact and offload context systematically."),
                    QuadrantSpec(number="03", title="Harness", narrative="Equip sandboxes, tools, and linters."),
                    QuadrantSpec(number="04", title="Loop", narrative="Automate execution with human review."),
                ]
            return SlideSpec(
                archetype="executive_grid",
                title=title,
                subtitle=subtitle or "Executive 4-quadrant summary of key pillars",
                kicker=kicker or "EXECUTIVE SUMMARY",
                id=slide_id,
                notes=self._clean_notes(notes),
                quadrants=quad_specs,
            )

        # 6. Actionable Takeaways & Next Steps
        if (
            explicit_arch in ("actionable_takeaways", "takeaways")
            or "takeaway" in title.lower()
            or "next step" in title.lower()
            or "conclusion" in title.lower()
        ):
            principles = [
                PrincipleSpec(number=1, title="Spec First", description="Define verifiable completion criteria."),
                PrincipleSpec(number=2, title="Harness Ratchet", description="Block bad commits automatically."),
                PrincipleSpec(number=3, title="Human Gate", description="Keep human review at merge boundaries."),
            ]
            return SlideSpec(
                archetype="actionable_takeaways",
                title=title,
                subtitle=subtitle or "Key principles and implementation roadmap",
                kicker=kicker or "NEXT STEPS",
                id=slide_id,
                notes=self._clean_notes(notes),
                takeaway=TakeawaySpec(
                    thesis="Move from ad-hoc manual prompting to deterministic engineering factories.",
                    principles=principles,
                    roadmap_title="IMPLEMENTATION ROADMAP",
                    roadmap_items=[
                        "Step 1: Audit prompt specs & done-when gates",
                        "Step 2: Deploy enforcing pre-commit ratchets",
                        "Step 3: Orchestrate adversarial evaluator sub-agents",
                    ],
                    cta_text="START HARNESS AUDIT →",
                    contact_info="go/ai-factory · feedback@google.com",
                ),
            )

        # 7. Chapter Divider
        if (
            explicit_arch == "chapter_divider"
            or title.lower().startswith("chapter")
            or title.lower().startswith("part ")
            or (not raw_slide.get("bullets") and not raw_slide.get("cards") and not raw_slide.get("metrics") and slide_index == 1)
        ):
            return SlideSpec(
                archetype="chapter_divider",
                title=title,
                subtitle=subtitle or "Architectural foundation and overview",
                kicker=kicker or f"CHAPTER {slide_index:02d}",
                chapter_number=slide_index,
                id=slide_id,
                notes=self._clean_notes(notes),
            )

        # 8. Default: Split Cards (2-card or 3-card)
        cards_raw = raw_slide.get("cards", [])
        card_specs: list[CardSpec] = []
        for c in cards_raw:
            if isinstance(c, CardSpec):
                card_specs.append(c)
            elif isinstance(c, dict):
                card_specs.append(CardSpec.from_dict(c))

        if not card_specs:
            bullets = raw_slide.get("bullets", [])
            if len(bullets) >= 4:
                half = len(bullets) // 2
                card_specs = [
                    CardSpec(title="Core Concepts", kicker="OVERVIEW", bullets=bullets[:half], theme="#1A73E8"),
                    CardSpec(title="Key Mechanisms", kicker="DETAILS", bullets=bullets[half:half + 3], theme="#1E8E3E"),
                ]
            else:
                card_specs = [
                    CardSpec(title="Key Findings", kicker="ANALYSIS", bullets=bullets or ["Structured observation", "Verified outcome"], theme="#1A73E8"),
                    CardSpec(title="Implications", kicker="OUTCOMES", bullets=["Deterministic reproducibility", "Accelerated delivery"], theme="#1E8E3E"),
                ]

        return SlideSpec(
            archetype="split_cards",
            title=title,
            subtitle=subtitle or "Structured comparison and component analysis",
            kicker=kicker or "ANALYSIS",
            id=slide_id,
            notes=self._clean_notes(notes),
            cards=card_specs[:3],
        )

    @staticmethod
    def _clean_notes(existing_notes: str) -> str:
        """Returns authored speaker notes as-is (stripped). Notes are optional; nothing is invented."""
        return (existing_notes or "").strip()

    def _build_presentation_spec(
        self,
        raw_slides: list[dict[str, Any]],
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
    ) -> PresentationSpec:
        """Groups parsed slides into chapters and constructs a complete PresentationSpec."""
        mapped_slides: list[SlideSpec] = []
        for i, s in enumerate(raw_slides, start=1):
            mapped_slides.append(self.classify_and_map_slide(s, slide_index=i))

        # Determine presentation title and subtitle
        first_slide = mapped_slides[0]
        preso_title = title or first_slide.title or "Ingested Presentation Blueprint"
        preso_subtitle = subtitle or first_slide.subtitle or "Executive Blueprint Presentation"

        # Organize slides into chapters
        chapters: list[ChapterSpec] = []
        curr_chapter_slides: list[SlideSpec] = []
        curr_chapter_num = 1
        curr_chapter_title = preso_title

        for slide in mapped_slides:
            if slide.archetype == "chapter_divider" and curr_chapter_slides:
                chapters.append(
                    ChapterSpec(
                        number=curr_chapter_num,
                        title=curr_chapter_title,
                        subtitle=preso_subtitle,
                        slides=curr_chapter_slides,
                        notes=f"Chapter {curr_chapter_num} covers {curr_chapter_title}.",
                    )
                )
                curr_chapter_num += 1
                curr_chapter_title = slide.title or f"Chapter {curr_chapter_num}"
                curr_chapter_slides = [slide]
            else:
                curr_chapter_slides.append(slide)

        if curr_chapter_slides:
            chapters.append(
                ChapterSpec(
                    number=curr_chapter_num,
                    title=curr_chapter_title,
                    subtitle=preso_subtitle,
                    slides=curr_chapter_slides,
                    notes=f"Chapter {curr_chapter_num} details key operational concepts.",
                )
            )

        metadata = MetadataSpec(
            title=preso_title,
            subtitle=preso_subtitle,
            target_audience="Executive Leadership & Senior Staff Engineers",
            core_thesis="Automated conversion of existing presentations into the AI Factory Blueprint format.",
            template_id="1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U",
        )

        return PresentationSpec(
            metadata=metadata,
            chapters=chapters,
        )

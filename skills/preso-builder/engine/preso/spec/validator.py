"""Specification Validator and Text Budget Enforcer for preso_spec.yaml manifests.

Enforces structural validity, archetype constraints, text-budgeting bounds,
cardinality rules, and layout lints across all Blueprint slide archetypes.
Speaker notes are optional and are not validated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
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
    PrincipleSpec,
    QuadrantSpec,
    SlideSpec,
    TakeawaySpec,
    SLIDE_TIERS,
)


# =============================================================================
# Constants & Character Budgets
# =============================================================================

# Hard text character budget limits to guarantee zero truncation in 720x405pt canvas.
# These are coarse per-field caps; the geometry-aware pass (`validate(..., geometry=True)`
# / `preso budgets`) is the authoritative fit check for a given layout.
BUDGET_SLIDE_TITLE = 60
BUDGET_SLIDE_SUBTITLE = 120
BUDGET_KICKER = 30
BUDGET_CARD_TITLE = 35
BUDGET_CARD_BULLET = 90
BUDGET_MAX_BULLETS = 4
BUDGET_CODE_MAX_LINES = 16
BUDGET_CODE_MAX_LINE_WIDTH = 60
BUDGET_HERO_STAT = 12
BUDGET_HERO_DESC = 100
BUDGET_HERO_LABEL = 30
BUDGET_LADDER_TITLE = 35
BUDGET_LADDER_DESC = 100
BUDGET_QUADRANT_TITLE = 35
BUDGET_QUADRANT_NARRATIVE = 120
BUDGET_CHECKLIST_ITEM = 90
BUDGET_PRINCIPLE_TITLE = 40
BUDGET_PRINCIPLE_DESC = 100
BUDGET_ROADMAP_ITEM = 60
BUDGET_CTA_TEXT = 40
BUDGET_WATCH_FOR_ITEM = 28
BUDGET_WATCH_FOR_MAX = 3
BUDGET_IMAGE_CAPTION = 90
MIN_ASSERTION_SUBTITLE_WORDS = 4
MAX_CONSECUTIVE_SAME_ARCHETYPE = 2

# Archetypes that intentionally carry no assertion subtitle.
SUBTITLE_EXEMPT_ARCHETYPES = {"chapter_divider", "demo_pivot"}

# Leftover research/LLM citation markers that must never reach a slide.
CITATION_ARTIFACT_RE = re.compile(
    r"\[cite[^\]]*\]|\[\d+(?:,\s*\d+)*\]|\[source[^\]]*\]|\[ref[^\]]*\]|\(see doc\)|【\d+[^】]*】",
    re.IGNORECASE,
)

CANONICAL_ARCHETYPES = {
    "chapter_divider",
    "split_cards",
    "code_terminal",
    "hero_metrics",
    "ladder_hierarchy",
    "executive_grid",
    "dodont_checklist",
    "actionable_takeaways",
    "demo_pivot",
    "image_split",
}

ARCHETYPE_ALIASES = {
    "split_comparison": "split_cards",
    "code_ratchet": "code_terminal",
    "hero_metric": "hero_metrics",
    "ladder_flow": "ladder_hierarchy",
    "ladder": "ladder_hierarchy",
    "exec_grid": "executive_grid",
    "takeaways": "actionable_takeaways",
    "demo": "demo_pivot",
    "image": "image_split",
    "diagram": "image_split",
}


# =============================================================================
# Validation Result Model
# =============================================================================


@dataclass
class ValidationResult:
    """Represents the outcome of a specification validation pass."""

    is_valid: bool = True
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        """Returns True if the spec is completely valid (zero errors)."""
        return self.is_valid

    def add_error(self, message: str) -> None:
        """Appends an error and marks result invalid."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Appends a warning without marking invalid."""
        self.warnings.append(message)

    def merge(self, other: ValidationResult) -> None:
        """Combines another validation result into this one."""
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        if other.errors:
            self.is_valid = False

    def summary(self) -> str:
        """Generates a human-readable validation summary."""
        lines = []
        if self.is_valid:
            lines.append("✓ Specification is VALID (0 errors)")
        else:
            lines.append(f"✗ Specification is INVALID ({len(self.errors)} error(s))")

        if self.errors:
            lines.append("\nErrors:")
            for err in self.errors:
                lines.append(f"  - ✗ {err}")

        if self.warnings:
            lines.append("\nWarnings:")
            for warn in self.warnings:
                lines.append(f"  - ⚠ {warn}")

        return "\n".join(lines)


# =============================================================================
# Specification Validator Engine
# =============================================================================


class SpecValidator:
    """Enforces Blueprint design system constraints on presentation specifications."""

    @classmethod
    def normalize_archetype(cls, archetype: str) -> str:
        """Normalizes an archetype string, resolving aliases."""
        clean = archetype.strip().lower().replace("-", "_")
        return ARCHETYPE_ALIASES.get(clean, clean)

    @classmethod
    def validate(
        cls,
        spec: Union[PresentationSpec, dict[str, Any], str, Path],
        strict: bool = True,
        raise_on_error: bool = False,
        geometry: bool = False,
    ) -> ValidationResult:
        """Validates a presentation specification across all chapters and slides.

        Args:
            spec: PresentationSpec object, dictionary, YAML filepath, or YAML string.
            strict: If True, flags budget overruns as hard errors; otherwise as warnings.
            raise_on_error: If True, raises ValueError on first validation failure.
            geometry: If True, compiles the spec and adds layout-aware text-fit
                warnings ("cut ~N chars") from the shared text_fit heuristic.

        Returns:
            ValidationResult with list of errors and warnings.

        Raises:
            ValueError: If raise_on_error is True and validation fails.
        """
        result = ValidationResult()

        # Parse spec if provided as string, path, or dict
        parsed_spec: PresentationSpec
        if isinstance(spec, PresentationSpec):
            parsed_spec = spec
        elif isinstance(spec, (str, Path)):
            try:
                parsed_spec = PresentationSpec.from_yaml(spec)
            except Exception as e:
                result.add_error(f"Failed to parse YAML specification: {e}")
                if raise_on_error:
                    raise ValueError(result.summary()) from e
                return result
        elif isinstance(spec, dict):
            try:
                parsed_spec = PresentationSpec.from_dict(spec)
            except Exception as e:
                result.add_error(f"Failed to parse dictionary specification: {e}")
                if raise_on_error:
                    raise ValueError(result.summary()) from e
                return result
        else:
            result.add_error(f"Unsupported specification type: {type(spec)}")
            return result

        # 1. Validate Presentation-Level Structure
        cls._validate_presentation_level(parsed_spec, result, strict=strict)

        # 2. Validate Chapters and Slides
        slide_counter = 0
        for ch_idx, chapter in enumerate(parsed_spec.chapters, start=1):
            cls._validate_chapter(chapter, ch_idx, result, strict=strict)
            for s_idx, slide in enumerate(chapter.slides, start=1):
                slide_counter += 1
                slide_res = cls.validate_slide(slide, slide_index=slide_counter, strict=strict)
                result.merge(slide_res)

        if slide_counter == 0:
            result.add_error("Presentation contains zero slides. At least 1 slide is required.")

        # 3. Deck-level rhythm: avoid long runs of the same layout.
        cls._validate_layout_variety(parsed_spec, result)

        # 4. Optional geometry-aware fit pass on the compiled operations.
        if geometry and result.is_valid:
            for warning in cls.geometry_fit_warnings(parsed_spec):
                result.add_warning(warning)

        if raise_on_error and not result.is_valid:
            raise ValueError(result.summary())

        return result

    @classmethod
    def _validate_layout_variety(cls, spec: PresentationSpec, result: ValidationResult) -> None:
        """Warns when more than MAX_CONSECUTIVE_SAME_ARCHETYPE slides in a row share a layout.

        Auto-inserted chapter dividers (include_divider without an explicit divider slide)
        break a run, mirroring what the compiler will actually render.
        """
        sequence: list[tuple[str, str]] = []  # (archetype, title)
        for chapter in spec.chapters:
            has_explicit_divider = any(
                cls.normalize_archetype(s.archetype or "") == "chapter_divider" for s in chapter.slides
            )
            if getattr(chapter, "include_divider", True) and not has_explicit_divider:
                sequence.append(("chapter_divider", chapter.title))
            for s in chapter.slides:
                if getattr(s, "skip", False):
                    continue
                sequence.append((cls.normalize_archetype(s.archetype or ""), s.title))

        run_arch, run_titles = "", []  # type: str, list[str]
        for arch, title in sequence + [("__end__", "")]:
            if arch == run_arch:
                run_titles.append(title)
                continue
            if len(run_titles) > MAX_CONSECUTIVE_SAME_ARCHETYPE and run_arch not in ("chapter_divider", "__end__"):
                result.add_warning(
                    f"{len(run_titles)} consecutive '{run_arch}' slides "
                    f"('{run_titles[0][:30]}' … '{run_titles[-1][:30]}'). Vary the layout "
                    f"(e.g. hero_metrics, ladder_hierarchy, image_split) to keep rhythm."
                )
            run_arch, run_titles = arch, [title]

    @classmethod
    def geometry_fit_warnings(cls, spec: PresentationSpec) -> list[str]:
        """Compiles the spec and runs the shared text-fit heuristic on every textbox.

        Returns human-readable warnings that include the approximate number of
        characters to cut, so authors can fix overflow before building.
        """
        # Lazy imports keep the validator free of compiler/QA import cycles.
        from preso.compiler.batch_generator import BatchCompiler  # pylint: disable=g-import-not-at-top
        from preso.qa.verifier import QAVerifier  # pylint: disable=g-import-not-at-top

        try:
            ops = BatchCompiler().compile(spec).operations
        except Exception as e:  # pylint: disable=broad-except
            return [f"Geometry fit check skipped (compile failed: {e})."]
        _viols, warns, _metrics, _records = QAVerifier().verify_text_overflow(ops)
        out = []
        for w in warns:
            msg = str(w.get("message", ""))
            out.append(msg.replace("Potential text overflow", "Geometry fit", 1).replace(
                "on Slide", "on deck slide", 1))
        return out

    @classmethod
    def _validate_presentation_level(
        cls,
        spec: PresentationSpec,
        result: ValidationResult,
        strict: bool = True,
    ) -> None:
        """Validates presentation metadata and chapter counts."""
        if not spec.chapters:
            result.add_error("Presentation contains zero chapters. At least 1 chapter is required.")

        meta = spec.metadata
        if meta.title and len(meta.title) > BUDGET_SLIDE_TITLE:
            msg = f"Metadata title exceeds {BUDGET_SLIDE_TITLE} character budget ({len(meta.title)} chars): '{meta.title[:30]}...'"
            if strict:
                result.add_error(msg)
            else:
                result.add_warning(msg)

        if meta.subtitle and len(meta.subtitle) > BUDGET_SLIDE_SUBTITLE:
            msg = f"Metadata subtitle exceeds {BUDGET_SLIDE_SUBTITLE} character budget ({len(meta.subtitle)} chars)"
            if strict:
                result.add_error(msg)
            else:
                result.add_warning(msg)

    @classmethod
    def _validate_chapter(
        cls,
        chapter: ChapterSpec,
        chapter_index: int,
        result: ValidationResult,
        strict: bool = True,
    ) -> None:
        """Validates a chapter specification."""
        if not chapter.slides:
            result.add_warning(f"Chapter {chapter_index} ('{chapter.title}') has no slides.")

        if chapter.title and len(chapter.title) > BUDGET_SLIDE_TITLE:
            msg = f"Chapter {chapter_index} title exceeds {BUDGET_SLIDE_TITLE} character budget ({len(chapter.title)} chars)"
            if strict:
                result.add_error(msg)
            else:
                result.add_warning(msg)

    @classmethod
    def validate_slide(
        cls,
        slide: Union[SlideSpec, dict[str, Any]],
        slide_index: int = 1,
        strict: bool = True,
    ) -> ValidationResult:
        """Validates a single slide specification against its archetype rules.

        Args:
            slide: SlideSpec object or dictionary.
            slide_index: 1-based slide index.
            strict: If True, flags budget overruns as hard errors.

        Returns:
            ValidationResult for this slide.
        """
        result = ValidationResult()

        parsed: SlideSpec
        if isinstance(slide, SlideSpec):
            parsed = slide
        elif isinstance(slide, dict):
            try:
                parsed = SlideSpec.from_dict(slide)
            except Exception as e:
                result.add_error(f"Slide {slide_index} malformed: {e}")
                return result
        else:
            result.add_error(f"Slide {slide_index} invalid type: {type(slide)}")
            return result

        # 1. Archetype Enum Check
        raw_arch = parsed.archetype or ""
        normalized_arch = cls.normalize_archetype(raw_arch)
        if not raw_arch:
            result.add_error(f"Slide {slide_index} is missing required 'archetype' field.")
            return result

        if normalized_arch not in CANONICAL_ARCHETYPES:
            result.add_error(
                f"Slide {slide_index} has unknown archetype '{raw_arch}'. "
                f"Supported archetypes: {sorted(list(CANONICAL_ARCHETYPES))}"
            )
            return result

        # 2. Universal Header Text Budgets
        if parsed.title and len(parsed.title) > BUDGET_SLIDE_TITLE:
            msg = (
                f"Slide {slide_index} ({normalized_arch}) title exceeds {BUDGET_SLIDE_TITLE} "
                f"character budget ({len(parsed.title)} chars): '{parsed.title[:35]}...'"
            )
            if strict:
                result.add_error(msg)
            else:
                result.add_warning(msg)

        if parsed.subtitle and len(parsed.subtitle) > BUDGET_SLIDE_SUBTITLE:
            msg = (
                f"Slide {slide_index} ({normalized_arch}) subtitle exceeds {BUDGET_SLIDE_SUBTITLE} "
                f"character budget ({len(parsed.subtitle)} chars): '{parsed.subtitle[:45]}...'"
            )
            if strict:
                result.add_error(msg)
            else:
                result.add_warning(msg)

        if parsed.kicker and len(parsed.kicker) > BUDGET_KICKER:
            msg = (
                f"Slide {slide_index} ({normalized_arch}) kicker exceeds {BUDGET_KICKER} "
                f"character budget ({len(parsed.kicker)} chars): '{parsed.kicker}'"
            )
            if strict:
                result.add_error(msg)
            else:
                result.add_warning(msg)

        # 3. Tier / visibility (speaker notes are optional and never validated)
        tier = (getattr(parsed, "tier", "") or "core").strip().lower()
        if tier not in SLIDE_TIERS:
            result.add_error(
                f"Slide {slide_index} ({normalized_arch}) has unknown tier '{tier}'. "
                f"Supported tiers: {list(SLIDE_TIERS)}"
            )

        # 5. Assertion subtitle: the subtitle carries the one-sentence takeaway.
        if normalized_arch not in SUBTITLE_EXEMPT_ARCHETYPES:
            words = len((parsed.subtitle or "").split())
            if words < MIN_ASSERTION_SUBTITLE_WORDS:
                result.add_warning(
                    f"Slide {slide_index} ({normalized_arch}) '{parsed.title[:30]}': subtitle should state "
                    f"the slide's takeaway as a full sentence (≥{MIN_ASSERTION_SUBTITLE_WORDS} words), "
                    f"not a topic label."
                )

        # 6. Citation / research artifacts leaking into visible text
        for field_path, text in cls._visible_text_fields(parsed):
            match = CITATION_ARTIFACT_RE.search(text)
            if match:
                result.add_warning(
                    f"Slide {slide_index} ({normalized_arch}) {field_path} contains citation artifact "
                    f"'{match.group(0)}'. Remove it before building."
                )

        # 7. Archetype-Specific Constraint Validations
        if normalized_arch == "chapter_divider":
            cls._validate_chapter_divider(parsed, slide_index, result, strict)
        elif normalized_arch == "split_cards":
            cls._validate_split_cards(parsed, slide_index, result, strict)
        elif normalized_arch == "code_terminal":
            cls._validate_code_terminal(parsed, slide_index, result, strict)
        elif normalized_arch == "hero_metrics":
            cls._validate_hero_metrics(parsed, slide_index, result, strict)
        elif normalized_arch == "ladder_hierarchy":
            cls._validate_ladder_hierarchy(parsed, slide_index, result, strict)
        elif normalized_arch == "executive_grid":
            cls._validate_executive_grid(parsed, slide_index, result, strict)
        elif normalized_arch == "dodont_checklist":
            cls._validate_dodont_checklist(parsed, slide_index, result, strict)
        elif normalized_arch == "actionable_takeaways":
            cls._validate_actionable_takeaways(parsed, slide_index, result, strict)
        elif normalized_arch == "demo_pivot":
            cls._validate_demo_pivot(parsed, slide_index, result, strict)
        elif normalized_arch == "image_split":
            cls._validate_image_split(parsed, slide_index, result, strict)

        return result

    @classmethod
    def _visible_text_fields(cls, slide: SlideSpec) -> list[tuple[str, str]]:
        """Flattens on-slide text (excluding notes and code) into (path, text) pairs."""
        skip_keys = {"notes", "speaker_notes", "code", "terminals", "code_blocks", "code_box",
                     "id", "archetype", "image", "path", "url", "tier", "skip"}
        out: list[tuple[str, str]] = []

        def walk(node: Any, path: str) -> None:
            if isinstance(node, str):
                out.append((path, node))
            elif isinstance(node, dict):
                for k, v in node.items():
                    if k not in skip_keys:
                        walk(v, f"{path}.{k}" if path else str(k))
            elif isinstance(node, (list, tuple)):
                for i, v in enumerate(node):
                    walk(v, f"{path}[{i}]")

        try:
            walk(slide.to_dict(), "")
        except Exception:  # pylint: disable=broad-except
            pass
        return out

    # -------------------------------------------------------------------------
    # Archetype Constraint Checkers
    # -------------------------------------------------------------------------

    @classmethod
    def _validate_chapter_divider(
        cls, slide: SlideSpec, idx: int, result: ValidationResult, strict: bool
    ) -> None:
        if not slide.title and not slide.chapter_number:
            result.add_error(f"Slide {idx} (chapter_divider) must specify a title or chapter_number.")

    @classmethod
    def _validate_split_cards(
        cls, slide: SlideSpec, idx: int, result: ValidationResult, strict: bool
    ) -> None:
        cards = slide.cards
        if not cards:
            result.add_error(f"Slide {idx} (split_cards) requires cards, but none were provided.")
            return

        if len(cards) < 2 or len(cards) > 3:
            msg = f"Slide {idx} (split_cards) standard Blueprint layout uses 2 or 3 cards, found {len(cards)}."
            if len(cards) > 4 or len(cards) < 1:
                result.add_error(msg)
            else:
                result.add_warning(msg)

        for c_idx, card in enumerate(cards, start=1):
            c_title = card.title if isinstance(card, CardSpec) else str(card.get("title", card.get("header", "")))
            if c_title and len(c_title) > BUDGET_CARD_TITLE:
                msg = f"Slide {idx} Card {c_idx} header exceeds {BUDGET_CARD_TITLE} chars ({len(c_title)} chars): '{c_title}'"
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

            bullets = card.bullets if isinstance(card, CardSpec) else card.get("bullets", [])
            if isinstance(bullets, str):
                bullets = [b.strip() for b in bullets.splitlines() if b.strip()]

            if len(bullets) > BUDGET_MAX_BULLETS:
                msg = f"Slide {idx} Card {c_idx} has {len(bullets)} bullets (recommended max {BUDGET_MAX_BULLETS})."
                result.add_warning(msg)

            for b_idx, bullet in enumerate(bullets, start=1):
                clean_b = bullet.lstrip("•-* ").strip()
                if len(clean_b) > BUDGET_CARD_BULLET:
                    msg = (
                        f"Slide {idx} Card {c_idx} Bullet {b_idx} exceeds {BUDGET_CARD_BULLET} chars "
                        f"({len(clean_b)} chars): '{clean_b[:35]}...'"
                    )
                    if strict:
                        result.add_error(msg)
                    else:
                        result.add_warning(msg)

    @classmethod
    def _validate_code_terminal(
        cls, slide: SlideSpec, idx: int, result: ValidationResult, strict: bool
    ) -> None:
        terminals = slide.terminals
        if not terminals:
            result.add_error(f"Slide {idx} (code_terminal) requires at least 1 terminal/code block.")
            return

        if len(terminals) > 2:
            result.add_error(f"Slide {idx} (code_terminal) supports maximum 2 terminal boxes, found {len(terminals)}.")

        for t_idx, term in enumerate(terminals, start=1):
            filename = term.filename if isinstance(term, CodeBlockSpec) else str(term.get("filename", ""))
            code = term.code if isinstance(term, CodeBlockSpec) else str(term.get("code", ""))

            code_lines = [l for l in code.splitlines() if l.strip()]
            if len(code_lines) > BUDGET_CODE_MAX_LINES:
                msg = (
                    f"Slide {idx} Terminal {t_idx} ('{filename}') code exceeds {BUDGET_CODE_MAX_LINES} "
                    f"lines ({len(code_lines)} lines). Truncate snippet to prevent slide overflow."
                )
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

            for line_no, line in enumerate(code.splitlines(), start=1):
                if len(line) > BUDGET_CODE_MAX_LINE_WIDTH:
                    result.add_warning(
                        f"Slide {idx} Terminal {t_idx} ('{filename}') line {line_no} is wide "
                        f"({len(line)} chars > {BUDGET_CODE_MAX_LINE_WIDTH}). May soft-wrap in presentation."
                    )

    @classmethod
    def _validate_hero_metrics(
        cls, slide: SlideSpec, idx: int, result: ValidationResult, strict: bool
    ) -> None:
        metrics = slide.metrics
        if not metrics:
            result.add_error(f"Slide {idx} (hero_metrics) requires at least 1 metric callout.")
            return

        if len(metrics) > 4:
            result.add_error(f"Slide {idx} (hero_metrics) supports maximum 4 metric callouts, found {len(metrics)}.")

        for m_idx, m in enumerate(metrics, start=1):
            val = m.value if isinstance(m, HeroMetricSpec) else str(m.get("value", m.get("stat", "")))
            desc = m.description if isinstance(m, HeroMetricSpec) else str(m.get("description", m.get("context", "")))
            label = m.label if isinstance(m, HeroMetricSpec) else str(m.get("label", ""))

            if not val:
                result.add_error(f"Slide {idx} Metric {m_idx} is missing a stat value.")

            if val and len(val) > BUDGET_HERO_STAT:
                msg = f"Slide {idx} Metric {m_idx} stat '{val}' exceeds {BUDGET_HERO_STAT} chars ({len(val)} chars)."
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

            if desc and len(desc) > BUDGET_HERO_DESC:
                msg = f"Slide {idx} Metric {m_idx} context description exceeds {BUDGET_HERO_DESC} chars ({len(desc)} chars)."
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

            if label and len(label) > BUDGET_HERO_LABEL:
                msg = f"Slide {idx} Metric {m_idx} label exceeds {BUDGET_HERO_LABEL} chars ({len(label)} chars)."
                result.add_warning(msg)

    @classmethod
    def _validate_ladder_hierarchy(
        cls, slide: SlideSpec, idx: int, result: ValidationResult, strict: bool
    ) -> None:
        steps = slide.steps
        if not steps:
            result.add_error(f"Slide {idx} (ladder_hierarchy) requires steps, but none were provided.")
            return

        if len(steps) < 3 or len(steps) > 5:
            result.add_error(f"Slide {idx} (ladder_hierarchy) requires 3 to 5 steps, found {len(steps)}.")

        for s_idx, step in enumerate(steps, start=1):
            title = step.title if isinstance(step, LadderStepSpec) else str(step.get("title", ""))
            desc = step.description if isinstance(step, LadderStepSpec) else str(step.get("description", ""))

            if not title:
                result.add_error(f"Slide {idx} Step {s_idx} is missing a title.")

            if title and len(title) > BUDGET_LADDER_TITLE:
                msg = f"Slide {idx} Step {s_idx} title exceeds {BUDGET_LADDER_TITLE} chars ({len(title)} chars): '{title}'"
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

            if desc and len(desc) > BUDGET_LADDER_DESC:
                msg = f"Slide {idx} Step {s_idx} description exceeds {BUDGET_LADDER_DESC} chars ({len(desc)} chars)."
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

    @classmethod
    def _validate_executive_grid(
        cls, slide: SlideSpec, idx: int, result: ValidationResult, strict: bool
    ) -> None:
        quadrants = slide.quadrants
        if not quadrants:
            result.add_error(f"Slide {idx} (executive_grid) requires quadrants, but none were provided.")
            return

        if len(quadrants) != 4:
            result.add_error(f"Slide {idx} (executive_grid) requires exactly 4 quadrants (2x2), found {len(quadrants)}.")

        for q_idx, q in enumerate(quadrants, start=1):
            title = q.title if isinstance(q, QuadrantSpec) else str(q.get("title", ""))
            narrative = (
                q.narrative
                if isinstance(q, QuadrantSpec)
                else str(q.get("narrative", q.get("description", q.get("body", ""))))
            )

            if not title:
                result.add_error(f"Slide {idx} Quadrant {q_idx} is missing a title.")

            if title and len(title) > BUDGET_QUADRANT_TITLE:
                msg = f"Slide {idx} Quadrant {q_idx} title exceeds {BUDGET_QUADRANT_TITLE} chars ({len(title)} chars)."
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

            if narrative and len(narrative) > BUDGET_QUADRANT_NARRATIVE:
                msg = f"Slide {idx} Quadrant {q_idx} narrative exceeds {BUDGET_QUADRANT_NARRATIVE} chars ({len(narrative)} chars)."
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

    @classmethod
    def _validate_dodont_checklist(
        cls, slide: SlideSpec, idx: int, result: ValidationResult, strict: bool
    ) -> None:
        if slide.checklist:
            dont_items = slide.checklist.dont_items
            do_items = slide.checklist.do_items
        else:
            dont_items = slide.raw_content.get("dont_items", slide.raw_content.get("dont", []))
            do_items = slide.raw_content.get("do_items", slide.raw_content.get("do", []))

        if not dont_items or not do_items:
            result.add_error(
                f"Slide {idx} (dodont_checklist) requires at least 1 DO item and 1 DON'T item."
            )

        if len(dont_items) > 5:
            result.add_warning(f"Slide {idx} (dodont_checklist) DON'T column has > 5 items ({len(dont_items)}).")
        if len(do_items) > 5:
            result.add_warning(f"Slide {idx} (dodont_checklist) DO column has > 5 items ({len(do_items)}).")

        for item in dont_items:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            if len(text) > BUDGET_CHECKLIST_ITEM:
                msg = f"Slide {idx} DON'T item exceeds {BUDGET_CHECKLIST_ITEM} chars ({len(text)} chars): '{text[:35]}...'"
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

        for item in do_items:
            text = item.get("text", "") if isinstance(item, dict) else str(item)
            if len(text) > BUDGET_CHECKLIST_ITEM:
                msg = f"Slide {idx} DO item exceeds {BUDGET_CHECKLIST_ITEM} chars ({len(text)} chars): '{text[:35]}...'"
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

    @classmethod
    def _validate_actionable_takeaways(
        cls, slide: SlideSpec, idx: int, result: ValidationResult, strict: bool
    ) -> None:
        if slide.takeaway:
            principles = slide.takeaway.principles
            roadmap = slide.takeaway.roadmap_items
            cta = slide.takeaway.cta_text
        else:
            principles = slide.raw_content.get("principles", [])
            roadmap = slide.raw_content.get("roadmap_items", [])
            cta = slide.raw_content.get("cta_text", "")

        if not principles:
            result.add_error(f"Slide {idx} (actionable_takeaways) requires at least 1 action principle.")

        if len(principles) > 5:
            result.add_warning(f"Slide {idx} (actionable_takeaways) has > 5 principles ({len(principles)}).")

        for p_idx, p in enumerate(principles, start=1):
            if isinstance(p, PrincipleSpec):
                p_title, p_desc = p.title, p.description
            elif isinstance(p, dict):
                p_title = str(p.get("title", ""))
                p_desc = str(p.get("description", p.get("body", "")))
            else:
                p_title, p_desc = f"Principle {p_idx}", str(p)

            if p_title and len(p_title) > BUDGET_PRINCIPLE_TITLE:
                msg = f"Slide {idx} Principle {p_idx} title exceeds {BUDGET_PRINCIPLE_TITLE} chars ({len(p_title)} chars)."
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

            if p_desc and len(p_desc) > BUDGET_PRINCIPLE_DESC:
                msg = f"Slide {idx} Principle {p_idx} description exceeds {BUDGET_PRINCIPLE_DESC} chars ({len(p_desc)} chars)."
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

        if len(roadmap) > 5:
            result.add_warning(f"Slide {idx} (actionable_takeaways) roadmap has > 5 milestones ({len(roadmap)}).")

        for r_idx, r_item in enumerate(roadmap, start=1):
            r_text = str(r_item)
            if len(r_text) > BUDGET_ROADMAP_ITEM:
                msg = f"Slide {idx} Roadmap milestone {r_idx} exceeds {BUDGET_ROADMAP_ITEM} chars ({len(r_text)} chars)."
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

        if cta and len(cta) > BUDGET_CTA_TEXT:
            msg = f"Slide {idx} CTA text exceeds {BUDGET_CTA_TEXT} chars ({len(cta)} chars)."
            result.add_warning(msg)

    @classmethod
    def _validate_demo_pivot(
        cls, slide: SlideSpec, idx: int, result: ValidationResult, strict: bool
    ) -> None:
        if not slide.title:
            result.add_error(f"Slide {idx} (demo_pivot) must specify a title (what the demo shows).")
        watch_for = slide.raw_content.get("watch_for", []) or []
        if isinstance(watch_for, str):
            watch_for = [watch_for]
        if len(watch_for) > BUDGET_WATCH_FOR_MAX:
            result.add_warning(
                f"Slide {idx} (demo_pivot) has {len(watch_for)} watch_for items "
                f"(max {BUDGET_WATCH_FOR_MAX}); extra items are dropped."
            )
        for w_idx, item in enumerate(watch_for, start=1):
            if len(str(item)) > BUDGET_WATCH_FOR_ITEM:
                msg = (
                    f"Slide {idx} (demo_pivot) watch_for {w_idx} exceeds "
                    f"{BUDGET_WATCH_FOR_ITEM} chars ({len(str(item))} chars)."
                )
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

    @classmethod
    def _validate_image_split(
        cls, slide: SlideSpec, idx: int, result: ValidationResult, strict: bool
    ) -> None:
        image = slide.raw_content.get("image")
        if isinstance(image, str):
            image = {"path": image}
        if not isinstance(image, dict) or not (image.get("path") or image.get("url")):
            result.add_error(
                f"Slide {idx} (image_split) requires `image: {{path: ..., alt: ...}}` or `image: {{url: ...}}`."
            )
            return
        path = image.get("path")
        if path and not str(path).startswith(("http://", "https://")) and not Path(str(path)).expanduser().exists():
            result.add_warning(f"Slide {idx} (image_split) image path not found: {path}")
        if not image.get("alt"):
            result.add_warning(f"Slide {idx} (image_split) image has no `alt` text (used in audit + notes).")
        caption = str(image.get("caption", "") or "")
        if len(caption) > BUDGET_IMAGE_CAPTION:
            result.add_warning(
                f"Slide {idx} (image_split) caption exceeds {BUDGET_IMAGE_CAPTION} chars ({len(caption)})."
            )
        layout = str(slide.raw_content.get("image_layout", "split")).lower()
        if layout not in ("split", "full"):
            result.add_error(f"Slide {idx} (image_split) image_layout must be 'split' or 'full', got '{layout}'.")
        side = str(slide.raw_content.get("image_side", "right")).lower()
        if side not in ("left", "right"):
            result.add_error(f"Slide {idx} (image_split) image_side must be 'left' or 'right', got '{side}'.")
        bullets = slide.raw_content.get("bullets", []) or []
        if layout == "split" and len(bullets) > BUDGET_MAX_BULLETS:
            result.add_warning(
                f"Slide {idx} (image_split) has {len(bullets)} bullets (recommended max {BUDGET_MAX_BULLETS})."
            )
        for b_idx, b in enumerate(bullets, start=1):
            if len(str(b)) > BUDGET_CARD_BULLET:
                msg = f"Slide {idx} (image_split) bullet {b_idx} exceeds {BUDGET_CARD_BULLET} chars."
                if strict:
                    result.add_error(msg)
                else:
                    result.add_warning(msg)

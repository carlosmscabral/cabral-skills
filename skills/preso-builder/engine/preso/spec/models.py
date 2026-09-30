"""Data Models for Structured Blueprint Presentation Specifications (preso_spec.yaml).

Provides typed dataclasses, flexible dictionary normalization, and bi-directional
YAML/JSON serialization for presentation manifests conforming to the AI Factory
Blueprint layout system.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import io
import json
from pathlib import Path
from typing import Any, Optional, TextIO, Union

import yaml


# =============================================================================
# Helper Utilities
# =============================================================================

# Slide visibility tiers used to cut one master deck to a time budget.
# `appendix` slides are always kept in the deck but skipped in presentation mode.
SLIDE_TIERS: tuple[str, ...] = ("core", "explain", "detail", "appendix")
DEFAULT_TIER: str = "core"

# Which tiers stay visible for each `--duration` preset.
DURATION_VISIBLE_TIERS: dict[str, tuple[str, ...]] = {
    "5": ("core",),
    "15": ("core", "explain"),
    "45": ("core", "explain", "detail"),
    "full": ("core", "explain", "detail"),
}


def _clean_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Recursively removes None values and empty optional collections for clean export."""
    out: dict[str, Any] = {}
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, dict):
            cleaned = _clean_dict(v)
            if cleaned or k in ("metadata", "theme"):
                out[k] = cleaned
        elif isinstance(v, list):
            cleaned_list = []
            for item in v:
                if isinstance(item, dict):
                    cleaned_list.append(_clean_dict(item))
                else:
                    cleaned_list.append(item)
            out[k] = cleaned_list
        else:
            out[k] = v
    return out


# =============================================================================
# Sub-Specification Models
# =============================================================================


@dataclass
class MetadataSpec:
    """Metadata specification for presentation properties and styling."""

    title: str = ""
    subtitle: str = ""
    template_id: str = "1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U"
    target_audience: str = ""
    core_thesis: str = ""
    theme: dict[str, Any] = field(default_factory=dict)
    version: str = "1.0"

    def to_dict(self) -> dict[str, Any]:
        """Serializes metadata to dictionary."""
        d = {
            "title": self.title,
            "subtitle": self.subtitle,
            "template_id": self.template_id,
            "target_audience": self.target_audience,
            "core_thesis": self.core_thesis,
        }
        if self.theme:
            d["theme"] = self.theme
        if self.version != "1.0":
            d["version"] = self.version
        return d

    @classmethod
    def from_dict(cls, data: Optional[dict[str, Any]]) -> MetadataSpec:
        """Parses MetadataSpec from dictionary with backwards compatibility."""
        if not data or not isinstance(data, dict):
            return cls()
        return cls(
            title=str(data.get("title", "")),
            subtitle=str(data.get("subtitle", "")),
            template_id=str(data.get("template_id", "1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U")),
            target_audience=str(data.get("target_audience", "")),
            core_thesis=str(data.get("core_thesis", "")),
            theme=dict(data.get("theme", {})),
            version=str(data.get("version", "1.0")),
        )


@dataclass
class CardSpec:
    """Specification for a split comparison card (Archetype 2)."""

    title: str = ""
    kicker: str = ""
    bullets: list[str] = field(default_factory=list)
    theme: str = ""  # stripe_color or hex accent
    category: str = ""  # alias for kicker / category_pill

    def __post_init__(self) -> None:
        if not self.kicker and self.category:
            self.kicker = self.category
        if not self.category and self.kicker:
            self.category = self.kicker

    def to_dict(self) -> dict[str, Any]:
        """Serializes card to dictionary compatible with engine and spec."""
        d: dict[str, Any] = {
            "title": self.title,
            "category": self.kicker or self.category,
            "category_pill": self.kicker or self.category,
            "header": self.title,
            "bullets": list(self.bullets),
        }
        if self.theme:
            d["stripe_color"] = self.theme
            d["theme"] = self.theme
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CardSpec:
        """Parses CardSpec from dictionary handling multiple field aliases."""
        if not isinstance(data, dict):
            return cls()
        title = data.get("title") or data.get("header") or ""
        kicker = data.get("kicker") or data.get("category_pill") or data.get("category") or ""
        raw_bullets = data.get("bullets", [])
        if isinstance(raw_bullets, str):
            bullets = [b.strip() for b in raw_bullets.splitlines() if b.strip()]
        elif isinstance(raw_bullets, list):
            bullets = [str(b) for b in raw_bullets]
        else:
            bullets = []
        theme = data.get("theme") or data.get("stripe_color") or ""
        return cls(title=str(title), kicker=str(kicker), bullets=bullets, theme=str(theme), category=str(kicker))


@dataclass
class CodeBlockSpec:
    """Specification for a code/terminal container (Archetype 3)."""

    filename: str = "snippet.py"
    code: str = ""
    language: str = "python"
    status: str = "do"  # "do", "dont", "info", or custom badge
    badge_text: str = ""
    badge_color: str = ""
    badge_bg: str = ""

    def __post_init__(self) -> None:
        if not self.badge_text and self.status:
            if self.status.lower() in ("do", "valid", "good"):
                self.badge_text = "✓ DO"
            elif self.status.lower() in ("dont", "don't", "invalid", "bad"):
                self.badge_text = "✗ DON'T"

    def to_dict(self) -> dict[str, Any]:
        """Serializes code block to dictionary compatible with engine."""
        d: dict[str, Any] = {
            "filename": self.filename,
            "code": self.code,
            "language": self.language,
        }
        if self.badge_text:
            d["badge_text"] = self.badge_text
        if self.badge_color:
            d["badge_color"] = self.badge_color
        if self.badge_bg:
            d["badge_bg"] = self.badge_bg
        if self.status:
            d["status"] = self.status
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CodeBlockSpec:
        """Parses CodeBlockSpec from dictionary."""
        if not isinstance(data, dict):
            return cls()
        return cls(
            filename=str(data.get("filename", "snippet.py")),
            code=str(data.get("code", "")),
            language=str(data.get("language", "python")),
            status=str(data.get("status", "do")),
            badge_text=str(data.get("badge_text", "")),
            badge_color=str(data.get("badge_color", "")),
            badge_bg=str(data.get("badge_bg", "")),
        )


# Alias for compatibility with engine models
TerminalSpec = CodeBlockSpec


@dataclass
class HeroMetricSpec:
    """Specification for a hero metric / economics callout (Archetype 4)."""

    value: str = ""
    unit: str = ""
    label: str = ""
    delta: str = ""
    delta_type: str = "positive"  # "positive", "negative", "neutral"
    description: str = ""
    is_hero: bool = False
    accent_color: str = ""
    kicker: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serializes metric to dictionary compatible with engine."""
        d: dict[str, Any] = {
            "value": self.value,
            "stat": self.value,
            "unit": self.unit,
            "label": self.label,
            "description": self.description,
            "context": self.description,
        }
        if self.delta:
            d["delta"] = self.delta
            d["delta_type"] = self.delta_type
        if self.is_hero:
            d["is_hero"] = self.is_hero
        if self.accent_color:
            d["accent_color"] = self.accent_color
        if self.kicker:
            d["kicker"] = self.kicker
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HeroMetricSpec:
        """Parses HeroMetricSpec from dictionary."""
        if not isinstance(data, dict):
            return cls()
        val = data.get("value") or data.get("stat") or ""
        desc = data.get("description") or data.get("context") or ""
        return cls(
            value=str(val),
            unit=str(data.get("unit", "")),
            label=str(data.get("label", "")),
            delta=str(data.get("delta", "")),
            delta_type=str(data.get("delta_type", "positive")),
            description=str(desc),
            is_hero=bool(data.get("is_hero", False)),
            accent_color=str(data.get("accent_color", "")),
            kicker=str(data.get("kicker", "")),
        )


# Alias for compatibility with engine models
MetricSpec = HeroMetricSpec


@dataclass
class LadderStepSpec:
    """Specification for a ladder / stepped hierarchy rung (Archetype 5)."""

    step_number: Union[int, str] = 1
    title: str = ""
    description: str = ""
    badge_color: str = ""
    badge: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serializes ladder step to dictionary."""
        d: dict[str, Any] = {
            "step_number": self.step_number,
            "number": self.step_number,
            "title": self.title,
            "description": self.description,
        }
        if self.badge_color:
            d["badge_color"] = self.badge_color
        if self.badge:
            d["badge"] = self.badge
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LadderStepSpec:
        """Parses LadderStepSpec from dictionary."""
        if not isinstance(data, dict):
            return cls()
        num = data.get("step_number") if "step_number" in data else data.get("number", 1)
        return cls(
            step_number=num,
            title=str(data.get("title", "")),
            description=str(data.get("description", "")),
            badge_color=str(data.get("badge_color", "")),
            badge=str(data.get("badge", "")),
        )


# Alias for compatibility with engine models
StepSpec = LadderStepSpec


@dataclass
class QuadrantSpec:
    """Specification for a 2x2 executive summary quadrant (Archetype 6)."""

    number: Union[int, str] = "01"
    title: str = ""
    narrative: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serializes quadrant to dictionary."""
        return {
            "number": self.number,
            "title": self.title,
            "narrative": self.narrative,
            "description": self.narrative,
            "body": self.narrative,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> QuadrantSpec:
        """Parses QuadrantSpec from dictionary."""
        if not isinstance(data, dict):
            return cls()
        num = data.get("number", "01")
        title = data.get("title", "")
        narrative = data.get("narrative") or data.get("description") or data.get("body") or ""
        return cls(
            number=num,
            title=str(title),
            narrative=str(narrative),
        )


@dataclass
class ChecklistSpec:
    """Specification for a Do / Don't best practice checklist (Archetype 7)."""

    dont_items: list[str] = field(default_factory=list)
    do_items: list[str] = field(default_factory=list)
    dont_title: str = "ANTI-PATTERN (DON'T)"
    do_title: str = "BLUEPRINT STANDARD (DO)"
    takeaway: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serializes checklist to dictionary."""
        d: dict[str, Any] = {
            "dont_items": list(self.dont_items),
            "do_items": list(self.do_items),
            "dont": list(self.dont_items),
            "do": list(self.do_items),
            "dont_title": self.dont_title,
            "do_title": self.do_title,
        }
        if self.takeaway:
            d["takeaway"] = self.takeaway
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChecklistSpec:
        """Parses ChecklistSpec from dictionary."""
        if not isinstance(data, dict):
            return cls()
        dont_list = data.get("dont_items") or data.get("dont") or []
        if isinstance(dont_list, str):
            dont_list = [line.strip() for line in dont_list.splitlines() if line.strip()]
        elif isinstance(dont_list, list):
            dont_list = [str(item) for item in dont_list]

        do_list = data.get("do_items") or data.get("do") or []
        if isinstance(do_list, str):
            do_list = [line.strip() for line in do_list.splitlines() if line.strip()]
        elif isinstance(do_list, list):
            do_list = [str(item) for item in do_list]

        return cls(
            dont_items=dont_list,
            do_items=do_list,
            dont_title=str(data.get("dont_title") or data.get("dont_header") or "ANTI-PATTERN (DON'T)"),
            do_title=str(data.get("do_title") or data.get("do_header") or "BLUEPRINT STANDARD (DO)"),
            takeaway=str(data.get("takeaway", "")),
        )


@dataclass
class PrincipleSpec:
    """Specification for an actionable principle item (Archetype 8)."""

    number: Union[int, str] = 1
    title: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serializes principle to dictionary."""
        return {
            "number": self.number,
            "title": self.title,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Union[dict[str, Any], str], index: int = 1) -> PrincipleSpec:
        """Parses PrincipleSpec from string or dictionary."""
        if isinstance(data, str):
            # Parse possible "Title: Description" format or raw text
            if ":" in data:
                parts = data.split(":", 1)
                return cls(number=index, title=parts[0].strip(), description=parts[1].strip())
            return cls(number=index, title=f"Principle {index:02d}", description=data.strip())
        elif isinstance(data, dict):
            num = data.get("number", index)
            title = data.get("title", f"Principle {index:02d}")
            desc = data.get("description") or data.get("body") or data.get("text", "")
            return cls(number=num, title=str(title), description=str(desc))
        return cls(number=index, title=f"Principle {index:02d}", description=str(data))


@dataclass
class TakeawaySpec:
    """Specification for actionable takeaways & closing slide (Archetype 8)."""

    principles: list[Union[PrincipleSpec, dict[str, Any], str]] = field(default_factory=list)
    roadmap_title: str = "NEXT STEPS & ROADMAP"
    roadmap_items: list[str] = field(default_factory=list)
    cta_text: str = "EXECUTE BUILD NOW →"
    thesis: str = ""
    contact_info: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serializes takeaway spec to dictionary."""
        serialized_principles = []
        for p in self.principles:
            if isinstance(p, PrincipleSpec):
                serialized_principles.append(p.to_dict())
            elif isinstance(p, dict):
                serialized_principles.append(p)
            else:
                serialized_principles.append(str(p))

        d: dict[str, Any] = {
            "principles": serialized_principles,
            "roadmap_title": self.roadmap_title,
            "roadmap_items": list(self.roadmap_items),
            "cta_text": self.cta_text,
        }
        if self.thesis:
            d["thesis"] = self.thesis
        if self.contact_info:
            d["contact_info"] = self.contact_info
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TakeawaySpec:
        """Parses TakeawaySpec from dictionary."""
        if not isinstance(data, dict):
            return cls()
        raw_principles = data.get("principles", [])
        parsed_principles: list[Union[PrincipleSpec, dict[str, Any], str]] = []
        for i, item in enumerate(raw_principles, start=1):
            if isinstance(item, PrincipleSpec):
                parsed_principles.append(item)
            elif isinstance(item, (dict, str)):
                parsed_principles.append(PrincipleSpec.from_dict(item, index=i))
            else:
                parsed_principles.append(str(item))

        raw_roadmap = data.get("roadmap_items", [])
        if isinstance(raw_roadmap, str):
            roadmap_items = [line.strip() for line in raw_roadmap.splitlines() if line.strip()]
        elif isinstance(raw_roadmap, list):
            roadmap_items = [str(item) for item in raw_roadmap]
        else:
            roadmap_items = []

        return cls(
            principles=parsed_principles,
            roadmap_title=str(data.get("roadmap_title", "NEXT STEPS & ROADMAP")),
            roadmap_items=roadmap_items,
            cta_text=str(data.get("cta_text", "EXECUTE BUILD NOW →")),
            thesis=str(data.get("thesis", "")),
            contact_info=str(data.get("contact_info", "")),
        )


# =============================================================================
# Primary Slide Specification Model
# =============================================================================


@dataclass
class SlideSpec:
    """Unified specification for a single presentation slide.

    Encapsulates archetype selection, universal header fields (title, subtitle, kicker),
    speaker notes, and archetype-specific structured content.
    """

    archetype: str
    title: str = ""
    subtitle: str = ""
    kicker: str = ""
    notes: str = ""
    id: str = ""
    tier: str = DEFAULT_TIER
    skip: bool = False

    # Archetype-specific fields
    chapter_number: Union[int, str] = 1
    cards: list[CardSpec] = field(default_factory=list)
    terminals: list[CodeBlockSpec] = field(default_factory=list)
    metrics: list[HeroMetricSpec] = field(default_factory=list)
    steps: list[LadderStepSpec] = field(default_factory=list)
    quadrants: list[QuadrantSpec] = field(default_factory=list)
    checklist: Optional[ChecklistSpec] = None
    takeaway: Optional[TakeawaySpec] = None
    raw_content: dict[str, Any] = field(default_factory=dict)

    @property
    def speaker_notes(self) -> str:
        """Alias property for speaker notes."""
        return self.notes

    @speaker_notes.setter
    def speaker_notes(self, value: str) -> None:
        self.notes = value

    @property
    def code_blocks(self) -> list[CodeBlockSpec]:
        """Alias property for terminals / code blocks."""
        return self.terminals

    @code_blocks.setter
    def code_blocks(self, value: list[CodeBlockSpec]) -> None:
        self.terminals = value

    def to_dict(self) -> dict[str, Any]:
        """Serializes slide spec to a clean dictionary consumable by ArchetypeEngine."""
        out: dict[str, Any] = {
            "archetype": self.archetype,
            "title": self.title,
            "subtitle": self.subtitle,
            "kicker": self.kicker,
            "speaker_notes": self.notes,
            "notes": self.notes,
        }
        if self.id:
            out["id"] = self.id
        if self.tier and self.tier != DEFAULT_TIER:
            out["tier"] = self.tier
        if self.skip:
            out["skip"] = True

        arch = self.archetype.strip().lower().replace("-", "_")

        if arch == "chapter_divider":
            out["chapter_number"] = self.chapter_number
            if not self.kicker:
                out["kicker"] = "CHAPTER"

        elif arch in ("split_cards", "split_comparison"):
            out["cards"] = [c.to_dict() if isinstance(c, CardSpec) else c for c in self.cards]

        elif arch in ("code_terminal", "code_ratchet"):
            out["terminals"] = [t.to_dict() if isinstance(t, CodeBlockSpec) else t for t in self.terminals]

        elif arch in ("hero_metrics", "hero_metric"):
            out["metrics"] = [m.to_dict() if isinstance(m, HeroMetricSpec) else m for m in self.metrics]

        elif arch in ("ladder_hierarchy", "ladder_flow"):
            out["steps"] = [s.to_dict() if isinstance(s, LadderStepSpec) else s for s in self.steps]

        elif arch in ("executive_grid", "exec_grid"):
            out["quadrants"] = [q.to_dict() if isinstance(q, QuadrantSpec) else q for q in self.quadrants]

        elif arch == "dodont_checklist":
            if self.checklist:
                ch_dict = self.checklist.to_dict()
                out.update(ch_dict)
            else:
                out["dont_items"] = self.raw_content.get("dont_items", self.raw_content.get("dont", []))
                out["do_items"] = self.raw_content.get("do_items", self.raw_content.get("do", []))

        elif arch in ("actionable_takeaways", "takeaways"):
            if self.takeaway:
                tk_dict = self.takeaway.to_dict()
                out.update(tk_dict)
            else:
                out["principles"] = self.raw_content.get("principles", [])
                out["roadmap_title"] = self.raw_content.get("roadmap_title", "NEXT STEPS & ROADMAP")
                out["roadmap_items"] = self.raw_content.get("roadmap_items", [])
                out["cta_text"] = self.raw_content.get("cta_text", "EXECUTE BUILD NOW →")

        # Merge any unparsed raw content that doesn't overwrite existing
        for k, v in self.raw_content.items():
            if k not in out:
                out[k] = v

        return _clean_dict(out)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SlideSpec:
        """Parses a SlideSpec from a flat or nested dictionary representation."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict for slide specification, got {type(data)}")

        archetype = str(data.get("archetype", "split_cards")).strip().lower().replace("-", "_")
        title = str(data.get("title", ""))
        subtitle = str(data.get("subtitle", ""))
        kicker = str(data.get("kicker", ""))
        notes = str(data.get("speaker_notes") or data.get("notes") or "")
        slide_id = str(data.get("id", ""))
        tier = str(data.get("tier") or DEFAULT_TIER).strip().lower()
        skip = bool(data.get("skip", False))

        # Check for nested 'content' dictionary
        content = data.get("content", {})
        if isinstance(content, dict):
            if not title and "title" in content:
                title = str(content["title"])
            if not subtitle and "subtitle" in content:
                subtitle = str(content["subtitle"])
            if not kicker and "kicker" in content:
                kicker = str(content["kicker"])
            if not notes and ("speaker_notes" in content or "notes" in content):
                notes = str(content.get("speaker_notes") or content.get("notes") or "")

        # Extract archetype-specific attributes
        chapter_number = data.get("chapter_number", content.get("chapter_number", 1) if isinstance(content, dict) else 1)

        # 1. Cards
        cards_raw = data.get("cards") or (content.get("cards") if isinstance(content, dict) else None) or []
        cards = [CardSpec.from_dict(c) if isinstance(c, dict) else c for c in cards_raw]

        # 2. Code Terminals
        terms_raw = (
            data.get("terminals")
            or data.get("code_blocks")
            or (content.get("terminals") if isinstance(content, dict) else None)
            or (content.get("code_blocks") if isinstance(content, dict) else None)
            or []
        )
        # Handle single code_box
        if not terms_raw:
            single_box = data.get("code_box") or (content.get("code_box") if isinstance(content, dict) else None)
            if single_box and isinstance(single_box, dict):
                terms_raw = [single_box]

        terminals = [CodeBlockSpec.from_dict(t) if isinstance(t, dict) else t for t in terms_raw]

        # 3. Metrics
        metrics_raw = data.get("metrics") or (content.get("metrics") if isinstance(content, dict) else None) or []
        metrics = [HeroMetricSpec.from_dict(m) if isinstance(m, dict) else m for m in metrics_raw]

        # 4. Ladder Steps
        steps_raw = data.get("steps") or (content.get("steps") if isinstance(content, dict) else None) or []
        steps = [LadderStepSpec.from_dict(s) if isinstance(s, dict) else s for s in steps_raw]

        # 5. Quadrants
        quads_raw = data.get("quadrants") or (content.get("quadrants") if isinstance(content, dict) else None) or []
        quadrants = [QuadrantSpec.from_dict(q) if isinstance(q, dict) else q for q in quads_raw]

        # 6. Checklist
        checklist = None
        if archetype == "dodont_checklist":
            if "checklist" in data and isinstance(data["checklist"], dict):
                ch_data = data["checklist"]
            elif isinstance(content, dict) and "checklist" in content and isinstance(content["checklist"], dict):
                ch_data = content["checklist"]
            elif isinstance(content, dict) and ("do_items" in content or "do" in content or "do_column" in content):
                ch_data = content
            else:
                ch_data = data
            checklist = ChecklistSpec.from_dict(ch_data)

        # 7. Takeaway
        takeaway = None
        if archetype in ("actionable_takeaways", "takeaways"):
            if "takeaway" in data and isinstance(data["takeaway"], dict):
                tk_data = data["takeaway"]
            elif "takeaways" in data and isinstance(data["takeaways"], dict):
                tk_data = data["takeaways"]
            elif isinstance(content, dict) and "takeaway" in content and isinstance(content["takeaway"], dict):
                tk_data = content["takeaway"]
            elif isinstance(content, dict) and ("principles" in content or "roadmap_items" in content):
                tk_data = content
            else:
                tk_data = data
            takeaway = TakeawaySpec.from_dict(tk_data)

        raw_extra = dict(data)
        for k in (
            "archetype",
            "title",
            "subtitle",
            "kicker",
            "notes",
            "speaker_notes",
            "id",
            "content",
            "cards",
            "terminals",
            "code_blocks",
            "code_box",
            "metrics",
            "steps",
            "quadrants",
            "checklist",
            "takeaway",
            "takeaways",
            "tier",
            "skip",
        ):
            raw_extra.pop(k, None)

        return cls(
            archetype=archetype,
            title=title,
            subtitle=subtitle,
            kicker=kicker,
            notes=notes,
            id=slide_id,
            tier=tier,
            skip=skip,
            chapter_number=chapter_number,
            cards=cards,
            terminals=terminals,
            metrics=metrics,
            steps=steps,
            quadrants=quadrants,
            checklist=checklist,
            takeaway=takeaway,
            raw_content=raw_extra,
        )


# =============================================================================
# Chapter Specification Model
# =============================================================================


@dataclass
class ChapterSpec:
    """Specification for a presentation chapter grouping slides."""

    number: int = 1
    title: str = ""
    subtitle: str = ""
    slides: list[SlideSpec] = field(default_factory=list)
    notes: str = ""
    include_divider: bool = True

    @property
    def chapter_number(self) -> int:
        """Alias property for chapter number."""
        return self.number

    @chapter_number.setter
    def chapter_number(self, val: int) -> None:
        self.number = val

    @property
    def speaker_notes(self) -> str:
        """Alias property for chapter speaker notes."""
        return self.notes

    @speaker_notes.setter
    def speaker_notes(self, val: str) -> None:
        self.notes = val

    def to_dict(self) -> dict[str, Any]:
        """Serializes chapter to dictionary."""
        d: dict[str, Any] = {
            "chapter_number": self.number,
            "title": self.title,
            "subtitle": self.subtitle,
            "slides": [s.to_dict() if isinstance(s, SlideSpec) else s for s in self.slides],
            "include_divider": self.include_divider,
        }
        if self.notes:
            d["speaker_notes"] = self.notes
        return _clean_dict(d)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChapterSpec:
        """Parses ChapterSpec from dictionary."""
        if not isinstance(data, dict):
            return cls()
        num = data.get("chapter_number", data.get("number", 1))
        try:
            num = int(num)
        except (ValueError, TypeError):
            num = 1

        title = str(data.get("title", ""))
        subtitle = str(data.get("subtitle", ""))
        notes = str(data.get("speaker_notes", data.get("notes", "")))
        include_divider = bool(data.get("include_divider", True))

        raw_slides = data.get("slides", [])
        slides = []
        for s in raw_slides:
            if isinstance(s, SlideSpec):
                slides.append(s)
            elif isinstance(s, dict):
                slides.append(SlideSpec.from_dict(s))

        return cls(
            number=num,
            title=title,
            subtitle=subtitle,
            slides=slides,
            notes=notes,
            include_divider=include_divider,
        )


# =============================================================================
# Presentation Specification Model
# =============================================================================


@dataclass
class PresentationSpec:
    """Root specification for an entire presentation deck.

    Provides complete serialization to/from YAML and JSON, dictionary normalization,
    and direct validation against Blueprint design limits.
    """

    version: str = "1.0"
    metadata: MetadataSpec = field(default_factory=MetadataSpec)
    chapters: list[ChapterSpec] = field(default_factory=list)

    def all_slides(self) -> list[SlideSpec]:
        """Returns a flat list of all slides across all chapters."""
        slides: list[SlideSpec] = []
        for chapter in self.chapters:
            slides.extend(chapter.slides)
        return slides

    def slide_count(self) -> int:
        """Returns the total number of slides across all chapters."""
        return len(self.all_slides())

    def to_dict(self) -> dict[str, Any]:
        """Serializes presentation specification to a standard nested dictionary."""
        d = {
            "version": self.version,
            "metadata": self.metadata.to_dict(),
            "chapters": [c.to_dict() for c in self.chapters],
        }
        return _clean_dict(d)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PresentationSpec:
        """Parses PresentationSpec from dictionary."""
        if not isinstance(data, dict):
            raise TypeError(f"Expected dict for presentation specification, got {type(data)}")

        version = str(data.get("version", "1.0"))
        metadata = MetadataSpec.from_dict(data.get("metadata", {}))

        raw_chapters = data.get("chapters", [])
        chapters = []
        if isinstance(raw_chapters, list):
            for i, c in enumerate(raw_chapters, start=1):
                if isinstance(c, ChapterSpec):
                    chapters.append(c)
                elif isinstance(c, dict):
                    chap_spec = ChapterSpec.from_dict(c)
                    if not chap_spec.number:
                        chap_spec.number = i
                    chapters.append(chap_spec)

        # Handle flat slide list without chapters
        if not chapters and "slides" in data and isinstance(data["slides"], list):
            flat_slides = []
            for s in data["slides"]:
                if isinstance(s, SlideSpec):
                    flat_slides.append(s)
                elif isinstance(s, dict):
                    flat_slides.append(SlideSpec.from_dict(s))
            chapters.append(ChapterSpec(number=1, title=metadata.title or "Presentation", slides=flat_slides))

        return cls(version=version, metadata=metadata, chapters=chapters)

    # -------------------------------------------------------------------------
    # YAML & JSON Serialization Methods
    # -------------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path_or_str: Union[str, Path, TextIO]) -> PresentationSpec:
        """Loads and parses a PresentationSpec from a YAML file path, stream, or string.

        Args:
            path_or_str: Path object, filepath string, open stream, or raw YAML string.

        Returns:
            Instantiated and parsed PresentationSpec.

        Raises:
            FileNotFoundError: If a file path was provided but doesn't exist.
            yaml.YAMLError: If YAML syntax is malformed.
            ValueError: If structure is invalid.
        """
        raw_content: str
        if isinstance(path_or_str, Path):
            raw_content = path_or_str.read_text(encoding="utf-8")
        elif isinstance(path_or_str, str):
            # Check if it's an existing file path or raw YAML content
            potential_path = Path(path_or_str)
            if "\n" not in path_or_str and potential_path.exists() and potential_path.is_file():
                raw_content = potential_path.read_text(encoding="utf-8")
            else:
                raw_content = path_or_str
        elif hasattr(path_or_str, "read"):
            raw_content = path_or_str.read()
        else:
            raise TypeError(f"Unsupported input type for YAML parsing: {type(path_or_str)}")

        loaded = yaml.safe_load(raw_content)
        if not loaded:
            return cls()
        if not isinstance(loaded, dict):
            raise ValueError(f"YAML root must be a mapping, got {type(loaded)}")

        return cls.from_dict(loaded)

    def to_yaml(self, path_or_stream: Optional[Union[str, Path, TextIO]] = None) -> str:
        """Serializes PresentationSpec to formatted YAML.

        Args:
            path_or_stream: Optional file path, Path object, or stream to write output to.

        Returns:
            Formatted YAML string.
        """
        dict_data = self.to_dict()
        yaml_str = yaml.dump(
            dict_data,
            sort_keys=False,
            allow_unicode=True,
            default_flow_style=False,
            indent=2,
        )

        if path_or_stream is not None:
            if isinstance(path_or_stream, (str, Path)):
                Path(path_or_stream).write_text(yaml_str, encoding="utf-8")
            elif hasattr(path_or_stream, "write"):
                path_or_stream.write(yaml_str)

        return yaml_str

    @classmethod
    def from_json(cls, path_or_str: Union[str, Path, TextIO]) -> PresentationSpec:
        """Loads and parses a PresentationSpec from JSON."""
        raw_content: str
        if isinstance(path_or_str, Path):
            raw_content = path_or_str.read_text(encoding="utf-8")
        elif isinstance(path_or_str, str):
            potential_path = Path(path_or_str)
            if "\n" not in path_or_str and potential_path.exists() and potential_path.is_file():
                raw_content = potential_path.read_text(encoding="utf-8")
            else:
                raw_content = path_or_str
        elif hasattr(path_or_str, "read"):
            raw_content = path_or_str.read()
        else:
            raise TypeError(f"Unsupported input type for JSON parsing: {type(path_or_str)}")

        loaded = json.loads(raw_content)
        if not isinstance(loaded, dict):
            raise ValueError(f"JSON root must be an object, got {type(loaded)}")
        return cls.from_dict(loaded)

    def to_json(self, path_or_stream: Optional[Union[str, Path, TextIO]] = None, indent: int = 2) -> str:
        """Serializes PresentationSpec to formatted JSON."""
        dict_data = self.to_dict()
        json_str = json.dumps(dict_data, indent=indent, ensure_ascii=False)

        if path_or_stream is not None:
            if isinstance(path_or_stream, (str, Path)):
                Path(path_or_stream).write_text(json_str, encoding="utf-8")
            elif hasattr(path_or_stream, "write"):
                path_or_stream.write(json_str)

        return json_str

    def validate(self, raise_on_error: bool = False) -> Any:
        """Validates this specification against Blueprint design rules.

        Deferred import to avoid circular dependencies with SpecValidator.
        """
        from preso.spec.validator import SpecValidator

        return SpecValidator.validate(self, raise_on_error=raise_on_error)

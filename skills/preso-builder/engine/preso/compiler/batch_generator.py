"""Presentation Specification Batch Compiler.

Compiles high-level presentation manifests and slide specifications into
atomic, single-pass `gslides batch` JSON payloads with deterministic IDs,
placeholder cleanup, archetype coordinate dispatch, and guaranteed speaker notes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
from typing import Any, Optional, Union
import yaml

from preso.engine.archetypes import ArchetypeEngine
from preso.spec.models import DEFAULT_TIER, SLIDE_TIERS

# =============================================================================
# Manifest Data Models
# =============================================================================


@dataclass
class SlideManifest:
    """Specification for an individual slide in a presentation manifest."""

    archetype: str
    id: Optional[str] = None
    title: str = ""
    subtitle: str = ""
    kicker: str = ""
    notes: str = ""
    speaker_notes: str = ""

    # Archetype-specific payload fields
    cards: list[Any] = field(default_factory=list)
    terminals: list[Any] = field(default_factory=list)
    metrics: list[Any] = field(default_factory=list)
    steps: list[Any] = field(default_factory=list)
    quadrants: list[Any] = field(default_factory=list)
    dont_items: list[Any] = field(default_factory=list)
    do_items: list[Any] = field(default_factory=list)
    principles: list[Any] = field(default_factory=list)
    chapter_number: Optional[Union[int, str]] = None
    roadmap_title: str = "NEXT STEPS & ROADMAP"
    roadmap_items: list[Any] = field(default_factory=list)
    cta_text: str = "EXECUTE BUILD NOW →"
    extra_fields: dict[str, Any] = field(default_factory=dict)

    def get_notes(self) -> str:
        """Returns speaker notes from either `notes` or `speaker_notes`."""
        return (self.notes or self.speaker_notes or "").strip()

    def to_dict(self) -> dict[str, Any]:
        """Serializes slide manifest to dictionary."""
        d: dict[str, Any] = {
            "archetype": self.archetype,
            "title": self.title,
            "subtitle": self.subtitle,
            "kicker": self.kicker,
            "notes": self.get_notes(),
        }
        if self.id:
            d["id"] = self.id
        if self.chapter_number is not None:
            d["chapter_number"] = self.chapter_number
        if self.cards:
            d["cards"] = self.cards
        if self.terminals:
            d["terminals"] = self.terminals
        if self.metrics:
            d["metrics"] = self.metrics
        if self.steps:
            d["steps"] = self.steps
        if self.quadrants:
            d["quadrants"] = self.quadrants
        if self.dont_items:
            d["dont_items"] = self.dont_items
        if self.do_items:
            d["do_items"] = self.do_items
        if self.principles:
            d["principles"] = self.principles
        if self.roadmap_items:
            d["roadmap_items"] = self.roadmap_items
            d["roadmap_title"] = self.roadmap_title
            d["cta_text"] = self.cta_text
        if self.extra_fields:
            d.update(self.extra_fields)
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SlideManifest:
        """Creates a SlideManifest from dictionary representation."""
        data_copy = dict(data)
        archetype = str(data_copy.pop("archetype", "split_cards"))
        slide_id = data_copy.pop("id", None)
        title = str(data_copy.pop("title", ""))
        subtitle = str(data_copy.pop("subtitle", ""))
        kicker = str(data_copy.pop("kicker", ""))
        notes = str(data_copy.pop("notes", data_copy.pop("speaker_notes", "")))
        cards = data_copy.pop("cards", [])
        terminals = data_copy.pop("terminals", [])
        metrics = data_copy.pop("metrics", [])
        steps = data_copy.pop("steps", [])
        quadrants = data_copy.pop("quadrants", [])
        chk_dict = data_copy.get("checklist", {}) if isinstance(data_copy.get("checklist"), dict) else {}
        tk_dict = data_copy.get("takeaway", {}) if isinstance(data_copy.get("takeaway"), dict) else {}
        dont_items = data_copy.pop("dont_items", data_copy.pop("dont", chk_dict.get("dont_items", chk_dict.get("dont", []))))
        do_items = data_copy.pop("do_items", data_copy.pop("do", chk_dict.get("do_items", chk_dict.get("do", []))))
        principles = data_copy.pop("principles", tk_dict.get("principles", []))
        chapter_number = data_copy.pop("chapter_number", None)
        roadmap_title = str(data_copy.pop("roadmap_title", tk_dict.get("roadmap_title", "NEXT STEPS & ROADMAP")))
        roadmap_items = data_copy.pop("roadmap_items", tk_dict.get("roadmap_items", []))
        cta_text = str(data_copy.pop("cta_text", tk_dict.get("cta_text", "EXECUTE BUILD NOW →")))

        return cls(
            archetype=archetype,
            id=slide_id,
            title=title,
            subtitle=subtitle,
            kicker=kicker,
            notes=notes,
            cards=cards,
            terminals=terminals,
            metrics=metrics,
            steps=steps,
            quadrants=quadrants,
            dont_items=dont_items,
            do_items=do_items,
            principles=principles,
            chapter_number=chapter_number,
            roadmap_title=roadmap_title,
            roadmap_items=roadmap_items,
            cta_text=cta_text,
            extra_fields=data_copy,
        )


@dataclass
class ChapterManifest:
    """Specification for a chapter containing slide manifests."""

    chapter_number: Union[int, str] = 1
    title: str = ""
    subtitle: str = ""
    kicker: str = "CHAPTER"
    notes: str = ""
    slides: list[Union[SlideManifest, dict[str, Any]]] = field(
        default_factory=list
    )
    include_divider: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Serializes chapter manifest to dictionary."""
        return {
            "chapter_number": self.chapter_number,
            "title": self.title,
            "subtitle": self.subtitle,
            "kicker": self.kicker,
            "notes": self.notes,
            "include_divider": self.include_divider,
            "slides": [
                s.to_dict() if isinstance(s, SlideManifest) else s
                for s in self.slides
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChapterManifest:
        """Creates a ChapterManifest from dictionary representation."""
        slides_raw = data.get("slides", [])
        parsed_slides: list[Union[SlideManifest, dict[str, Any]]] = []
        for s in slides_raw:
            if isinstance(s, dict):
                parsed_slides.append(SlideManifest.from_dict(s))
            elif isinstance(s, SlideManifest):
                parsed_slides.append(s)

        return cls(
            chapter_number=data.get("chapter_number", 1),
            title=str(data.get("title", "")),
            subtitle=str(data.get("subtitle", "")),
            kicker=str(data.get("kicker", "CHAPTER")),
            notes=str(data.get("notes", data.get("speaker_notes", ""))),
            slides=parsed_slides,
            include_divider=bool(data.get("include_divider", True)),
        )


@dataclass
class PresentationManifest:
    """Root specification for an executive presentation deck."""

    title: str = "The AI Factory Blueprint"
    subtitle: str = ""
    template_id: Optional[str] = None
    target_audience: str = ""
    core_thesis: str = ""
    chapters: list[ChapterManifest] = field(default_factory=list)
    slides: list[Union[SlideManifest, dict[str, Any]]] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serializes presentation manifest to dictionary."""
        return {
            "title": self.title,
            "subtitle": self.subtitle,
            "template_id": self.template_id,
            "target_audience": self.target_audience,
            "core_thesis": self.core_thesis,
            "chapters": [c.to_dict() for c in self.chapters],
            "slides": [
                s.to_dict() if isinstance(s, SlideManifest) else s
                for s in self.slides
            ],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PresentationManifest:
        """Creates a PresentationManifest from dictionary representation."""
        chapters_raw = data.get("chapters", [])
        parsed_chapters: list[ChapterManifest] = []
        for c in chapters_raw:
            if isinstance(c, dict):
                parsed_chapters.append(ChapterManifest.from_dict(c))
            elif isinstance(c, ChapterManifest):
                parsed_chapters.append(c)

        slides_raw = data.get("slides", [])
        parsed_slides: list[Union[SlideManifest, dict[str, Any]]] = []
        for s in slides_raw:
            if isinstance(s, dict):
                parsed_slides.append(SlideManifest.from_dict(s))
            elif isinstance(s, SlideManifest):
                parsed_slides.append(s)

        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        return cls(
            title=str(data.get("title", "The AI Factory Blueprint")),
            subtitle=str(data.get("subtitle", "")),
            template_id=data.get("template_id"),
            target_audience=str(data.get("target_audience", "")),
            core_thesis=str(data.get("core_thesis", "")),
            chapters=parsed_chapters,
            slides=parsed_slides,
            metadata=metadata,
        )

    @classmethod
    def from_yaml(cls, path_or_content: Union[str, Path]) -> PresentationManifest:
        """Loads and parses a PresentationManifest from a YAML file or string."""
        content: str
        if isinstance(path_or_content, Path) or (
            isinstance(path_or_content, str) and "\n" not in path_or_content and os.path.exists(path_or_content)
        ):
            with open(path_or_content, "r", encoding="utf-8") as f:
                content = f.read()
        else:
            content = str(path_or_content)

        data = yaml.safe_load(content)
        if not isinstance(data, dict):
            raise ValueError(f"YAML content did not parse into a dictionary: {data}")
        return cls.from_dict(data)


# =============================================================================
# Compiler Configuration & Results
# =============================================================================


@dataclass
class BatchCompilerConfig:
    """Configuration options for batch operation compilation."""

    clean_default_placeholders: bool = False
    first_slide_target: str = "add_new"  # "add_new", "reuse_p", "clean_p"
    deterministic_id_prefix: str = "SLIDE"
    validate_operations: bool = True
    # Tiers rendered visibly. None => every tier except "appendix".
    # Slides in other tiers are still built, then hidden via `skip-slide`.
    visible_tiers: Optional[tuple[str, ...]] = None


@dataclass
class BatchResult:
    """Output artifact containing compiled batch operations and presentation stats."""

    operations: list[dict[str, Any]]
    slide_count: int = 0
    slide_ids: list[str] = field(default_factory=list)
    chapter_count: int = 0
    stats: dict[str, Any] = field(default_factory=dict)
    # Local image files that must be inserted after the batch executes
    # (batch `add-image` only accepts URLs). Each entry carries slide id,
    # absolute file path, and x/y/width/height in points.
    pending_images: list[dict[str, Any]] = field(default_factory=list)
    skipped_slide_ids: list[str] = field(default_factory=list)

    def to_json(self, indent: int = 2) -> str:
        """Serializes batch operations array to JSON string."""
        return json.dumps(self.operations, indent=indent)

    def save_json(self, output_path: Union[str, Path]) -> Path:
        """Writes batch operations array to a JSON file on disk."""
        dest = Path(output_path).resolve()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(self.operations, f, indent=2)
        return dest


# =============================================================================
# Batch Compiler
# =============================================================================


class BatchCompiler:
    """Compiles presentation manifests into atomic gslides batch operations.

    Orchestrates:
    - Default placeholder cleanup (`i0`, `i1`) on newly created decks.
    - Chapter dividers and content slide dispatch.
    - Deterministic ID assignment.
    - TODO placeholders for missing speaker notes (never fabricated prose).
    - Tier-based visibility (`skip-slide`) for duration variants / appendix.
    - Single-pass flat operation list aggregation.
    """

    def __init__(
        self,
        config: Optional[BatchCompilerConfig] = None,
    ) -> None:
        """Initializes BatchCompiler with optional configuration."""
        self.config = config or BatchCompilerConfig()

    def _visible_tiers(self) -> tuple[str, ...]:
        if self.config.visible_tiers is not None:
            return tuple(t.strip().lower() for t in self.config.visible_tiers)
        return tuple(t for t in SLIDE_TIERS if t != "appendix")

    def _is_hidden(self, slide_data: dict[str, Any]) -> bool:
        """True when the slide should be built but hidden (skip-slide)."""
        if bool(slide_data.get("skip", False)):
            return True
        tier = str(slide_data.get("tier") or DEFAULT_TIER).strip().lower()
        return tier not in self._visible_tiers()

    def _normalize_slide(
        self,
        slide: Union[SlideManifest, dict[str, Any]],
        slide_index: int,
    ) -> dict[str, Any]:
        """Normalizes a slide input into a clean dictionary with deterministic ID and defaults."""
        data: dict[str, Any]
        if isinstance(slide, SlideManifest):
            data = slide.to_dict()
        elif isinstance(slide, dict):
            data = dict(slide)
        elif hasattr(slide, "to_dict") and callable(slide.to_dict):
            data = slide.to_dict()
        elif hasattr(slide, "__dict__"):
            data = vars(slide)
        else:
            raise TypeError(f"Unsupported slide spec type: {type(slide)}")

        archetype = str(data.get("archetype", "split_cards")).strip().lower()
        archetype = archetype.replace("-", "_")
        data["archetype"] = archetype

        # Provide sane defaults for archetype content if empty
        title = data.get("title", "")
        subtitle = data.get("subtitle", "")

        if archetype == "split_cards" and not data.get("cards"):
            data["cards"] = [
                {"title": title or "Core Concept", "bullets": [subtitle or "Primary architectural standard."]},
                {"title": "Implementation", "bullets": ["Operational details and execution."]},
            ]
        elif archetype == "code_terminal" and not data.get("terminals"):
            data["terminals"] = [
                {"filename": "main.py", "code": "# Production blueprint implementation\npass"}
            ]
        elif archetype == "hero_metrics" and not data.get("metrics"):
            data["metrics"] = [
                {"value": "100%", "unit": "verified", "delta": "+100% accuracy", "is_hero": True}
            ]
        elif archetype == "ladder_hierarchy" and not data.get("steps"):
            data["steps"] = [
                {"number": 1, "title": "Step 1", "description": "Initial setup"},
                {"number": 2, "title": "Step 2", "description": "Execution"},
            ]
        elif archetype == "executive_grid" and not data.get("quadrants"):
            data["quadrants"] = [
                {"number": 1, "title": "Speed", "description": "Fast turnarounds"},
                {"number": 2, "title": "Quality", "description": "Zero defects"},
                {"number": 3, "title": "Cost", "description": "Low token overhead"},
                {"number": 4, "title": "Scale", "description": "Continuous deployment"},
            ]
        elif archetype == "dodont_checklist" and not data.get("dont_items") and not data.get("do_items"):
            data["dont_items"] = ["Anti-pattern without verification"]
            data["do_items"] = ["Deterministic harness and tests"]
        elif archetype == "actionable_takeaways" and not data.get("principles"):
            data["principles"] = [
                {"number": 1, "title": "Action Principle", "description": "Execute immediately."}
            ]

        # Deterministic ID assignment
        if not data.get("id"):
            data["id"] = f"{self.config.deterministic_id_prefix}_{slide_index:02d}_{archetype.upper()}"

        # Speaker notes are optional: pass authored notes through, never invent any.
        notes = str(data.get("notes") or data.get("speaker_notes") or "").strip()
        data["notes"] = notes
        data["speaker_notes"] = notes

        return data

    def compile(
        self,
        manifest: Union[PresentationManifest, dict[str, Any], list[Any]],
        clean_default_placeholders: Optional[bool] = None,
    ) -> BatchResult:
        """Compiles a complete presentation manifest into an atomic batch payload.

        Args:
            manifest: PresentationManifest, raw dictionary manifest, or list of
                slides/chapters.
            clean_default_placeholders: Override config placeholder cleanup setting.

        Returns:
            BatchResult object containing operations list and generation metadata.
        """
        all_ops: list[dict[str, Any]] = []
        slide_ids: list[str] = []
        archetype_counts: dict[str, int] = {}
        chapter_count = 0

        # Step 1: Initial Operations (Placeholder cleanup)
        should_clean = (
            self.config.clean_default_placeholders
            if clean_default_placeholders is None
            else clean_default_placeholders
        )

        if should_clean:
            all_ops.append({"op": "delete-element", "element": "i0"})
            all_ops.append({"op": "delete-element", "element": "i1"})

        # Step 2: Unpack chapters and slides from manifest
        slides_to_process: list[dict[str, Any]] = []

        if isinstance(manifest, PresentationManifest):
            p_manifest = manifest
        elif hasattr(manifest, "to_dict") and callable(manifest.to_dict):
            p_manifest = PresentationManifest.from_dict(manifest.to_dict())
        elif isinstance(manifest, dict):
            p_manifest = PresentationManifest.from_dict(manifest)
        elif isinstance(manifest, list):
            # List of slides or chapters
            p_manifest = PresentationManifest(slides=[s for s in manifest])
        else:
            raise TypeError(f"Unsupported manifest type: {type(manifest)}")

        # Process chapters if present
        if p_manifest.chapters:
            chapter_count = len(p_manifest.chapters)
            for ch in p_manifest.chapters:
                ch_dict = ch.to_dict() if isinstance(ch, ChapterManifest) else ch
                ch_num = ch_dict.get("chapter_number", 1)
                ch_title = ch_dict.get("title", "")
                ch_sub = ch_dict.get("subtitle", "")
                ch_kicker = ch_dict.get("kicker", "CHAPTER")
                ch_notes = ch_dict.get("notes", "")
                include_div = ch_dict.get("include_divider", True)

                # Add Chapter Divider slide if requested and title is present, and not already present
                has_divider_slide = any(
                    (s.archetype if isinstance(s, SlideManifest) else s.get("archetype") if isinstance(s, dict) else getattr(s, "archetype", "")) == "chapter_divider"
                    for s in ch_dict.get("slides", [])
                )
                chapter_slide_dicts = [
                    slide.to_dict() if isinstance(slide, SlideManifest) else dict(slide)
                    for slide in ch_dict.get("slides", [])
                ]
                if include_div and (ch_title or ch_num) and not has_divider_slide:
                    divider_spec: dict[str, Any] = {
                        "archetype": "chapter_divider",
                        "chapter_number": ch_num,
                        "title": ch_title,
                        "subtitle": ch_sub,
                        "kicker": ch_kicker,
                        "notes": ch_notes,
                    }
                    # Hide the auto divider when every slide in the chapter is hidden.
                    if chapter_slide_dicts and all(self._is_hidden(s) for s in chapter_slide_dicts):
                        divider_spec["skip"] = True
                    slides_to_process.append(divider_spec)

                slides_to_process.extend(chapter_slide_dicts)

        elif p_manifest.slides:
            for slide in p_manifest.slides:
                slide_dict = (
                    slide.to_dict() if isinstance(slide, SlideManifest) else dict(slide)
                )
                slides_to_process.append(slide_dict)

        # Step 3: Slide Compilation Loop
        pending_images: list[dict[str, Any]] = []
        skipped_ids: list[str] = []
        for idx, raw_slide in enumerate(slides_to_process, start=1):
            slide_data = self._normalize_slide(raw_slide, idx)
            slide_id = slide_data["id"]
            archetype = slide_data["archetype"]

            # Generate archetype batch operations via ArchetypeEngine
            slide_ops = ArchetypeEngine.generate_slide_ops(
                slide_spec=slide_data,
                slide_index=idx,
            )

            # Local images cannot go through batch `add-image` (URL-only);
            # archetypes emit `_pending-image` markers that the CLI inserts
            # after the batch runs.
            for op in slide_ops:
                if op.get("op") == "_pending-image":
                    pending_images.append({k: v for k, v in op.items() if k != "op"})
                else:
                    all_ops.append(op)

            if self._is_hidden(slide_data):
                all_ops.append({"op": "skip-slide", "slide": slide_id})
                skipped_ids.append(slide_id)

            slide_ids.append(slide_id)
            archetype_counts[archetype] = archetype_counts.get(archetype, 0) + 1

        stats = {
            "total_operations": len(all_ops),
            "slide_count": len(slide_ids),
            "chapter_count": chapter_count,
            "archetypes": archetype_counts,
            "skipped_slides": len(skipped_ids),
            "pending_images": len(pending_images),
        }

        return BatchResult(
            operations=all_ops,
            pending_images=pending_images,
            skipped_slide_ids=skipped_ids,
            slide_count=len(slide_ids),
            slide_ids=slide_ids,
            chapter_count=chapter_count,
            stats=stats,
        )

    def compile_slides(
        self,
        slides: list[Union[SlideManifest, dict[str, Any]]],
        clean_placeholders: Optional[bool] = None,
    ) -> BatchResult:
        """Compiles a flat list of slide manifests into a BatchResult."""
        return self.compile(
            manifest=PresentationManifest(slides=slides),
            clean_default_placeholders=clean_placeholders,
        )

    def compile_slide(
        self,
        slide: Union[SlideManifest, dict[str, Any]],
        slide_index: int = 1,
    ) -> list[dict[str, Any]]:
        """Compiles a single slide specification into its batch operations."""
        slide_data = self._normalize_slide(slide, slide_index)
        ops = ArchetypeEngine.generate_slide_ops(
            slide_spec=slide_data,
            slide_index=slide_index,
        )
        return [op for op in ops if op.get("op") != "_pending-image"]

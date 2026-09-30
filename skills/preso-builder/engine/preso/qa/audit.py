"""Render-audit checklist generation for built decks.

The automated verifier catches structural problems (overflow heuristics,
bounds). What it cannot catch is what a human eye sees on the rendered slide.
This module turns the exported thumbnails into a per-slide checklist that an
agent (multimodal) or a human walks through, with a hard cap on fix rounds.

Workflow:
    1. `preso build` (or `preso audit --deck-id X`) exports fresh thumbnails.
    2. `audit_checklist.md` lists every slide PNG with spec context and the
       overflow hotspots predicted by the shared text-fit heuristic.
    3. The reviewer opens each PNG, applies the rubric, fixes the spec, rebuilds.
       After 2 fix rounds, stop and show the user the remaining issues.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Sequence, Union

from preso.spec.models import DEFAULT_TIER, PresentationSpec

MAX_FIX_ROUNDS = 2

RUBRIC: tuple[tuple[str, str], ...] = (
    ("Overflow / clipping", "No text cut off, no text spilling outside its card or box."),
    ("Padding & alignment", "Consistent inner padding; columns/cards aligned on a common grid."),
    ("Bottom-left zone", "Nothing collides with the footer / logo area in the bottom-left."),
    ("Collisions", "No overlapping shapes or text; header, subtitle and body do not touch."),
    ("Contrast", "Text readable on its background (white on navy, navy on light)."),
    ("Leftovers", "No template placeholder text, empty shapes, or stray elements."),
    ("Takeaway", "Subtitle states the slide's point as a sentence a skimmer would get."),
)


def _deck_slide_rows(spec: Optional[PresentationSpec]) -> list[dict[str, Any]]:
    """Mirrors the compiler's slide order (auto chapter dividers included)."""
    rows: list[dict[str, Any]] = []
    if spec is None:
        return rows
    for chapter in spec.chapters:
        has_divider = any(
            (s.archetype or "").strip().lower() == "chapter_divider" for s in chapter.slides
        )
        if getattr(chapter, "include_divider", True) and not has_divider and (chapter.title or chapter.number):
            rows.append({
                "title": chapter.title,
                "archetype": "chapter_divider (auto)",
                "tier": DEFAULT_TIER,
                "skip": False,
            })
        for s in chapter.slides:
            rows.append({
                "title": s.title,
                "archetype": s.archetype,
                "tier": getattr(s, "tier", DEFAULT_TIER) or DEFAULT_TIER,
                "skip": bool(getattr(s, "skip", False)),
            })
    return rows


def _hotspots_by_slide(operations: Optional[Sequence[dict[str, Any]]]) -> dict[int, list[str]]:
    """Returns predicted overflow hotspots keyed by 1-based deck slide index."""
    if not operations:
        return {}
    from preso.qa.verifier import QAVerifier  # pylint: disable=g-import-not-at-top

    _v, warns, _m, _r = QAVerifier().verify_text_overflow(list(operations))
    out: dict[int, list[str]] = {}
    for w in warns:
        details = w.get("details", {})
        idx = int(w.get("slide_index", 0))
        out.setdefault(idx, []).append(
            f"`{w.get('element_id')}` cut ~{details.get('excess_chars', '?')} chars "
            f"(capacity ~{details.get('capacity_chars', '?')})"
        )
    return out


def _hidden_slide_indices(operations: Optional[Sequence[dict[str, Any]]]) -> set[int]:
    """1-based deck indices hidden via `skip-slide` (explicit skip or out-of-tier)."""
    if not operations:
        return set()
    index_by_id: dict[str, int] = {}
    for op in operations:
        if op.get("op") == "add-slide":
            index_by_id[str(op.get("id"))] = len(index_by_id) + 1
    return {
        index_by_id[str(op.get("slide"))]
        for op in operations
        if op.get("op") == "skip-slide" and str(op.get("slide")) in index_by_id
    }


def write_audit_checklist(
    thumbnails: Sequence[Union[str, Path]],
    output_path: Union[str, Path],
    spec: Optional[PresentationSpec] = None,
    operations: Optional[Sequence[dict[str, Any]]] = None,
    deck_id: str = "",
) -> Path:
    """Writes `audit_checklist.md` pairing each thumbnail with context + rubric."""
    thumbs = sorted(Path(t).resolve() for t in thumbnails)
    rows = _deck_slide_rows(spec)
    hotspots = _hotspots_by_slide(operations)
    hidden = _hidden_slide_indices(operations)
    dest = Path(output_path).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = ["# Render audit checklist", ""]
    if deck_id:
        lines.append(f"Deck: https://docs.google.com/presentation/d/{deck_id}/edit")
        lines.append("")
    lines += [
        f"Open every PNG below and check it against the rubric. Fix issues in the spec and "
        f"rebuild. **Stop after {MAX_FIX_ROUNDS} fix rounds** and show the user what remains.",
        "",
        "## Rubric (apply to every slide)",
        "",
    ]
    lines += [f"- **{name}** — {desc}" for name, desc in RUBRIC]
    lines += ["", "## Slides", ""]

    if not thumbs:
        lines.append("_No thumbnails were exported. Run `preso audit --deck-id <ID>` against a live deck._")

    for i, thumb in enumerate(thumbs, start=1):
        row = rows[i - 1] if i - 1 < len(rows) else {}
        title = row.get("title") or "(untitled)"
        meta = [f"archetype `{row.get('archetype', '?')}`"]
        tier = row.get("tier", DEFAULT_TIER)
        if tier != DEFAULT_TIER:
            meta.append(f"tier `{tier}`")
        if row.get("skip"):
            meta.append("hidden (skip)")
        elif i in hidden:
            meta.append("hidden (tier)")
        lines.append(f"### {i:02d}. {title}")
        lines.append("")
        lines.append(f"- PNG: `{thumb}`")
        lines.append(f"- {' · '.join(meta)}")
        for h in hotspots.get(i, []):
            lines.append(f"- ⚠ Predicted overflow: {h}")
        lines.append("- [ ] Passes rubric")
        lines.append("")

    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return dest

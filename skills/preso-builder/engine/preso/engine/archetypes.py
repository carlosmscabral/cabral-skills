"""Google Cloud Editorial Presentation Slide Archetype Batch Operation Generators.

Implements 18 slide archetypes (12 core + 6 Google Cloud Editorial archetypes)
generating atomic, single-pass `gslides batch` JSON payloads with deterministic
IDs, typography, Google 4-color accents, WCAG AA contrast, and speaker notes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union

from preso.engine.coordinates import (
    BoundingBox,
    calculate_2x2_grid_bounds,
    calculate_asymmetric_split_bounds,
    calculate_card_internal_bounds,
    calculate_grid_bounds,
    calculate_header_bounds,
    calculate_n_column_bounds,
)
from preso.engine.design_tokens import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    COLOR_AMBER_DARK,
    COLOR_AMBER_LIGHT,
    COLOR_AMBER_TEXT,
    COLOR_AMBER_WARN,
    COLOR_BG_LIGHT,
    COLOR_BLUE_ACCENT,
    COLOR_BLUE_LIGHT,
    COLOR_BLUE_SUBTITLE,
    COLOR_BLUE_TEXT,
    COLOR_CARD_BORDER,
    COLOR_CARD_WHITE,
    COLOR_CODE_FILENAME,
    COLOR_DARK_BORDER,
    COLOR_DARK_MUTED,
    COLOR_DARK_PRIMARY,
    COLOR_DARK_SURFACE,
    COLOR_DIVIDER,
    COLOR_DOT_GREEN,
    COLOR_DOT_RED,
    COLOR_DOT_YELLOW,
    COLOR_GREEN_BORDER,
    COLOR_GREEN_DO,
    COLOR_GREEN_LIGHT,
    COLOR_GREEN_TEXT,
    COLOR_NAVY_PRIMARY,
    COLOR_NAVY_SURFACE,
    COLOR_ORANGE_COBUILD,
    COLOR_ORANGE_TINT,
    COLOR_RED_BORDER,
    COLOR_RED_DONT,
    COLOR_RED_LIGHT,
    COLOR_RED_TEXT,
    COLOR_SLATE_DARK,
    COLOR_SLATE_HEADER,
    COLOR_TEXT_BODY,
    COLOR_TEXT_CODE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_WHITE,
    FONT_FAMILY_BODY,
    FONT_FAMILY_CODE,
    FONT_FAMILY_HEADING,
    FONT_SIZE_BADGE,
    FONT_SIZE_CARD_BODY,
    FONT_SIZE_CARD_HEADER,
    FONT_SIZE_CHAPTER_NUM,
    FONT_SIZE_CHAPTER_SUBTITLE,
    FONT_SIZE_CHAPTER_TITLE,
    FONT_SIZE_CODE_BODY,
    FONT_SIZE_CODE_FILENAME,
    FONT_SIZE_HERO_DELTA,
    FONT_SIZE_HERO_STAT,
    FONT_SIZE_HERO_UNIT,
    FONT_SIZE_KICKER,
    FONT_SIZE_SLIDE_SUBTITLE,
    FONT_SIZE_SLIDE_TITLE,
    GOOGLE_4_COLORS,
    ZEN_CLOSING_SECT_Y,
    ZEN_GRID_2X2_TOP_Y,
    ZEN_GRID_2X3_TOP_Y,
    ZEN_SPLIT_CARDS_MA_TOP_Y,
    ZEN_STAIRCASE_HIGHEST_TOP_Y,
    ZEN_SUBTITLE_SIZE,
    ZEN_TITLE_COMPACT,
    ZEN_TITLE_LARGE,
    ZEN_TITLE_MEDIUM,
    google_accent,
)


# =============================================================================
# Input Data Models
# =============================================================================


@dataclass
class CardSpec:
    """Specification for a content card in split comparison archetypes."""

    title: str
    bullets: list[str] | str
    category: str = ""
    stripe_color: str = ""


@dataclass
class TerminalSpec:
    """Specification for a code/ratchet terminal box."""

    filename: str
    code: str
    badge_text: str = ""
    badge_color: str = COLOR_TEXT_WHITE
    badge_bg: str = ""


@dataclass
class MetricSpec:
    """Specification for a hero metric / economics callout card."""

    value: str
    unit: str
    delta: str = ""
    delta_type: str = "positive"  # "positive", "negative", or "neutral"
    description: str = ""
    is_hero: bool = False
    kicker: str = ""


@dataclass
class StepSpec:
    """Specification for a ladder / stepped flow rung."""

    number: Union[int, str]
    title: str
    description: str


@dataclass
class QuadrantSpec:
    """Specification for a 2x2 executive grid quadrant."""

    number: Union[int, str]
    title: str
    description: str


@dataclass
class PrincipleSpec:
    """Specification for an action principle item in Archetype 8."""

    number: Union[int, str]
    title: str
    description: str


# =============================================================================
# Helper Utilities for Operation Payloads
# =============================================================================


from preso.engine.diagrams import RawCanvas, generate_flow_diagram  # noqa: E402


def _format_bullets(bullets: list[str] | str) -> str:
    """Formats bullet items into a newline-separated bullet string."""
    if isinstance(bullets, str):
        return bullets
    formatted_lines = []
    for item in bullets:
        line = item.strip()
        if not line:
            continue
        if not line.startswith("•") and not line.startswith("-"):
            line = f"• {line}"
        formatted_lines.append(line)
    return "\n".join(formatted_lines)


def _build_mini_4color_bar(
    slide_id: str,
    prefix: str,
    x: float = 36.0,
    y: float = 26.0,
    seg_w: float = 18.0,
    seg_h: float = 3.0,
    gap: float = 0.0,
    colors: tuple[str, str, str, str] = ("#1A73E8", "#EA4335", "#FBBC04", "#34A853"),
    suffixes: tuple[str, str, str, str] = ("1", "2", "3", "4"),
) -> list[dict[str, Any]]:
    """Emits the signature Google Cloud Editorial 4-color mini bar."""
    ops: list[dict[str, Any]] = []
    for idx, (col, sfx) in enumerate(zip(colors, suffixes)):
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": round(x + idx * (seg_w + gap), 2),
            "y": round(y, 2),
            "width": round(seg_w, 2),
            "height": round(seg_h, 2),
            "background_color": col,
            "id": f"{prefix}_{sfx}",
        })
    return ops


def _build_header_ops(
    slide_id: str,
    slide_idx_str: str,
    title: str,
    subtitle: str,
    kicker: str,
) -> list[dict[str, Any]]:
    """Builds Zen Editorial header operations for content slides."""
    bounds = calculate_header_bounds()
    ops: list[dict[str, Any]] = []

    # Zen Editorial 4-color mini bar (36..116pt, y=25pt, h=3pt)
    ops.extend(
        _build_mini_4color_bar(
            slide_id=slide_id,
            prefix=f"MBAR_S{slide_idx_str}",
            x=bounds["title"].x,
            y=25.0,
            seg_w=20.0,
            seg_h=3.0,
        )
    )

    # Optional category kicker inline next to mini bar (omitted when empty for Zen restraint)
    if kicker and kicker.strip():
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": kicker.strip().upper(),
            "x": 124.0,
            "y": 19.0,
            "width": 360.0,
            "height": 16.0,
            "font_size": 9.0,
            "bold": True,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": f"HDR_S{slide_idx_str}_PILL",
        })

    # Slide Main Title — Zen Google Sans Regular #202124 with adaptive single-line scale
    if title:
        clean_t = title.strip()
        if len(clean_t) <= 45:
            t_font = ZEN_TITLE_LARGE
        elif len(clean_t) <= 52:
            t_font = ZEN_TITLE_MEDIUM
        else:
            t_font = ZEN_TITLE_COMPACT
        t_height = 52.0 if (len(clean_t) > 60 and not subtitle) else 32.0
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": title,
            "x": bounds["title"].x,
            "y": 40.0,
            "width": bounds["title"].width,
            "height": t_height,
            "font_size": t_font,
            "bold": False,
            "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": f"HDR_S{slide_idx_str}_TITL",
        })

    # Slide Subtitle / Supporting Line
    if subtitle:
        s_font = 12.5 if len(subtitle.strip()) > 85 else ZEN_SUBTITLE_SIZE
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": subtitle,
            "x": bounds["subtitle"].x,
            "y": 74.0,
            "width": bounds["subtitle"].width,
            "height": 20.0,
            "font_size": s_font,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": f"HDR_S{slide_idx_str}_SUBT",
        })

    return ops


def _extract_slide_idx(slide_id: str, default: int = 1) -> str:
    """Extracts a 2-digit slide index string from a slide ID."""
    import re

    match = re.search(r"(?:SLIDE_)?(\d+)", slide_id)
    if match:
        return f"{int(match.group(1)):02d}"
    return f"{default:02d}"


def _round_rect_top_bar_bounds(x: float, width: float, height: float) -> tuple[float, float]:
    """Computes (bar_x, bar_width) flush with the flat top segment of a Google Slides ROUND_RECTANGLE.

    Google Slides renders ROUND_RECTANGLE with corner radius r ≈ (1/6) * min(width, height).
    Insetting the top bar by ~0.175 * min(width, height) avoids corner overhang wings.
    """
    inset = round(min(42.0, max(12.0, 0.175 * min(width, height))), 2)
    bar_w = round(max(24.0, width - 2.0 * inset), 2)
    bar_x = round(x + (width - bar_w) / 2.0, 2)
    return bar_x, bar_w


# =============================================================================
# Archetype 1: Chapter Divider (Dark Navy Master)
# =============================================================================


def generate_chapter_divider(
    slide_id: str,
    chapter_number: Union[int, str],
    title: str,
    subtitle: str,
    speaker_notes: str = "",
    kicker: str = "CHAPTER",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 1: Chapter Divider.

    Exact Blueprint Standard: Pure white #FFFFFF background, Google rainbow
    gradient progress bar across the top, massive 72pt black chapter number,
    72pt black chapter title, and 18pt Google Blue subtitle/aphorism.
    """
    slide_idx = _extract_slide_idx(slide_id)
    chap_num_str = f"{int(chapter_number):02d}" if str(chapter_number).isdigit() else str(chapter_number)

    # Dynamic vertical flow calculation based on title length to prevent line-wrapping overlap
    clean_title = (title or "").strip()
    title_len = len(clean_title)

    if title_len <= 22:
        # Single-line title (e.g. "Context Engineering")
        title_font_size = 56.0
        title_y = 118.0
        title_height = 65.0
        sub_y = 196.0
        sub_font_size = 16.0
        sub_height = 70.0
    elif title_len <= 42:
        # 2-line title (e.g. "The Enterprise Observability Gap")
        title_font_size = 46.0
        title_y = 116.0
        title_height = 112.0
        sub_y = 240.0
        sub_font_size = 15.0
        sub_height = 75.0
    else:
        # Multi-line long title
        title_font_size = 38.0
        title_y = 114.0
        title_height = 126.0
        sub_y = 250.0
        sub_font_size = 14.5
        sub_height = 75.0

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_CARD_WHITE},
        *_build_mini_4color_bar(
            slide_id=slide_id,
            prefix=f"BAR_S{slide_idx}",
            x=36.0,
            y=36.0,
            seg_w=22.0,
            seg_h=3.5,
            colors=("#1A73E8", "#EA4335", "#FBBC04", "#34A853"),
            suffixes=("BLU", "RED", "YEL", "GRN"),
        ),

        # Editorial Chapter Number (56pt Google Blue)
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": chap_num_str,
            "x": 36.0,
            "y": 52.0,
            "width": 648.0,
            "height": 56.0,
            "font_size": 56.0,
            "bold": False,
            "color": COLOR_BLUE_ACCENT,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": f"NUM_S{slide_idx}",
        },

        # Dynamic Editorial Chapter Title (Google Sans Regular #202124)
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": title,
            "x": 36.0,
            "y": title_y,
            "width": 648.0,
            "height": title_height,
            "font_size": title_font_size,
            "bold": False,
            "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": f"TITL_S{slide_idx}",
        },

        # Subtitle / Aphorism (Positioned safely below title with zero overlap)
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": subtitle,
            "x": 36.0,
            "y": sub_y,
            "width": 648.0,
            "height": sub_height,
            "font_size": sub_font_size,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "line_spacing": 130,
            "id": f"SUBT_S{slide_idx}",
        },
    ]

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 2: 2-Card & 3-Card Split Comparison (+ Optional Process Strip)
# =============================================================================


def _resolve_card_accent(stripe_color: str, index: int) -> tuple[str, str, str]:
    """Returns (solid_hex, pill_bg_hex, pill_fg_hex) for a card at `index`."""
    clean = (stripe_color or "").strip().upper()
    if not clean:
        solid, text, tint = google_accent(index)
        return solid, tint, text
    accent_map = {
        "#1A73E8": (COLOR_BLUE_ACCENT, COLOR_BLUE_LIGHT, COLOR_BLUE_TEXT),
        "#34A853": ("#34A853", COLOR_GREEN_LIGHT, COLOR_GREEN_TEXT),
        "#137333": ("#34A853", COLOR_GREEN_LIGHT, COLOR_GREEN_TEXT),
        "#FBBC04": ("#FBBC04", COLOR_AMBER_LIGHT, COLOR_AMBER_DARK),
        "#F9AB00": ("#FBBC04", COLOR_AMBER_LIGHT, COLOR_AMBER_DARK),
        "#EA4335": ("#EA4335", COLOR_RED_LIGHT, COLOR_RED_TEXT),
        "#C5221F": ("#EA4335", COLOR_RED_LIGHT, COLOR_RED_TEXT),
        "#E37400": (COLOR_ORANGE_COBUILD, COLOR_AMBER_LIGHT, COLOR_AMBER_DARK),
    }
    if clean in accent_map:
        return accent_map[clean]
    return stripe_color, COLOR_BLUE_LIGHT, COLOR_BLUE_TEXT


def generate_split_cards(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    cards: list[Union[dict[str, Any], CardSpec]],
    speaker_notes: str = "",
    foundation: Optional[Union[dict[str, Any], CardSpec, str]] = None,
    flow_steps: Optional[list[Union[dict[str, Any], str]]] = None,
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 2: Split Card Comparison.

    Supports 2-card and 3-card Zen Editorial variants on a `#F8F9FA` soft canvas,
    adaptive *Ma* vertical breathing room for concise cards, Regular semantic-colored
    card titles, optional top `flow_steps` horizontal process strip, and optional
    bottom `foundation` baseline banner.
    """
    slide_idx = _extract_slide_idx(slide_id)
    n = len(cards)
    if n < 1:
        raise ValueError("At least 1 card is required for split card archetype")

    def _card_density(rc: Any) -> tuple[int, int]:
        raw_b = rc.bullets if isinstance(rc, CardSpec) else rc.get("bullets", [])
        if isinstance(raw_b, list):
            return len(raw_b), sum(len(str(x)) for x in raw_b)
        s = str(raw_b or "")
        return max(1, s.count("\n") + 1), len(s)

    densities = [_card_density(c) for c in cards]
    max_bullets = max((d[0] for d in densities), default=0)
    max_chars = max((d[1] for d in densities), default=0)

    has_flow = bool(flow_steps)
    compact = bool(foundation or has_flow)
    gap = 24.0 if n == 2 else 18.0
    if has_flow and foundation:
        step_y, step_h = 100.0, 44.0
        col_bounds = calculate_n_column_bounds(n=n, gap=gap, top_y=154.0, height=132.0)
    elif has_flow:
        step_y, step_h = 114.0, 46.0
        col_bounds = calculate_n_column_bounds(n=n, gap=gap, top_y=176.0, height=198.0)
    elif foundation:
        step_y, step_h = 100.0, 46.0
        col_bounds = calculate_n_column_bounds(n=n, gap=gap, top_y=102.0, height=182.0)
    elif max_bullets <= 3 and max_chars <= 185:
        step_y, step_h = 100.0, 46.0
        col_bounds = calculate_n_column_bounds(
            n=n, gap=gap, top_y=ZEN_SPLIT_CARDS_MA_TOP_Y, height=232.0
        )
    else:
        step_y, step_h = 100.0, 46.0
        col_bounds = calculate_n_column_bounds(n=n, gap=gap)

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_BG_LIGHT},
    ]

    # Universal Header
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    # Optional Top Process Strip (Slide 10 Zen Editorial pattern: white pills + semantic outlines)
    if flow_steps:
        steps_clean = list(flow_steps)[:5]
        m = len(steps_clean)
        step_gap = 20.0 if m <= 4 else 14.0
        step_w = (648.0 - (m - 1) * step_gap) / m
        for j, raw_step in enumerate(steps_clean):
            s_idx = j + 1
            sx = round(36.0 + j * (step_w + step_gap), 2)
            sw = round(step_w, 2)
            solid_hex, _, _ = google_accent(j)
            if isinstance(raw_step, dict):
                st_title = str(raw_step.get("title") or raw_step.get("label") or f"Step {s_idx}")
                st_sub = str(raw_step.get("subtitle") or raw_step.get("detail") or "")
                st_hi = bool(raw_step.get("highlight", False))
            else:
                st_title = str(raw_step)
                st_sub = ""
                st_hi = False

            step_id = f"FSTEP_S{slide_idx}_{s_idx}"
            ops.append({
                "op": "add-shape",
                "slide": slide_id,
                "shape_type": "ROUND_RECTANGLE",
                "x": sx,
                "y": step_y,
                "width": sw,
                "height": step_h,
                "background_color": COLOR_ORANGE_TINT if st_hi else COLOR_CARD_WHITE,
                "id": step_id,
            })
            ops.append({
                "op": "style-shape",
                "element": step_id,
                "outline_color": COLOR_ORANGE_COBUILD if st_hi else solid_hex,
                "outline_weight": 2.0 if st_hi else 1.5,
            })
            if st_sub:
                top_pad = round((step_h - 34.0) / 2.0, 2)
                ops.append({
                    "op": "add-textbox",
                    "slide": slide_id,
                    "text": st_title,
                    "x": round(sx + 4.0, 2),
                    "y": round(step_y + top_pad, 2),
                    "width": round(sw - 8.0, 2),
                    "height": 17.0,
                    "font_size": 10.0,
                    "bold": False,
                    "color": COLOR_TEXT_PRIMARY,
                    "font_family": FONT_FAMILY_HEADING,
                    "alignment": "center",
                    "content_alignment": "MIDDLE",
                    "id": f"FSTEP_TITL_S{slide_idx}_{s_idx}",
                })
                ops.append({
                    "op": "add-textbox",
                    "slide": slide_id,
                    "text": st_sub,
                    "x": round(sx + 4.0, 2),
                    "y": round(step_y + top_pad + 18.0, 2),
                    "width": round(sw - 8.0, 2),
                    "height": 16.0,
                    "font_size": 8.5,
                    "color": COLOR_TEXT_MUTED,
                    "font_family": FONT_FAMILY_BODY,
                    "alignment": "center",
                    "content_alignment": "MIDDLE",
                    "id": f"FSTEP_SUB_S{slide_idx}_{s_idx}",
                })
            else:
                ops.append({
                    "op": "add-textbox",
                    "slide": slide_id,
                    "text": st_title,
                    "x": sx,
                    "y": step_y,
                    "width": sw,
                    "height": step_h,
                    "font_size": 10.5,
                    "bold": False,
                    "color": COLOR_TEXT_PRIMARY,
                    "font_family": FONT_FAMILY_HEADING,
                    "alignment": "center",
                    "content_alignment": "MIDDLE",
                    "id": f"FSTEP_TITL_S{slide_idx}_{s_idx}",
                })

            if j < m - 1:
                ops.append({
                    "op": "add-line",
                    "slide": slide_id,
                    "line_category": "STRAIGHT",
                    "x": round(sx + sw + 2.0, 2),
                    "y": round(step_y + step_h / 2.0, 2),
                    "width": round(step_gap - 4.0, 2),
                    "height": 0.0,
                    "line_weight": 1.5,
                    "color": COLOR_TEXT_MUTED,
                    "end_arrow": "FILL_ARROW",
                    "id": f"FCONN_S{slide_idx}_{s_idx}_{s_idx + 1}",
                })

    # Process Cards (Kanso: crisp white card, flush top bar, Regular semantic title, no inner divider)
    for i, raw_card in enumerate(cards):
        card_num = i + 1
        if isinstance(raw_card, CardSpec):
            c_title = raw_card.title
            c_bullets = raw_card.bullets
            c_cat = raw_card.category
            raw_stripe = raw_card.stripe_color
        else:
            c_title = raw_card.get("title", f"Card {card_num}")
            c_bullets = raw_card.get("bullets", [])
            c_cat = raw_card.get("category", "")
            raw_stripe = raw_card.get("stripe_color", "")

        c_stripe, _, pill_fg = _resolve_card_accent(raw_stripe, i)
        box = col_bounds[i]
        card_id = f"CARD_S{slide_idx}_C{card_num}"
        stripe_id = f"STRIPE_S{slide_idx}_C{card_num}"
        pill_id = f"PILL_S{slide_idx}_C{card_num}"
        titl_id = f"TITL_S{slide_idx}_C{card_num}"
        body_id = f"BODY_S{slide_idx}_C{card_num}"

        # Card Container Shape
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": box.x,
            "y": box.y,
            "width": box.width,
            "height": box.height,
            "background_color": COLOR_CARD_WHITE,
            "id": card_id,
        })
        ops.append({
            "op": "style-shape",
            "element": card_id,
            "outline_color": COLOR_CARD_BORDER,
            "outline_weight": 1.0,
        })

        # Top Accent Stripe (inset past ROUND_RECTANGLE corner radius)
        bar_x, bar_w = _round_rect_top_bar_bounds(box.x, box.width, box.height)
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": bar_x,
            "y": box.y,
            "width": bar_w,
            "height": 3.0,
            "background_color": c_stripe,
            "id": stripe_id,
        })

        inner_w = box.width - 36.0
        cur_y = box.y + (12.0 if compact else 16.0)
        if c_cat:
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": c_cat.upper(),
                "x": box.x + 18.0,
                "y": cur_y,
                "width": inner_w,
                "height": 15.0,
                "font_size": 8.5,
                "bold": True,
                "color": pill_fg,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "left",
                "id": pill_id,
            })
            cur_y += 18.0
        else:
            cur_y += 2.0

        # Card Title — Google Sans Regular in accessible semantic accent color
        titl_height = 24.0 if compact else 26.0
        titl_font = 13.0 if (compact or n >= 3) else 15.0
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": c_title,
            "x": box.x + 18.0,
            "y": cur_y,
            "width": inner_w,
            "height": titl_height,
            "font_size": titl_font,
            "bold": False,
            "color": pill_fg,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": titl_id,
        })
        cur_y += (titl_height + (6.0 if compact else 10.0))

        # Card Bullets Body (clean whitespace separation without inner divider line)
        body_text = _format_bullets(c_bullets)
        body_height = max(44.0, (box.y + box.height) - cur_y - 10.0)
        font_size = 10.5 if compact else 11.5
        line_spacing = 135 if compact else 145
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": body_text,
            "x": box.x + 18.0,
            "y": cur_y,
            "width": inner_w,
            "height": body_height,
            "font_size": font_size,
            "color": COLOR_TEXT_BODY,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "line_spacing": line_spacing,
            "id": body_id,
        })

    # Optional Foundation Banner (Common Enterprise Baseline)
    if foundation:
        f_box_x = 36.0
        f_box_y = 294.0
        f_box_w = 648.0
        f_box_h = 84.0

        f_id = f"FOUND_S{slide_idx}"
        f_stripe_id = f"FSTRIPE_S{slide_idx}"
        f_pill_id = f"FPILL_S{slide_idx}"
        f_titl_id = f"FTITL_S{slide_idx}"
        f_body_id = f"FBODY_S{slide_idx}"

        if isinstance(foundation, dict):
            f_title = foundation.get("title", "Fundação Enterprise")
            f_cat = (
                foundation.get("category")
                or foundation.get("category_pill")
                or foundation.get("kicker")
                or "BASE CORPORATIVA"
            )
            f_bullets = (
                foundation.get("bullets")
                or foundation.get("description")
                or foundation.get("text")
                or ""
            )
            f_stripe = foundation.get("stripe_color", foundation.get("theme", COLOR_BLUE_ACCENT))
        elif isinstance(foundation, CardSpec):
            f_title = foundation.title
            f_cat = foundation.category or "BASE CORPORATIVA"
            f_bullets = foundation.bullets
            f_stripe = foundation.stripe_color or COLOR_BLUE_ACCENT
        else:
            f_title = str(foundation)
            f_cat = "BASE CORPORATIVA"
            f_bullets = ""
            f_stripe = COLOR_BLUE_ACCENT

        _, _, f_accent_fg = _resolve_card_accent(f_stripe, 0)

        # 1. Foundation Container Shape
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": f_box_x,
            "y": f_box_y,
            "width": f_box_w,
            "height": f_box_h,
            "background_color": COLOR_CARD_WHITE,
            "id": f_id,
        })
        ops.append({
            "op": "style-shape",
            "element": f_id,
            "outline_color": COLOR_CARD_BORDER,
            "outline_weight": 1.0,
        })

        # 2. Top Accent Stripe
        f_bar_x, f_bar_w = _round_rect_top_bar_bounds(f_box_x, f_box_w, f_box_h)
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": f_bar_x,
            "y": f_box_y,
            "width": f_bar_w,
            "height": 3.0,
            "background_color": f_stripe,
            "id": f_stripe_id,
        })

        # 3. Clean Micro-Kicker + Regular Foundation Title
        f_cur_y = f_box_y + 10.0
        cat_text = str(f_cat).upper()
        pill_w = min(190.0, max(84.0, len(cat_text) * 6.8 + 16.0))
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": cat_text,
            "x": f_box_x + 16.0,
            "y": f_cur_y,
            "width": pill_w,
            "height": 20.0,
            "font_size": 8.5,
            "bold": True,
            "color": f_accent_fg,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "content_alignment": "MIDDLE",
            "id": f_pill_id,
        })
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": f_title,
            "x": f_box_x + 20.0 + pill_w,
            "y": f_cur_y,
            "width": f_box_w - pill_w - 36.0,
            "height": 20.0,
            "font_size": 13.0,
            "bold": False,
            "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "content_alignment": "MIDDLE",
            "id": f_titl_id,
        })

        # 4. Bullets Body
        body_text = _format_bullets(f_bullets) if isinstance(f_bullets, list) else str(f_bullets)
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": body_text,
            "x": f_box_x + 16.0,
            "y": f_cur_y + 24.0,
            "width": f_box_w - 32.0,
            "height": 44.0,
            "font_size": 10.0,
            "color": COLOR_TEXT_BODY,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "line_spacing": 125,
            "id": f_body_id,
        })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 3: Code / Ratchet Terminal Box
# =============================================================================


def generate_code_terminal(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    terminals: list[Union[dict[str, Any], TerminalSpec]],
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 3: Code / Ratchet Terminal Box.

    Supports dual terminal (e.g. legacy vs modern / Do vs Don't) and single full-width terminal.
    Features: Slate Dark background, chrome titlebar, traffic light dots, filename,
    status badge, and monospace syntax body.
    """
    slide_idx = _extract_slide_idx(slide_id)
    n = len(terminals)
    if n < 1:
        raise ValueError("At least 1 terminal specification is required")

    gap = 24.0
    col_bounds = calculate_n_column_bounds(n=n, gap=gap)

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_CARD_WHITE},
    ]

    # Universal Header
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    for i, raw_term in enumerate(terminals):
        t_num = i + 1
        pos_suffix = "L" if (n == 2 and i == 0) else ("R" if (n == 2 and i == 1) else f"T{t_num}")

        if isinstance(raw_term, TerminalSpec):
            filename = raw_term.filename
            code_text = raw_term.code
            badge_text = raw_term.badge_text
            badge_color = raw_term.badge_color
            badge_bg = raw_term.badge_bg
        else:
            filename = raw_term.get("filename", "snippet.py")
            code_text = raw_term.get("code", "")
            badge_text = raw_term.get("badge_text", "")
            badge_color = raw_term.get("badge_color", COLOR_TEXT_WHITE)
            badge_bg = raw_term.get("badge_bg", "")

        box = col_bounds[i]

        term_bg_id = f"TERM_S{slide_idx}_{pos_suffix}_BG"
        term_hdr_id = f"TERM_S{slide_idx}_{pos_suffix}_HDR"
        dot_r_id = f"DOT_S{slide_idx}_{pos_suffix}_R"
        dot_y_id = f"DOT_S{slide_idx}_{pos_suffix}_Y"
        dot_g_id = f"DOT_S{slide_idx}_{pos_suffix}_G"
        file_id = f"FILE_S{slide_idx}_{pos_suffix}"
        badge_id = f"BADGE_S{slide_idx}_{pos_suffix}"
        code_id = f"CODE_S{slide_idx}_{pos_suffix}"

        # 1. Main Dark Terminal Container
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": box.x,
            "y": box.y,
            "width": box.width,
            "height": box.height,
            "background_color": COLOR_SLATE_DARK,
            "id": term_bg_id,
        })
        ops.append({
            "op": "style-shape",
            "element": term_bg_id,
            "outline_color": "#3C4043",
            "outline_weight": 1.0,
        })

        # 2. Chrome Titlebar Header
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": box.x + 1.0,
            "y": box.y + 1.0,
            "width": box.width - 2.0,
            "height": 27.0,
            "background_color": COLOR_SLATE_HEADER,
            "id": term_hdr_id,
        })

        # 3. Traffic Light Dots (vertically centered on 27pt header at box.y + 14.5)
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ELLIPSE",
            "x": box.x + 10.0,
            "y": box.y + 11.5,
            "width": 6.0,
            "height": 6.0,
            "background_color": COLOR_DOT_RED,
            "id": dot_r_id,
        })
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ELLIPSE",
            "x": box.x + 19.0,
            "y": box.y + 11.5,
            "width": 6.0,
            "height": 6.0,
            "background_color": COLOR_DOT_YELLOW,
            "id": dot_y_id,
        })
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ELLIPSE",
            "x": box.x + 28.0,
            "y": box.y + 11.5,
            "width": 6.0,
            "height": 6.0,
            "background_color": COLOR_DOT_GREEN,
            "id": dot_g_id,
        })

        # 4 & 5. Filename and Status Badge
        if badge_text:
            if not badge_bg:
                badge_bg = COLOR_GREEN_TEXT if ("DO" in badge_text.upper() or "✓" in badge_text) else COLOR_RED_TEXT
            badge_w = min(box.width - 173.0, max(75.0, len(badge_text) * 6.5 + 16.0))
            badge_x = box.x + box.width - badge_w - 8.0
            file_w = max(125.0, box.width - badge_w - 48.0)
        else:
            file_w = box.width - 50.0

        # Filename Text
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": filename,
            "x": box.x + 40.0,
            "y": box.y + 1.0,
            "width": file_w,
            "height": 27.0,
            "font_size": FONT_SIZE_CODE_FILENAME,
            "bold": True,
            "color": COLOR_CODE_FILENAME,
            "font_family": FONT_FAMILY_CODE,
            "alignment": "left",
            "content_alignment": "MIDDLE",
            "id": file_id,
        })

        # Status Badge (Do / Don't / Verified)
        if badge_text:
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": badge_text,
                "x": badge_x,
                "y": box.y + 4.5,
                "width": badge_w,
                "height": 20.0,
                "font_size": FONT_SIZE_BADGE,
                "bold": True,
                "color": badge_color,
                "background_color": badge_bg,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "center",
                "content_alignment": "MIDDLE",
                "id": badge_id,
            })

        # 6. Syntax / Code Body
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": code_text,
            "x": box.x + 14.0,
            "y": box.y + 34.0,
            "width": box.width - 28.0,
            "height": box.height - 44.0,
            "font_size": FONT_SIZE_CODE_BODY,
            "color": COLOR_TEXT_CODE,
            "font_family": FONT_FAMILY_CODE,
            "alignment": "left",
            "line_spacing": 130,
            "id": code_id,
        })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 4: Hero Metric / Economics Comparison
# =============================================================================


def generate_hero_metrics(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    metrics: list[Union[dict[str, Any], MetricSpec]],
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 4: Hero Metric Comparison.

    Features: 54pt huge display stat value, kicker, metric unit label,
    positive/negative delta pills, and descriptive context.
    """
    slide_idx = _extract_slide_idx(slide_id)
    n = len(metrics)
    if n < 1:
        raise ValueError("At least 1 metric card is required")

    gap = 18.0 if n == 3 else 24.0
    col_bounds = calculate_n_column_bounds(n=n, gap=gap)

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_CARD_WHITE},
    ]

    # Universal Header
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    for i, raw_metric in enumerate(metrics):
        m_num = i + 1
        if isinstance(raw_metric, MetricSpec):
            val = raw_metric.value
            unit = raw_metric.unit
            delta = raw_metric.delta
            delta_type = raw_metric.delta_type
            desc = raw_metric.description
            is_hero = raw_metric.is_hero
            m_kicker = raw_metric.kicker or f"METRIC {m_num:02d}"
        else:
            val = raw_metric.get("value", "0")
            unit = raw_metric.get("unit", "")
            delta = raw_metric.get("delta", "")
            delta_type = raw_metric.get("delta_type", "positive")
            desc = raw_metric.get("description", "")
            is_hero = raw_metric.get("is_hero", False)
            m_kicker = raw_metric.get("kicker") or raw_metric.get("label") or f"METRIC {m_num:02d}"

        box = col_bounds[i]

        card_id = f"CARD_S{slide_idx}_M{m_num}"
        kicker_id = f"KICK_S{slide_idx}_M{m_num}"
        stat_id = f"STAT_S{slide_idx}_M{m_num}"
        unit_id = f"UNIT_S{slide_idx}_M{m_num}"
        delta_id = f"DELTA_S{slide_idx}_M{m_num}"
        div_id = f"DIV_S{slide_idx}_M{m_num}"
        desc_id = f"DESC_S{slide_idx}_M{m_num}"

        bg_col = COLOR_DARK_PRIMARY if is_hero else COLOR_CARD_WHITE
        border_col = COLOR_DARK_BORDER if is_hero else COLOR_CARD_BORDER
        stat_col = COLOR_TEXT_WHITE if is_hero else COLOR_BLUE_ACCENT
        kicker_col = COLOR_DARK_MUTED if is_hero else COLOR_TEXT_MUTED
        unit_col = COLOR_TEXT_WHITE if is_hero else COLOR_TEXT_PRIMARY
        desc_col = COLOR_DARK_MUTED if is_hero else COLOR_TEXT_MUTED
        div_col = COLOR_DARK_BORDER if is_hero else COLOR_DIVIDER

        # Card Container Shape
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": box.x,
            "y": box.y,
            "width": box.width,
            "height": box.height,
            "background_color": bg_col,
            "id": card_id,
        })
        ops.append({
            "op": "style-shape",
            "element": card_id,
            "outline_color": border_col,
            "outline_weight": 1.0,
        })

        # Editorial Top Accent Bar
        m_bar_x, m_bar_w = _round_rect_top_bar_bounds(box.x, box.width, box.height)
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": m_bar_x,
            "y": box.y,
            "width": m_bar_w,
            "height": 3.5,
            "background_color": COLOR_BLUE_ACCENT if is_hero else google_accent(i)[0],
            "id": f"STRIPE_S{slide_idx}_M{m_num}",
        })

        # Metric Kicker Label
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": m_kicker.upper(),
            "x": box.x + 16.0,
            "y": box.y + 16.0,
            "width": box.width - 32.0,
            "height": 16.0,
            "font_size": 10.5,
            "bold": True,
            "color": kicker_col,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": kicker_id,
        })

        # Big Display Stat Value (54pt)
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": val,
            "x": box.x + 16.0,
            "y": box.y + 34.0,
            "width": box.width - 32.0,
            "height": 58.0,
            "font_size": FONT_SIZE_HERO_STAT,
            "bold": False,
            "color": stat_col,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": stat_id,
        })

        # Metric Unit / Title Label (Google Sans Regular)
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": unit,
            "x": box.x + 16.0,
            "y": box.y + 96.0,
            "width": box.width - 32.0,
            "height": 22.0,
            "font_size": FONT_SIZE_HERO_UNIT,
            "bold": False,
            "color": unit_col,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": unit_id,
        })

        # Delta Indicator Pill
        if delta:
            if delta_type == "negative":
                delta_bg = COLOR_RED_LIGHT
                delta_fg = COLOR_RED_TEXT
            elif delta_type == "warning":
                delta_bg = COLOR_AMBER_LIGHT
                delta_fg = COLOR_AMBER_DARK
            else:
                delta_bg = COLOR_GREEN_LIGHT
                delta_fg = COLOR_GREEN_TEXT

            pill_w = min(box.width - 32.0, max(110.0, len(delta) * 7.5 + 24.0))
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": delta,
                "x": box.x + 16.0,
                "y": box.y + 124.0,
                "width": pill_w,
                "height": 24.0,
                "font_size": FONT_SIZE_HERO_DELTA,
                "bold": True,
                "color": delta_fg,
                "background_color": delta_bg,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "center",
                "content_alignment": "MIDDLE",
                "id": delta_id,
            })

        # Description / Context (clean whitespace separation without inner divider)
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": desc,
            "x": box.x + 16.0,
            "y": box.y + 158.0,
            "width": box.width - 32.0,
            "height": 102.0,
            "font_size": 11.5,
            "color": desc_col,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "line_spacing": 135,
            "id": desc_id,
        })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 5: Ladder / Stepped Hierarchy
# =============================================================================


def generate_ladder_hierarchy(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    steps: list[Union[dict[str, Any], StepSpec]],
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 5: Ladder / Stepped Flow.

    Features: Multi-step horizontal pipeline, step number badges, cycling Google
    4-color top accent bars, directional connector arrow lines, titles, and descriptions.
    """
    slide_idx = _extract_slide_idx(slide_id)
    n = len(steps)
    if n < 2:
        raise ValueError("At least 2 steps are required for a stepped ladder flow")

    gap = 24.0
    col_bounds = calculate_n_column_bounds(n=n, gap=gap)

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_CARD_WHITE},
    ]

    # Universal Header
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    for i, raw_step in enumerate(steps):
        s_idx = i + 1
        if isinstance(raw_step, StepSpec):
            s_num = str(raw_step.number)
            s_title = raw_step.title
            s_desc = raw_step.description
        else:
            s_num = str(raw_step.get("number", s_idx))
            s_title = raw_step.get("title", f"Step {s_idx}")
            s_desc = raw_step.get("description", "")

        box = col_bounds[i]
        solid_hex, text_hex, tint_hex = google_accent(i)

        rung_id = f"RUNG_S{slide_idx}_{s_idx}"
        stripe_id = f"STRIPE_S{slide_idx}_{s_idx}"
        badge_id = f"BADGE_S{slide_idx}_{s_idx}"
        titl_id = f"TITL_S{slide_idx}_{s_idx}"
        div_id = f"DIV_S{slide_idx}_{s_idx}"
        desc_id = f"DESC_S{slide_idx}_{s_idx}"

        # 1. Rung Container Shape
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": box.x,
            "y": box.y,
            "width": box.width,
            "height": box.height,
            "background_color": COLOR_CARD_WHITE,
            "id": rung_id,
        })
        ops.append({
            "op": "style-shape",
            "element": rung_id,
            "outline_color": COLOR_CARD_BORDER,
            "outline_weight": 1.0,
        })

        # 2. Top Accent Stripe
        r_bar_x, r_bar_w = _round_rect_top_bar_bounds(box.x, box.width, box.height)
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": r_bar_x,
            "y": box.y,
            "width": r_bar_w,
            "height": 3.5,
            "background_color": solid_hex,
            "id": stripe_id,
        })

        # 3. Step Number Badge (Editorial tinted pill)
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": s_num,
            "x": box.x + 12.0,
            "y": box.y + 14.0,
            "width": 38.0,
            "height": 26.0,
            "font_size": 12.0,
            "bold": True,
            "color": text_hex,
            "background_color": tint_hex,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "center",
            "content_alignment": "MIDDLE",
            "id": badge_id,
        })

        # 4. Step Title (Google Sans Regular)
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": s_title,
            "x": box.x + 12.0,
            "y": box.y + 50.0,
            "width": box.width - 24.0,
            "height": 32.0,
            "font_size": 14.0,
            "bold": False,
            "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": titl_id,
        })

        # 5. Step Description (clean whitespace separation without inner divider)
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": s_desc,
            "x": box.x + 12.0,
            "y": box.y + 88.0,
            "width": box.width - 24.0,
            "height": 174.0,
            "font_size": 11.0,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "line_spacing": 135,
            "id": desc_id,
        })

        # Directional Connector Arrow between steps
        if i < n - 1:
            conn_x = box.x + box.width
            conn_id = f"CONN_S{slide_idx}_{s_idx}_{s_idx+1}"
            ops.append({
                "op": "add-line",
                "slide": slide_id,
                "line_category": "STRAIGHT",
                "x": conn_x,
                "y": box.y + 32.0,
                "width": gap,
                "height": 0.0,
                "line_weight": 2.0,
                "color": COLOR_TEXT_MUTED,
                "end_arrow": "FILL_ARROW",
                "id": conn_id,
            })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 6: Executive Grid (2x2 Quadrants or 2x3 Six-Card Grid)
# =============================================================================


def generate_executive_grid(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    quadrants: list[Union[dict[str, Any], QuadrantSpec]],
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 6: Executive Grid.

    Supports both 4-card (`2x2`) and 6-card (`2x3`, Zen Slide 2 style) grids with
    adaptive *Ma* negative space (anchoring concise grids in the lower half of the
    canvas), `ROUND_RECTANGLE` white cards, cycling Google 4-color top accent bars,
    clean colored `01..06` labels, Regular `#202124` titles, and muted descriptions.
    """
    slide_idx = _extract_slide_idx(slide_id)
    n_items = len(quadrants)
    if n_items not in (4, 6):
        raise ValueError(f"Archetype 6 requires 4 (2x2) or 6 (2x3) items, got {n_items}")

    max_desc_len = max(
        (
            len(
                q.description
                if isinstance(q, QuadrantSpec)
                else str(q.get("description") or q.get("body") or q.get("text") or "")
            )
            for q in quadrants
        ),
        default=0,
    )

    if n_items == 6:
        if max_desc_len <= 95:
            grid_bounds = calculate_grid_bounds(n=6, top_y=ZEN_GRID_2X3_TOP_Y, gap_y=13.0)
        else:
            grid_bounds = calculate_grid_bounds(n=6, top_y=132.0, gap_y=13.0)
    else:
        if max_desc_len <= 135:
            grid_bounds = calculate_grid_bounds(n=4, top_y=ZEN_GRID_2X2_TOP_Y, gap_y=15.0)
        else:
            grid_bounds = calculate_grid_bounds(n=4)

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_CARD_WHITE},
    ]

    # Universal Header
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    for i, raw_q in enumerate(quadrants):
        q_num = i + 1
        if isinstance(raw_q, QuadrantSpec):
            num_str = f"{int(raw_q.number):02d}" if str(raw_q.number).isdigit() else str(raw_q.number)
            q_title = raw_q.title
            q_desc = raw_q.description
        else:
            num_val = raw_q.get("number") or raw_q.get("quadrant_number") or q_num
            num_str = f"{int(num_val):02d}" if str(num_val).isdigit() else str(num_val)
            q_title = raw_q.get("title", f"Pillar {q_num}")
            q_desc = raw_q.get("description") or raw_q.get("body") or raw_q.get("text") or ""

        box = grid_bounds[i]
        solid_hex, text_hex, _ = google_accent(i)

        quad_id = f"QUAD_S{slide_idx}_Q{q_num}"
        stripe_id = f"STRIPE_S{slide_idx}_Q{q_num}"
        pill_id = f"PILL_S{slide_idx}_Q{q_num}"
        titl_id = f"TITL_S{slide_idx}_Q{q_num}"
        body_id = f"BODY_S{slide_idx}_Q{q_num}"

        # 1. Quadrant Container Shape
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": box.x,
            "y": box.y,
            "width": box.width,
            "height": box.height,
            "background_color": COLOR_CARD_WHITE,
            "id": quad_id,
        })
        ops.append({
            "op": "style-shape",
            "element": quad_id,
            "outline_color": COLOR_CARD_BORDER,
            "outline_weight": 1.0,
        })

        # 2. Top 4-Color Cycling Accent Bar
        q_bar_x, q_bar_w = _round_rect_top_bar_bounds(box.x, box.width, box.height)
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": q_bar_x,
            "y": box.y,
            "width": q_bar_w,
            "height": 3.0,
            "background_color": solid_hex,
            "id": stripe_id,
        })

        if n_items == 6:
            # 2x3 Zen Editorial Card Layout (clean colored number label above Regular title)
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": num_str,
                "x": box.x + 14.0,
                "y": box.y + 8.0,
                "width": 36.0,
                "height": 15.0,
                "font_size": 9.0,
                "bold": True,
                "color": text_hex,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "left",
                "id": pill_id,
            })
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": q_title,
                "x": box.x + 14.0,
                "y": box.y + 24.0,
                "width": box.width - 28.0,
                "height": 20.0,
                "font_size": 12.5,
                "bold": False,
                "color": COLOR_TEXT_PRIMARY,
                "font_family": FONT_FAMILY_HEADING,
                "alignment": "left",
                "id": titl_id,
            })
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": q_desc,
                "x": box.x + 14.0,
                "y": box.y + 45.0,
                "width": box.width - 28.0,
                "height": round(max(36.0, box.height - 50.0), 2),
                "font_size": 10.0,
                "color": COLOR_TEXT_MUTED,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "left",
                "line_spacing": 128,
                "id": body_id,
            })
        else:
            # 2x2 Zen Quadrant Layout (clean colored number label above Regular title)
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": num_str,
                "x": box.x + 16.0,
                "y": box.y + 10.0,
                "width": 40.0,
                "height": 16.0,
                "font_size": 9.5,
                "bold": True,
                "color": text_hex,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "left",
                "id": pill_id,
            })
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": q_title,
                "x": box.x + 16.0,
                "y": box.y + 28.0,
                "width": box.width - 32.0,
                "height": 22.0,
                "font_size": 14.5,
                "bold": False,
                "color": COLOR_TEXT_PRIMARY,
                "font_family": FONT_FAMILY_HEADING,
                "alignment": "left",
                "id": titl_id,
            })
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": q_desc,
                "x": box.x + 16.0,
                "y": box.y + 52.0,
                "width": box.width - 32.0,
                "height": round(max(46.0, box.height - 59.0), 2),
                "font_size": 11.0,
                "color": COLOR_TEXT_MUTED,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "left",
                "line_spacing": 132,
                "id": body_id,
            })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 7: Do / Don't Best Practice Checklist
# =============================================================================


def generate_dodont_checklist(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    dont_items: Union[list[str], dict[str, Any], str],
    do_items: Union[list[str], dict[str, Any], str],
    speaker_notes: str = "",
    dont_title: str = "",
    do_title: str = "",
    takeaway: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 7: Do / Don't Checklist.

    Features: Side-by-side anti-pattern (red banner) vs recommended standard (green banner),
    high-contrast rounded card containers, check/cross bullets, optional synthesis takeaway pill,
    and speaker notes.
    """
    slide_idx = _extract_slide_idx(slide_id)
    col_bounds = calculate_n_column_bounds(n=2, gap=24.0)

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_CARD_WHITE},
    ]

    # Universal Header
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    # Parse Don't and Do Items
    dont_list = dont_items.get("items", []) if isinstance(dont_items, dict) else dont_items
    do_list = do_items.get("items", []) if isinstance(do_items, dict) else do_items

    dont_banner_title = "✗ ANTI-PATTERNS (DON'T)"
    do_banner_title = "✓ RECOMMENDED STANDARD (DO)"

    if dont_title:
        dont_banner_title = dont_title if dont_title.startswith("✗") else f"✗ {dont_title}"
    elif isinstance(dont_items, dict) and "title" in dont_items:
        dont_banner_title = dont_items["title"]

    if do_title:
        do_banner_title = do_title if do_title.startswith("✓") else f"✓ {do_title}"
    elif isinstance(do_items, dict) and "title" in do_items:
        do_banner_title = do_items["title"]

    def _prep_bullets(items: Union[list[str], str], symbol: str) -> str:
        if isinstance(items, str):
            return items
        formatted = []
        for it in items:
            line = it.strip()
            if not line:
                continue
            if not line.startswith("✗") and not line.startswith("✓") and not line.startswith("•"):
                line = f"{symbol} {line}"
            formatted.append(line)
        return "\n".join(formatted)

    dont_body = _prep_bullets(dont_list, "✗")
    do_body = _prep_bullets(do_list, "✓")

    has_takeaway = bool(takeaway and takeaway.strip())
    card_height = col_bounds[0].height - 38.0 if has_takeaway else col_bounds[0].height

    # 1. Left Card: Don't / Anti-Pattern
    box_dont = col_bounds[0]
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "ROUND_RECTANGLE",
        "x": box_dont.x,
        "y": box_dont.y,
        "width": box_dont.width,
        "height": card_height,
        "background_color": COLOR_CARD_WHITE,
        "id": f"CARD_S{slide_idx}_DONT",
    })
    ops.append({
        "op": "style-shape",
        "element": f"CARD_S{slide_idx}_DONT",
        "outline_color": COLOR_CARD_BORDER,
        "outline_weight": 1.0,
    })
    # Top Red Banner Strip
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "RECTANGLE",
        "x": box_dont.x + 1.0,
        "y": box_dont.y + 1.0,
        "width": box_dont.width - 2.0,
        "height": 37.0,
        "background_color": COLOR_RED_LIGHT,
        "id": f"BANNER_S{slide_idx}_DONT",
    })
    # Banner Text
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": dont_banner_title,
        "x": box_dont.x + 14.0,
        "y": box_dont.y + 1.0,
        "width": box_dont.width - 28.0,
        "height": 37.0,
        "font_size": 12.5,
        "bold": True,
        "color": COLOR_RED_TEXT,
        "font_family": FONT_FAMILY_BODY,
        "alignment": "left",
        "content_alignment": "MIDDLE",
        "id": f"TITL_S{slide_idx}_DONT",
    })
    # Banner Bottom Line
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "RECTANGLE",
        "x": box_dont.x + 1.0,
        "y": box_dont.y + 38.0,
        "width": box_dont.width - 2.0,
        "height": 1.0,
        "background_color": COLOR_RED_BORDER,
        "id": f"LINE_S{slide_idx}_DONT",
    })
    # Bullets Body
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": dont_body,
        "x": box_dont.x + 16.0,
        "y": box_dont.y + 48.0,
        "width": box_dont.width - 32.0,
        "height": card_height - 60.0,
        "font_size": FONT_SIZE_CARD_BODY,
        "color": COLOR_TEXT_PRIMARY,
        "font_family": FONT_FAMILY_BODY,
        "alignment": "left",
        "line_spacing": 145,
        "id": f"BODY_S{slide_idx}_DONT",
    })

    # 2. Right Card: Do / Standard
    box_do = col_bounds[1]
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "ROUND_RECTANGLE",
        "x": box_do.x,
        "y": box_do.y,
        "width": box_do.width,
        "height": card_height,
        "background_color": COLOR_CARD_WHITE,
        "id": f"CARD_S{slide_idx}_DO",
    })
    ops.append({
        "op": "style-shape",
        "element": f"CARD_S{slide_idx}_DO",
        "outline_color": COLOR_CARD_BORDER,
        "outline_weight": 1.0,
    })
    # Top Green Banner Strip
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "RECTANGLE",
        "x": box_do.x + 1.0,
        "y": box_do.y + 1.0,
        "width": box_do.width - 2.0,
        "height": 37.0,
        "background_color": COLOR_GREEN_LIGHT,
        "id": f"BANNER_S{slide_idx}_DO",
    })
    # Banner Text
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": do_banner_title,
        "x": box_do.x + 14.0,
        "y": box_do.y + 1.0,
        "width": box_do.width - 28.0,
        "height": 37.0,
        "font_size": 12.5,
        "bold": True,
        "color": COLOR_GREEN_TEXT,
        "font_family": FONT_FAMILY_BODY,
        "alignment": "left",
        "content_alignment": "MIDDLE",
        "id": f"TITL_S{slide_idx}_DO",
    })
    # Banner Bottom Line
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "RECTANGLE",
        "x": box_do.x + 1.0,
        "y": box_do.y + 38.0,
        "width": box_do.width - 2.0,
        "height": 1.0,
        "background_color": COLOR_GREEN_BORDER,
        "id": f"LINE_S{slide_idx}_DO",
    })
    # Bullets Body
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": do_body,
        "x": box_do.x + 16.0,
        "y": box_do.y + 48.0,
        "width": box_do.width - 32.0,
        "height": card_height - 60.0,
        "font_size": FONT_SIZE_CARD_BODY,
        "color": COLOR_TEXT_PRIMARY,
        "font_family": FONT_FAMILY_BODY,
        "alignment": "left",
        "line_spacing": 145,
        "id": f"BODY_S{slide_idx}_DO",
    })

    # 3. Synthesis Footer Takeaway Pill (if provided)
    if has_takeaway:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": takeaway.strip(),
            "x": box_dont.x,
            "y": box_dont.y + card_height + 10.0,
            "width": (box_do.x + box_do.width) - box_dont.x,
            "height": 26.0,
            "font_size": 11.5,
            "bold": True,
            "color": COLOR_BLUE_TEXT,
            "background_color": COLOR_BLUE_LIGHT,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "center",
            "content_alignment": "MIDDLE",
            "id": f"TAKEAWAY_S{slide_idx}_PILL",
        })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 8: Actionable Takeaways & Next Steps
# =============================================================================


def generate_actionable_takeaways(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    principles: list[Union[dict[str, Any], PrincipleSpec]],
    roadmap_title: str,
    roadmap_items: list[str] | str,
    cta_text: str = "EXECUTE BUILD NOW →",
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 8: Actionable Takeaways.

    Features: Asymmetric split layout (3 action principles on left + Editorial
    charcoal `#202124` roadmap and Google Blue CTA button on right).
    """
    slide_idx = _extract_slide_idx(slide_id)
    left_box, right_box = calculate_asymmetric_split_bounds()

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_CARD_WHITE},
    ]

    # Universal Header
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    # =========================================================================
    # Left Panel: 3 Action Principles Container
    # =========================================================================
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "ROUND_RECTANGLE",
        "x": left_box.x,
        "y": left_box.y,
        "width": left_box.width,
        "height": left_box.height,
        "background_color": COLOR_CARD_WHITE,
        "id": f"PANEL_S{slide_idx}_LEFT",
    })
    ops.append({
        "op": "style-shape",
        "element": f"PANEL_S{slide_idx}_LEFT",
        "outline_color": COLOR_CARD_BORDER,
        "outline_weight": 1.0,
    })

    # Render up to 3 principles
    principle_offsets = [
        {"badge_y": 116.0, "titl_y": 116.0, "desc_y": 142.0, "desc_h": 36.0, "div_y": 184.0},
        {"badge_y": 196.0, "titl_y": 196.0, "desc_y": 222.0, "desc_h": 36.0, "div_y": 264.0},
        {"badge_y": 276.0, "titl_y": 276.0, "desc_y": 302.0, "desc_h": 56.0, "div_y": None},
    ]

    for i, raw_p in enumerate(principles[:3]):
        p_num = i + 1
        if isinstance(raw_p, PrincipleSpec):
            num_str = f"{int(raw_p.number):02d}" if str(raw_p.number).isdigit() else str(raw_p.number)
            p_title = raw_p.title
            p_desc = raw_p.description
        elif isinstance(raw_p, dict):
            num_val = raw_p.get("number", p_num)
            num_str = f"{int(num_val):02d}" if str(num_val).isdigit() else str(num_val)
            p_title = raw_p.get("title", f"Principle {p_num}")
            p_desc = raw_p.get("description", "")
        elif isinstance(raw_p, str):
            num_str = f"{p_num:02d}"
            p_title = raw_p
            p_desc = ""
        else:
            num_str = f"{p_num:02d}"
            p_title = getattr(raw_p, "title", f"Principle {p_num}")
            p_desc = getattr(raw_p, "description", "")

        geom = principle_offsets[i]
        _, text_hex, tint_hex = google_accent(i)

        # Number Badge Pill
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": num_str,
            "x": left_box.x + 16.0,
            "y": geom["badge_y"],
            "width": 38.0,
            "height": 24.0,
            "font_size": 11.0,
            "bold": True,
            "color": text_hex,
            "background_color": tint_hex,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "center",
            "content_alignment": "MIDDLE",
            "id": f"PILL_S{slide_idx}_P{p_num}",
        })

        # Principle Title
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": p_title,
            "x": left_box.x + 60.0,
            "y": geom["titl_y"],
            "width": left_box.width - 76.0,
            "height": 24.0,
            "font_size": 14.0,
            "bold": True,
            "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "content_alignment": "MIDDLE",
            "id": f"TITL_S{slide_idx}_P{p_num}",
        })

        # Principle Description
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": p_desc,
            "x": left_box.x + 60.0,
            "y": geom["desc_y"],
            "width": left_box.width - 76.0,
            "height": geom["desc_h"],
            "font_size": 11.5,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "line_spacing": 135,
            "id": f"DESC_S{slide_idx}_P{p_num}",
        })

        # Divider (between 1-2 and 2-3)
        if geom["div_y"] is not None:
            ops.append({
                "op": "add-shape",
                "slide": slide_id,
                "shape_type": "RECTANGLE",
                "x": left_box.x + 16.0,
                "y": geom["div_y"],
                "width": left_box.width - 32.0,
                "height": 1.0,
                "background_color": COLOR_DIVIDER,
                "id": f"DIV_S{slide_idx}_P{p_num}",
            })

    # =========================================================================
    # Right Panel: Editorial Charcoal (#202124) Milestone Roadmap & CTA Button
    # =========================================================================
    clean_roadmap_title = (roadmap_title or "NEXT STEPS & ROADMAP").strip().upper()
    title_len = len(clean_roadmap_title)

    if title_len <= 20:
        rtitle_font_size = 13.0
        rtitle_h = 22.0
        rdiv_y = right_box.y + 40.0
        rbody_y = right_box.y + 48.0
    else:
        rtitle_font_size = 12.0
        rtitle_h = 32.0
        rdiv_y = right_box.y + 52.0
        rbody_y = right_box.y + 60.0

    if cta_text:
        btn_h = 34.0
        btn_y = right_box.y + right_box.height - 44.0
        rbody_h = max(60.0, btn_y - rbody_y - 10.0)
    else:
        btn_h = 0.0
        btn_y = right_box.y + right_box.height
        rbody_h = right_box.height - (rbody_y - right_box.y) - 16.0

    raw_roadmap = roadmap_items or [
        "Phase 1: Planning & Setup",
        "Phase 2: Implementation & Verification",
        "Phase 3: Production Rollout",
    ]
    if isinstance(raw_roadmap, list):
        roadmap_count = len(raw_roadmap)
        roadmap_body = _format_bullets(raw_roadmap)
    else:
        roadmap_count = len(str(raw_roadmap).split("\n"))
        roadmap_body = str(raw_roadmap)

    if roadmap_count >= 4:
        rbody_font_size = 10.5
        rbody_spacing = 120
    else:
        rbody_font_size = 11.5
        rbody_spacing = 130

    # Panel Container
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "ROUND_RECTANGLE",
        "x": right_box.x,
        "y": right_box.y,
        "width": right_box.width,
        "height": right_box.height,
        "background_color": COLOR_DARK_PRIMARY,
        "id": f"PANEL_S{slide_idx}_RIGHT",
    })
    ops.append({
        "op": "style-shape",
        "element": f"PANEL_S{slide_idx}_RIGHT",
        "outline_color": COLOR_DARK_BORDER,
        "outline_weight": 1.0,
    })

    # Panel Title
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": clean_roadmap_title,
        "x": right_box.x + 16.0,
        "y": right_box.y + 14.0,
        "width": right_box.width - 32.0,
        "height": rtitle_h,
        "font_size": rtitle_font_size,
        "bold": True,
        "color": COLOR_TEXT_WHITE,
        "font_family": FONT_FAMILY_HEADING,
        "alignment": "left",
        "id": f"TITL_S{slide_idx}_ROADMAP",
    })

    # Inner Roadmap Divider
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "RECTANGLE",
        "x": right_box.x + 16.0,
        "y": rdiv_y,
        "width": right_box.width - 32.0,
        "height": 1.0,
        "background_color": COLOR_DARK_BORDER,
        "id": f"DIV_S{slide_idx}_ROADMAP",
    })

    # Roadmap Items Body
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": roadmap_body,
        "x": right_box.x + 16.0,
        "y": rbody_y,
        "width": right_box.width - 32.0,
        "height": rbody_h,
        "font_size": rbody_font_size,
        "color": COLOR_DARK_MUTED,
        "font_family": FONT_FAMILY_BODY,
        "alignment": "left",
        "line_spacing": rbody_spacing,
        "id": f"BODY_S{slide_idx}_ROADMAP",
    })

    # Action CTA Button
    if cta_text:
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": right_box.x + 16.0,
            "y": btn_y,
            "width": right_box.width - 32.0,
            "height": btn_h,
            "background_color": COLOR_BLUE_ACCENT,
            "id": f"BTN_S{slide_idx}_CTA",
        })
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": cta_text,
            "x": right_box.x + 16.0,
            "y": btn_y,
            "width": right_box.width - 32.0,
            "height": btn_h,
            "font_size": 11.5,
            "bold": True,
            "color": COLOR_TEXT_WHITE,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "center",
            "content_alignment": "MIDDLE",
            "id": f"BTN_TXT_S{slide_idx}_CTA",
        })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops



# =============================================================================
# Archetype 9: Demo Pivot (Charcoal "switch to live demo" slide)
# =============================================================================


def generate_demo_pivot(
    slide_id: str,
    title: str,
    subtitle: str = "",
    watch_for: Optional[list[str]] = None,
    speaker_notes: str = "",
    kicker: str = "LIVE DEMO",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 9: Demo Pivot.

    Editorial charcoal (`#202124`) slide that signals the switch to a live demo:
    mini 4-color bar, red (`#C5221F`) `▶ LIVE DEMO` pill, large white editorial
    title, optional subtitle, and up to 3 `watch_for` chips.
    """
    slide_idx = _extract_slide_idx(slide_id)
    clean_title = (title or "").strip()
    title_font = 40.0 if len(clean_title) <= 30 else 32.0 if len(clean_title) <= 55 else 26.0
    items = [str(w).strip() for w in (watch_for or []) if str(w).strip()][:3]

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_DARK_PRIMARY},
        *_build_mini_4color_bar(
            slide_id=slide_id,
            prefix=f"MBAR_S{slide_idx}",
            x=36.0,
            y=36.0,
            seg_w=20.0,
            seg_h=3.5,
        ),
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": f"▶ {(kicker or 'LIVE DEMO').upper()}",
            "x": 36.0,
            "y": 90.0,
            "width": 154.0,
            "height": 26.0,
            "font_size": 11.5,
            "bold": True,
            "color": COLOR_TEXT_WHITE,
            "background_color": "#C5221F",
            "font_family": FONT_FAMILY_BODY,
            "alignment": "center",
            "content_alignment": "MIDDLE",
            "id": f"PILL_S{slide_idx}_DEMO",
        },
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": clean_title,
            "x": 36.0,
            "y": 128.0,
            "width": 648.0,
            "height": 96.0,
            "font_size": title_font,
            "bold": False,
            "color": COLOR_TEXT_WHITE,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": f"TITL_S{slide_idx}_DEMO",
        },
    ]

    if subtitle:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": subtitle,
            "x": 36.0,
            "y": 230.0,
            "width": 648.0,
            "height": 40.0,
            "font_size": 15.0,
            "color": COLOR_DARK_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": f"SUBT_S{slide_idx}_DEMO",
        })

    if items:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": "WATCH FOR",
            "x": 36.0,
            "y": 288.0,
            "width": 200.0,
            "height": 16.0,
            "font_size": 10.0,
            "bold": True,
            "color": COLOR_DARK_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": f"WLBL_S{slide_idx}_DEMO",
        })
        gap = 12.0
        chip_w = (648.0 - gap * 2) / 3
        for i, item in enumerate(items):
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": item,
                "x": round(36.0 + i * (chip_w + gap), 2),
                "y": 308.0,
                "width": round(chip_w, 2),
                "height": 32.0,
                "font_size": 12.0,
                "color": COLOR_TEXT_WHITE,
                "background_color": COLOR_DARK_SURFACE,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "center",
                "content_alignment": "MIDDLE",
                "id": f"CHIP_S{slide_idx}_W{i + 1}",
            })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 10: Image Split (diagram / screenshot + bullets)
# =============================================================================

IMAGE_CAPTION_HEIGHT = 22.0
IMAGE_FRAME_PADDING = 8.0


def _normalize_image(image: Any) -> dict[str, Any]:
    if isinstance(image, str):
        return {"url": image} if image.startswith(("http://", "https://")) else {"path": image}
    return dict(image) if isinstance(image, dict) else {}


def generate_image_split(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    image: Union[dict[str, Any], str],
    bullets: Optional[list[str]] = None,
    image_side: str = "right",
    image_layout: str = "split",
    callout: Optional[dict[str, Any]] = None,
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 10: Image Split.

    Supports an optional bottom `callout` walkthrough strip on `image_layout: full`
    (Slides 7–9 Zen architecture step-walkthrough pattern: circular step badge +
    Regular step title + muted explanation + optional right-aligned pillar pill).
    """
    slide_idx = _extract_slide_idx(slide_id)
    img = _normalize_image(image)
    layout = (image_layout or "split").strip().lower()
    side = (image_side or "right").strip().lower()
    caption = str(img.get("caption", "") or "").strip()
    has_callout = layout == "full" and isinstance(callout, dict) and bool(callout)

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_CARD_WHITE},
    ]
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    top_y, height = 100.0, 275.0
    if layout == "full":
        if has_callout:
            img_box = BoundingBox(x=36.0, y=104.0, width=648.0, height=222.0)
        else:
            img_box = BoundingBox(x=36.0, y=top_y, width=648.0, height=height)
        text_box = None
    else:
        text_w, img_w, gap = 256.0, 368.0, 24.0
        if side == "left":
            img_box = BoundingBox(x=36.0, y=top_y, width=img_w, height=height)
            text_box = BoundingBox(x=36.0 + img_w + gap, y=top_y, width=text_w, height=height)
        else:
            text_box = BoundingBox(x=36.0, y=top_y, width=text_w, height=height)
            img_box = BoundingBox(x=36.0 + text_w + gap, y=top_y, width=img_w, height=height)

    # Bullets card
    if text_box is not None:
        card_id = f"CARD_S{slide_idx}_TXT"
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": text_box.x,
            "y": text_box.y,
            "width": text_box.width,
            "height": text_box.height,
            "background_color": COLOR_CARD_WHITE,
            "id": card_id,
        })
        ops.append({
            "op": "style-shape",
            "element": card_id,
            "outline_color": COLOR_CARD_BORDER,
            "outline_weight": 1.0,
        })
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": text_box.x + 2.0,
            "y": text_box.y,
            "width": text_box.width - 4.0,
            "height": 4.0,
            "background_color": COLOR_BLUE_ACCENT,
            "id": f"STRIPE_S{slide_idx}_TXT",
        })
        body = _format_bullets([str(b) for b in (bullets or [])][:4])
        if body:
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": body,
                "x": text_box.x + 16.0,
                "y": text_box.y + 20.0,
                "width": text_box.width - 32.0,
                "height": text_box.height - 36.0,
                "font_size": FONT_SIZE_CARD_BODY,
                "color": COLOR_TEXT_PRIMARY,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "left",
                "id": f"BODY_S{slide_idx}_TXT",
            })

    # Image frame (borderless on full-bleed real images so vector diagrams sit cleanly on white)
    frame_id = f"FRAME_S{slide_idx}_IMG"
    has_real_image = bool(img.get("url") or img.get("path"))
    borderless_full = layout == "full" and has_real_image
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "ROUND_RECTANGLE",
        "x": img_box.x,
        "y": img_box.y,
        "width": img_box.width,
        "height": img_box.height,
        "background_color": COLOR_CARD_WHITE if has_real_image else "#F8F9FA",
        "id": frame_id,
    })
    ops.append({
        "op": "style-shape",
        "element": frame_id,
        "outline_color": COLOR_CARD_WHITE if borderless_full else COLOR_CARD_BORDER,
        "outline_weight": 0.5 if borderless_full else 1.0,
    })

    cap_h = IMAGE_CAPTION_HEIGHT if caption else 0.0
    inner = {
        "x": round(img_box.x + IMAGE_FRAME_PADDING, 2),
        "y": round(img_box.y + IMAGE_FRAME_PADDING, 2),
        "width": round(img_box.width - 2 * IMAGE_FRAME_PADDING, 2),
        "height": round(img_box.height - 2 * IMAGE_FRAME_PADDING - cap_h, 2),
    }
    if img.get("url"):
        ops.append({"op": "add-image", "slide": slide_id, "url": img["url"], **inner})
    elif img.get("path"):
        ops.append({"op": "_pending-image", "slide": slide_id, "path": str(img["path"]),
                    "alt": str(img.get("alt", "")), **inner})
    else:
        placeholder_hint = str(img.get("placeholder") or img.get("hint") or "Inserir diagrama ou screenshot").strip()
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": "ESPAÇO PARA IMAGEM / DIAGRAMA",
            "x": round(img_box.x + 16.0, 2),
            "y": round(img_box.y + img_box.height / 2 - 26.0, 2),
            "width": round(img_box.width - 32.0, 2),
            "height": 22.0,
            "font_size": 8.5,
            "bold": True,
            "color": COLOR_TEXT_MUTED,
            "background_color": "#E8EAED",
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "center",
            "content_alignment": "MIDDLE",
            "id": f"PH_TAG_S{slide_idx}",
        })
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": placeholder_hint,
            "x": round(img_box.x + 16.0, 2),
            "y": round(img_box.y + img_box.height / 2 + 2.0, 2),
            "width": round(img_box.width - 32.0, 2),
            "height": 64.0,
            "font_size": 9.5,
            "italic": True,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "center",
            "line_spacing": 120,
            "id": f"PH_TXT_S{slide_idx}",
        })

    if caption:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": caption,
            "x": inner["x"],
            "y": round(img_box.y + img_box.height - IMAGE_FRAME_PADDING - cap_h, 2),
            "width": inner["width"],
            "height": cap_h,
            "font_size": 10.0,
            "italic": True,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "center",
            "id": f"CAPT_S{slide_idx}_IMG",
        })

    if has_callout and isinstance(callout, dict):
        step_raw = str(callout.get("step") or callout.get("number") or "1").strip()
        c_title = str(callout.get("title") or callout.get("label") or "").strip()
        c_desc = str(
            callout.get("description") or callout.get("detail") or callout.get("subtitle") or ""
        ).strip()
        c_pill = str(callout.get("pill") or callout.get("pillar") or callout.get("tag") or "").strip()
        accent_hint = str(callout.get("accent") or callout.get("color") or "").strip().lower()
        accent_idx_map = {"blue": 0, "red": 1, "yellow": 2, "amber": 2, "green": 3}
        if accent_hint in accent_idx_map:
            c_idx = accent_idx_map[accent_hint]
        elif step_raw.isdigit() and int(step_raw) >= 1:
            c_idx = int(step_raw) - 1
        else:
            c_idx = 0
        step_solid, step_fg, _ = google_accent(c_idx)
        badge_fill = COLOR_BLUE_ACCENT if (c_idx % 4 == 0) else step_fg

        call_bg_id = f"CALL_BG_S{slide_idx}"
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": 36.0,
            "y": 336.0,
            "width": 648.0,
            "height": 42.0,
            "background_color": COLOR_BG_LIGHT,
            "id": call_bg_id,
        })
        ops.append({
            "op": "style-shape",
            "element": call_bg_id,
            "outline_color": "#E8EAED",
            "outline_weight": 1.0,
        })

        bdg_id = f"CALL_BDG_S{slide_idx}"
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ELLIPSE",
            "x": 48.0,
            "y": 345.0,
            "width": 24.0,
            "height": 24.0,
            "background_color": badge_fill,
            "id": bdg_id,
        })
        ops.append({
            "op": "style-shape",
            "element": bdg_id,
            "outline_color": badge_fill,
            "outline_weight": 0.5,
        })
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": step_raw,
            "x": 42.0,
            "y": 345.0,
            "width": 36.0,
            "height": 24.0,
            "font_size": 10.0,
            "bold": True,
            "color": COLOR_TEXT_WHITE,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "center",
            "content_alignment": "MIDDLE",
            "id": f"CALL_NUM_S{slide_idx}",
        })

        pill_w = round(min(156.0, max(92.0, len(c_pill) * 6.2 + 24.0)), 2) if c_pill else 0.0
        txt_w = round(648.0 - 54.0 - (pill_w + 18.0 if c_pill else 12.0), 2)
        if c_title and c_desc:
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": c_title,
                "x": 80.0,
                "y": 339.0,
                "width": txt_w,
                "height": 17.0,
                "font_size": 11.0,
                "bold": False,
                "color": COLOR_TEXT_PRIMARY,
                "font_family": FONT_FAMILY_HEADING,
                "alignment": "left",
                "content_alignment": "MIDDLE",
                "id": f"CALL_TITL_S{slide_idx}",
            })
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": c_desc,
                "x": 80.0,
                "y": 357.0,
                "width": txt_w,
                "height": 17.0,
                "font_size": 9.0,
                "color": COLOR_TEXT_MUTED,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "left",
                "content_alignment": "MIDDLE",
                "id": f"CALL_DESC_S{slide_idx}",
            })
        elif c_title or c_desc:
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": c_title or c_desc,
                "x": 80.0,
                "y": 336.0,
                "width": txt_w,
                "height": 42.0,
                "font_size": 11.0,
                "bold": False,
                "color": COLOR_TEXT_PRIMARY,
                "font_family": FONT_FAMILY_HEADING,
                "alignment": "left",
                "content_alignment": "MIDDLE",
                "id": f"CALL_TITL_S{slide_idx}",
            })

        if c_pill:
            pill_x = round(684.0 - 12.0 - pill_w, 2)
            call_pill_id = f"CALL_PILL_BG_S{slide_idx}"
            ops.append({
                "op": "add-shape",
                "slide": slide_id,
                "shape_type": "ROUND_RECTANGLE",
                "x": pill_x,
                "y": 345.0,
                "width": pill_w,
                "height": 24.0,
                "background_color": COLOR_CARD_WHITE,
                "id": call_pill_id,
            })
            ops.append({
                "op": "style-shape",
                "element": call_pill_id,
                "outline_color": step_solid,
                "outline_weight": 1.25,
            })
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": c_pill,
                "x": pill_x,
                "y": 345.0,
                "width": pill_w,
                "height": 24.0,
                "font_size": 8.5,
                "bold": True,
                "color": step_fg,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "center",
                "content_alignment": "MIDDLE",
                "id": f"CALL_PILL_TXT_S{slide_idx}",
            })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 12: Workstream Card (Initiative Template: Image/Placeholder + Grid)
# =============================================================================


def generate_workstream_card(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    image: Optional[Union[dict[str, Any], str]] = None,
    tempo: str = "",
    receita: str = "",
    desafios: Optional[Union[list[str], str]] = None,
    diferenciais: Optional[Union[list[str], str]] = None,
    acoes: Optional[Union[list[str], str]] = None,
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 12: Workstream Card."""
    slide_idx = _extract_slide_idx(slide_id)
    img = _normalize_image(image) if image else {}

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_CARD_WHITE},
    ]
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    # 1. Left Panel: Image or Placeholder Drop-Zone (X=36, Y=106, W=220, H=264)
    img_x, img_y, img_w, img_h = 36.0, 106.0, 220.0, 264.0
    has_real_img = bool(img.get("url") or img.get("path"))
    frame_id = f"WS_IMG_S{slide_idx}"
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "ROUND_RECTANGLE",
        "x": img_x,
        "y": img_y,
        "width": img_w,
        "height": img_h,
        "background_color": COLOR_CARD_WHITE if has_real_img else "#F8F9FA",
        "id": frame_id,
    })
    ops.append({
        "op": "style-shape",
        "element": frame_id,
        "outline_color": COLOR_CARD_BORDER,
        "outline_weight": 1.0,
    })
    if img.get("url"):
        ops.append({
            "op": "add-image", "slide": slide_id, "url": img["url"],
            "x": img_x + 8.0, "y": img_y + 8.0, "width": img_w - 16.0, "height": img_h - 16.0,
        })
    elif img.get("path"):
        ops.append({
            "op": "_pending-image", "slide": slide_id, "path": str(img["path"]),
            "alt": str(img.get("alt", "")),
            "x": img_x + 8.0, "y": img_y + 8.0, "width": img_w - 16.0, "height": img_h - 16.0,
        })
    else:
        ph_text = str(img.get("placeholder") or img.get("hint") or "Inserir diagrama de arquitetura ou print").strip()
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": "ESPAÇO PARA IMAGEM / DIAGRAMA",
            "x": 50.0,
            "y": 196.0,
            "width": 192.0,
            "height": 22.0,
            "font_size": 8.0,
            "bold": True,
            "color": COLOR_TEXT_MUTED,
            "background_color": "#E8EAED",
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "center",
            "content_alignment": "MIDDLE",
            "id": f"WS_PHTAG_S{slide_idx}",
        })
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": ph_text,
            "x": 48.0,
            "y": 224.0,
            "width": 196.0,
            "height": 64.0,
            "font_size": 9.0,
            "italic": True,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "center",
            "line_spacing": 120,
            "id": f"WS_PHTXT_S{slide_idx}",
        })

    # 2. Right Top Row: 2 KPI Pills (Y=106, H=40, W=201 each)
    for idx_p, (px, lbl, val, bg, fg, brd) in enumerate([
        (270.0, "TEMPO / MATURIDADE", tempo or "Agora (Curto Prazo)", COLOR_BLUE_LIGHT, COLOR_BLUE_TEXT, "#AECBFA"),
        (483.0, "POTENCIAL DE RECEITA", receita or "A dimensionar", "#E6F4EA", "#137333", "#A8DAB5"),
    ], start=1):
        pid = f"WS_PILL_S{slide_idx}_{idx_p}"
        ops.append({
            "op": "add-shape", "slide": slide_id, "shape_type": "ROUND_RECTANGLE",
            "x": px, "y": 106.0, "width": 201.0, "height": 40.0,
            "background_color": bg, "id": pid,
        })
        ops.append({
            "op": "style-shape", "element": pid, "outline_color": brd, "outline_weight": 1.0,
        })
        ops.append({
            "op": "add-textbox", "slide": slide_id, "text": lbl,
            "x": px + 10.0, "y": 109.0, "width": 181.0, "height": 14.0,
            "font_size": 7.5, "bold": True, "color": fg,
            "font_family": FONT_FAMILY_HEADING, "alignment": "left",
            "content_alignment": "MIDDLE",
            "id": f"WS_PLBL_S{slide_idx}_{idx_p}",
        })
        ops.append({
            "op": "add-textbox", "slide": slide_id, "text": str(val),
            "x": px + 10.0, "y": 123.5, "width": 181.0, "height": 19.0,
            "font_size": 9.0, "bold": True, "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_BODY, "alignment": "left",
            "content_alignment": "MIDDLE",
            "id": f"WS_PVAL_S{slide_idx}_{idx_p}",
        })

    # 3. Right Middle Row: Desafios vs. Diferenciais (Y=154, H=114, W=201 each)
    for idx_c, (cx, stripe, hdr_col, hdr_txt, items) in enumerate([
        (270.0, "#EA4335", "#C5221F", "RISCOS & DESAFIOS", desafios or []),
        (483.0, "#34A853", "#137333", "DIFERENCIAIS GOOGLE", diferenciais or []),
    ], start=1):
        cid = f"WS_CARD_S{slide_idx}_{idx_c}"
        ops.append({
            "op": "add-shape", "slide": slide_id, "shape_type": "ROUND_RECTANGLE",
            "x": cx, "y": 154.0, "width": 201.0, "height": 114.0,
            "background_color": COLOR_CARD_WHITE, "id": cid,
        })
        ops.append({
            "op": "style-shape", "element": cid, "outline_color": COLOR_CARD_BORDER, "outline_weight": 1.0,
        })
        ops.append({
            "op": "add-shape", "slide": slide_id, "shape_type": "RECTANGLE",
            "x": cx + 2.0, "y": 154.0, "width": 197.0, "height": 4.0,
            "background_color": stripe, "id": f"WS_BAR_S{slide_idx}_{idx_c}",
        })
        ops.append({
            "op": "add-textbox", "slide": slide_id, "text": hdr_txt,
            "x": cx + 10.0, "y": 162.0, "width": 181.0, "height": 16.0,
            "font_size": 8.5, "bold": True, "color": hdr_col,
            "font_family": FONT_FAMILY_HEADING, "alignment": "left",
            "id": f"WS_CHDR_S{slide_idx}_{idx_c}",
        })
        b_list = [items] if isinstance(items, str) else list(items)
        ops.append({
            "op": "add-textbox", "slide": slide_id, "text": _format_bullets(b_list[:4]),
            "x": cx + 10.0, "y": 179.0, "width": 181.0, "height": 84.0,
            "font_size": 8.5, "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_BODY, "alignment": "left", "line_spacing": 118,
            "id": f"WS_CBDY_S{slide_idx}_{idx_c}",
        })

    # 4. Right Bottom Row: Ações / O que fazer? (X=270, Y=276, W=414, H=94)
    act_id = f"WS_ACT_S{slide_idx}"
    ops.append({
        "op": "add-shape", "slide": slide_id, "shape_type": "ROUND_RECTANGLE",
        "x": 270.0, "y": 276.0, "width": 414.0, "height": 94.0,
        "background_color": "#FEF7E0", "id": act_id,
    })
    ops.append({
        "op": "style-shape", "element": act_id, "outline_color": "#FDE293", "outline_weight": 1.0,
    })
    ops.append({
        "op": "add-shape", "slide": slide_id, "shape_type": "RECTANGLE",
        "x": 272.0, "y": 276.0, "width": 410.0, "height": 4.0,
        "background_color": "#FBBC04", "id": f"WS_ACTBAR_S{slide_idx}",
    })
    ops.append({
        "op": "add-textbox", "slide": slide_id,
        "text": "AÇÕES / O QUE FAZER? (PLANO & QUESTÕES EM ABERTO)",
        "x": 280.0, "y": 283.0, "width": 394.0, "height": 15.0,
        "font_size": 8.0, "bold": True, "color": COLOR_AMBER_DARK,
        "font_family": FONT_FAMILY_HEADING, "alignment": "left",
        "id": f"WS_ACTHDR_S{slide_idx}",
    })
    act_list = [acoes] if isinstance(acoes, str) else list(acoes or [])
    ops.append({
        "op": "add-textbox", "slide": slide_id,
        "text": _format_bullets(act_list[:4]),
        "x": 280.0, "y": 299.0, "width": 394.0, "height": 68.0,
        "font_size": 8.5, "color": COLOR_TEXT_PRIMARY,
        "font_family": FONT_FAMILY_BODY, "alignment": "left", "line_spacing": 116,
        "id": f"WS_ACTBDY_S{slide_idx}",
    })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 13: Editorial Cover (Evolution Breadcrumbs + Clean White Cover)
# =============================================================================


def generate_cover(
    slide_id: str,
    title: str,
    subtitle: str = "",
    kicker: str = "",
    breadcrumbs: Optional[list[Union[str, dict[str, Any]]]] = None,
    date: str = "",
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 13: Editorial Cover (Slide 1 style).

    Zen Editorial Cover: Pure white canvas, crisp outlined evolution breadcrumb pills
    (`A → B → [C]` where the active pill is `#FFFFFF` with `1.5pt #1A73E8` outline,
    or a 4-color mini bar when `breadcrumbs` are omitted), large `Google Sans` Regular
    headline, muted subtitle, and clean borderless bottom-left date/context line.
    """
    slide_idx = _extract_slide_idx(slide_id)
    clean_title = (title or "Presentation Title").strip()
    t_len = len(clean_title)
    title_font = 48.0 if t_len <= 28 else 40.0 if t_len <= 52 else 32.0

    crumbs = list(breadcrumbs or [])[:4]
    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_CARD_WHITE},
        *_build_mini_4color_bar(
            slide_id=slide_id,
            prefix=f"MBAR_S{slide_idx}",
            x=36.0,
            y=34.0,
            seg_w=20.0,
            seg_h=3.5,
        ),
    ]

    if crumbs:
        has_any_explicit_active = any(isinstance(c, dict) and "active" in c for c in crumbs)
        cur_x = 36.0
        crumb_y = 56.0
        for idx, raw_c in enumerate(crumbs):
            if isinstance(raw_c, dict):
                lbl = str(raw_c.get("label") or raw_c.get("title") or f"Stage {idx + 1}").strip()
                is_active = bool(raw_c.get("active", False))
            else:
                lbl = str(raw_c).strip()
                is_active = (not has_any_explicit_active) and (idx == len(crumbs) - 1)

            cw = round(min(210.0, max(84.0, len(lbl) * 6.5 + 24.0)), 2)
            if cur_x + cw > 684.0:
                cw = max(72.0, round(684.0 - cur_x, 2))

            pill_id = f"CRUMB_BG_S{slide_idx}_{idx + 1}"
            ops.append({
                "op": "add-shape",
                "slide": slide_id,
                "shape_type": "ROUND_RECTANGLE",
                "x": round(cur_x, 2),
                "y": crumb_y,
                "width": cw,
                "height": 26.0,
                "background_color": COLOR_CARD_WHITE,
                "id": pill_id,
            })
            ops.append({
                "op": "style-shape",
                "element": pill_id,
                "outline_color": COLOR_BLUE_ACCENT if is_active else COLOR_CARD_BORDER,
                "outline_weight": 1.5 if is_active else 1.0,
            })
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": lbl,
                "x": round(cur_x, 2),
                "y": crumb_y,
                "width": cw,
                "height": 26.0,
                "font_size": 9.5,
                "bold": is_active,
                "color": COLOR_BLUE_TEXT if is_active else COLOR_TEXT_MUTED,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "center",
                "content_alignment": "MIDDLE",
                "id": f"CRUMB_TXT_S{slide_idx}_{idx + 1}",
            })
            cur_x += cw
            if idx < len(crumbs) - 1 and cur_x + 24.0 < 684.0:
                ops.append({
                    "op": "add-textbox",
                    "slide": slide_id,
                    "text": "→",
                    "x": round(cur_x + 2.0, 2),
                    "y": crumb_y,
                    "width": 18.0,
                    "height": 26.0,
                    "font_size": 11.0,
                    "bold": False,
                    "color": COLOR_TEXT_MUTED,
                    "font_family": FONT_FAMILY_BODY,
                    "alignment": "center",
                    "content_alignment": "MIDDLE",
                    "id": f"CRUMB_ARR_S{slide_idx}_{idx + 1}",
                })
                cur_x += 22.0

    if kicker and kicker.strip():
        kick_y = 96.0 if crumbs else 64.0
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": kicker.strip().upper(),
            "x": 36.0,
            "y": kick_y,
            "width": 520.0,
            "height": 18.0,
            "font_size": 9.5,
            "bold": True,
            "color": COLOR_BLUE_TEXT,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": f"KICK_S{slide_idx}_COV",
        })

    title_y = 132.0 if (crumbs or kicker) else 118.0
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": clean_title,
        "x": 36.0,
        "y": title_y,
        "width": 636.0,
        "height": 116.0,
        "font_size": title_font,
        "bold": False,
        "color": COLOR_TEXT_PRIMARY,
        "font_family": FONT_FAMILY_HEADING,
        "alignment": "left",
        "line_spacing": 114,
        "id": f"TITL_S{slide_idx}_COV",
    })

    if subtitle:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": subtitle,
            "x": 36.0,
            "y": 258.0,
            "width": 580.0,
            "height": 64.0,
            "font_size": 15.5,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "line_spacing": 135,
            "id": f"SUBT_S{slide_idx}_COV",
        })

    if date:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": date,
            "x": 36.0,
            "y": 352.0,
            "width": 520.0,
            "height": 22.0,
            "font_size": 10.5,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": f"DATE_S{slide_idx}_COV",
        })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 14: Statement Pivot (Full-Bleed Google Blue or Charcoal Thesis)
# =============================================================================


def generate_statement_pivot(
    slide_id: str,
    title: str,
    subtitle: str = "",
    kicker: str = "",
    variant: str = "blue",
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 14: Statement Pivot (Slides 3 & 13).

    Supports two Zen editorial variants:
      - `blue`: Google Blue (`#1A73E8`) full-bleed thesis ("THE SHORT ANSWER" style).
      - `dark`: Charcoal (`#202124`) full-bleed provocation / rhetorical question.
    """
    slide_idx = _extract_slide_idx(slide_id)
    v = (variant or "blue").strip().lower()
    is_dark = v in ("dark", "charcoal", "black", "provocation")

    clean_title = (title or "").strip()
    t_len = len(clean_title)
    title_font = 38.0 if t_len <= 58 else 32.0 if t_len <= 100 else 26.0

    bg_color = COLOR_DARK_PRIMARY if is_dark else COLOR_BLUE_ACCENT
    bar_colors = (
        ("#1A73E8", "#EA4335", "#FBBC04", "#34A853")
        if is_dark
        else ("#FFFFFF", "#EA4335", "#FBBC04", "#34A853")
    )
    kicker_color = "#FBBC04" if is_dark else COLOR_TEXT_WHITE
    sub_color = COLOR_DARK_MUTED if is_dark else COLOR_TEXT_WHITE

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": bg_color},
        *_build_mini_4color_bar(
            slide_id=slide_id,
            prefix=f"MBAR_S{slide_idx}",
            x=36.0,
            y=44.0,
            seg_w=20.0,
            seg_h=3.5,
            colors=bar_colors,
        ),
    ]

    if kicker and kicker.strip():
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": kicker.strip().upper(),
            "x": 36.0,
            "y": 64.0,
            "width": 620.0,
            "height": 20.0,
            "font_size": 10.0,
            "bold": True,
            "color": kicker_color,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": f"KICK_S{slide_idx}_STMT",
        })

    title_y = 114.0 if subtitle else 130.0
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": clean_title,
        "x": 36.0,
        "y": title_y,
        "width": 636.0,
        "height": 156.0,
        "font_size": title_font,
        "bold": False,
        "color": COLOR_TEXT_WHITE,
        "font_family": FONT_FAMILY_HEADING,
        "alignment": "left",
        "line_spacing": 122,
        "id": f"TITL_S{slide_idx}_STMT",
    })

    if subtitle:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": subtitle,
            "x": 36.0,
            "y": 280.0,
            "width": 620.0,
            "height": 72.0,
            "font_size": 14.5,
            "color": sub_color,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "line_spacing": 135,
            "id": f"SUBT_S{slide_idx}_STMT",
        })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 15: Capability Matrix (Semantic Pill Heat-Matrix)
# =============================================================================


def _resolve_matrix_cell_palette(status: str, text: str) -> tuple[str, str, str]:
    """Returns WCAG-AA-safe (bg_hex, fg_hex, border_hex) for a matrix cell."""
    key = (status or "").strip().lower().replace("-", "_").replace(" ", "_")
    if not key:
        low = text.strip().lower()
        if any(k in low for k in ("native", "nativo", "pronto", "built-in", "yes", "sim", "✓")):
            key = "native"
        elif any(k in low for k in ("partial", "parcial", "manual", "medium", "médio")):
            key = "partial"
        elif any(k in low for k in ("gap", "plugin", "custom", "lacuna", "risco", "none", "✗")):
            key = "gap"
        elif any(k in low for k in ("block", "bloco", "platform", "plataforma", "vertex")):
            key = "building_blocks"

    if key in ("native", "done", "yes", "green", "strong", "ready"):
        return COLOR_GREEN_LIGHT, COLOR_GREEN_TEXT, COLOR_GREEN_BORDER
    if key in ("partial", "warn", "warning", "yellow", "amber", "medium"):
        return COLOR_AMBER_LIGHT, COLOR_AMBER_DARK, "#FDE293"
    if key in ("gap", "plugin", "no", "red", "risk", "custom", "missing"):
        return COLOR_RED_LIGHT, COLOR_RED_TEXT, COLOR_RED_BORDER
    if key in ("building_blocks", "blocks", "platform", "blue", "foundation"):
        return COLOR_BLUE_LIGHT, COLOR_BLUE_TEXT, "#AECBFA"
    if key in ("cobuild", "co_build", "orange"):
        return COLOR_ORANGE_TINT, COLOR_AMBER_DARK, COLOR_ORANGE_COBUILD
    return "#F8F9FA", COLOR_TEXT_BODY, COLOR_CARD_BORDER


def generate_capability_matrix(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    columns: list[Union[str, dict[str, Any]]],
    rows: list[dict[str, Any]],
    footnote: str = "",
    row_label_header: str = "",
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 15: Capability Matrix (Slide 4 style).

    Zen Editorial comparison matrix:
      - Floating Regular `#202124` column headers for standard columns (no heavy gray boxes),
        with a crisp `#FFFFFF` + `1.5pt #1A73E8` outline header for highlighted target columns.
      - Regular `#202124` row labels (plus optional `sublabel`).
      - Borderless pastel semantic cells (`native`, `partial`, `gap`, `building_blocks`) with
        left-aligned status labels, optional 2nd-line `detail` subtext, and true vector
        dashed `#E37400` co-build overlay (`dash="DASH"`) when `highlight: true`.
    """
    slide_idx = _extract_slide_idx(slide_id)
    cols_clean = list(columns or [])[:5]
    rows_clean = list(rows or [])[:7]
    if len(cols_clean) < 2:
        raise ValueError("Capability matrix requires at least 2 columns")
    if len(rows_clean) < 1:
        raise ValueError("Capability matrix requires at least 1 row")

    n_cols = len(cols_clean)
    n_rows = len(rows_clean)

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_CARD_WHITE},
    ]
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    lbl_w = 180.0 if n_cols <= 3 else 156.0 if n_cols == 4 else 136.0
    col_gap = 8.0
    rem_w = 648.0 - lbl_w - n_cols * col_gap
    col_w = rem_w / n_cols

    def _col_x(c: int) -> float:
        return round(36.0 + lbl_w + col_gap + c * (col_w + col_gap), 2)

    has_col_sub = any(
        isinstance(c, dict) and bool(str(c.get("subtitle") or c.get("sublabel") or "").strip())
        for c in cols_clean
    )
    hdr_y = 100.0
    hdr_h = 38.0 if has_col_sub else 28.0
    if row_label_header:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": row_label_header.upper(),
            "x": 36.0,
            "y": hdr_y,
            "width": round(lbl_w - 4.0, 2),
            "height": hdr_h,
            "font_size": 8.5,
            "bold": True,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "content_alignment": "MIDDLE",
            "id": f"MHDR_RLBL_S{slide_idx}",
        })

    for c_idx, raw_col in enumerate(cols_clean):
        cx = _col_x(c_idx)
        cw = round(col_w, 2)
        if isinstance(raw_col, dict):
            c_label = str(raw_col.get("label") or raw_col.get("title") or f"Option {c_idx + 1}")
            c_sub = str(raw_col.get("subtitle") or raw_col.get("sublabel") or "").strip()
            hi_raw = raw_col.get("highlight", "")
            hi_mode = "outline" if hi_raw is True else str(hi_raw or "").strip().lower()
        else:
            c_label = str(raw_col)
            c_sub = ""
            hi_mode = ""

        is_solid = hi_mode == "solid"
        is_outline = hi_mode in ("outline", "target", "recommended", "true")
        if is_solid or is_outline:
            h_bg = COLOR_BLUE_ACCENT if is_solid else COLOR_CARD_WHITE
            h_fg = COLOR_TEXT_WHITE if is_solid else COLOR_BLUE_TEXT
            h_sub_fg = COLOR_TEXT_WHITE if is_solid else COLOR_TEXT_MUTED
            hdr_bg_id = f"MHDR_BG_S{slide_idx}_C{c_idx + 1}"
            ops.append({
                "op": "add-shape",
                "slide": slide_id,
                "shape_type": "ROUND_RECTANGLE",
                "x": cx,
                "y": hdr_y,
                "width": cw,
                "height": hdr_h,
                "background_color": h_bg,
                "id": hdr_bg_id,
            })
            ops.append({
                "op": "style-shape",
                "element": hdr_bg_id,
                "outline_color": COLOR_BLUE_ACCENT,
                "outline_weight": 1.5,
            })
        else:
            h_fg = COLOR_TEXT_PRIMARY
            h_sub_fg = COLOR_TEXT_MUTED

        if c_sub:
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": c_label,
                "x": cx,
                "y": round(hdr_y + 3.0, 2),
                "width": cw,
                "height": 16.0,
                "font_size": 10.0,
                "bold": False,
                "color": h_fg,
                "font_family": FONT_FAMILY_HEADING,
                "alignment": "center",
                "content_alignment": "MIDDLE",
                "id": f"MHDR_TXT_S{slide_idx}_C{c_idx + 1}",
            })
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": c_sub,
                "x": cx,
                "y": round(hdr_y + 19.5, 2),
                "width": cw,
                "height": 15.5,
                "font_size": 8.0,
                "color": h_sub_fg,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "center",
                "content_alignment": "MIDDLE",
                "id": f"MHDR_SUB_S{slide_idx}_C{c_idx + 1}",
            })
        else:
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": c_label,
                "x": cx,
                "y": hdr_y,
                "width": cw,
                "height": hdr_h,
                "font_size": 10.5,
                "bold": False,
                "color": h_fg,
                "font_family": FONT_FAMILY_HEADING,
                "alignment": "center",
                "content_alignment": "MIDDLE",
                "id": f"MHDR_TXT_S{slide_idx}_C{c_idx + 1}",
            })

    rows_top = hdr_y + hdr_h + 8.0
    rows_bottom = 350.0 if footnote else 374.0
    avail_h = rows_bottom - rows_top
    row_gap = 6.0 if n_rows <= 5 else 4.0
    row_h = min(44.0, (avail_h - (n_rows - 1) * row_gap) / n_rows)

    dash_canvas = RawCanvas(slide_id, f"MCELL_S{slide_idx}")

    for r_idx, raw_row in enumerate(rows_clean):
        ry = round(rows_top + r_idx * (row_h + row_gap), 2)
        rh = round(row_h, 2)
        cap_label = str(
            raw_row.get("capability")
            or raw_row.get("label")
            or raw_row.get("title")
            or f"Capability {r_idx + 1}"
        )
        cap_sub = str(raw_row.get("sublabel") or raw_row.get("subtitle") or "").strip()
        if cap_sub and rh >= 34.0:
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": cap_label,
                "x": 36.0,
                "y": round(ry + 3.0, 2),
                "width": round(lbl_w - 4.0, 2),
                "height": 15.5,
                "font_size": 10.0 if n_rows <= 5 else 9.0,
                "bold": False,
                "color": COLOR_TEXT_PRIMARY,
                "font_family": FONT_FAMILY_HEADING,
                "alignment": "left",
                "content_alignment": "MIDDLE",
                "id": f"MROW_LBL_S{slide_idx}_R{r_idx + 1}",
            })
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": cap_sub,
                "x": 36.0,
                "y": round(ry + 19.0, 2),
                "width": round(lbl_w - 4.0, 2),
                "height": round(max(14.0, rh - 21.0), 2),
                "font_size": 8.0,
                "color": COLOR_TEXT_MUTED,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "left",
                "content_alignment": "MIDDLE",
                "id": f"MROW_SUB_S{slide_idx}_R{r_idx + 1}",
            })
        else:
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": cap_label,
                "x": 36.0,
                "y": ry,
                "width": round(lbl_w - 4.0, 2),
                "height": rh,
                "font_size": 10.0 if n_rows <= 5 else 9.0,
                "bold": False,
                "color": COLOR_TEXT_PRIMARY,
                "font_family": FONT_FAMILY_HEADING,
                "alignment": "left",
                "content_alignment": "MIDDLE",
                "id": f"MROW_LBL_S{slide_idx}_R{r_idx + 1}",
            })

        raw_cells = raw_row.get("cells") or raw_row.get("values") or []
        for c_idx in range(n_cols):
            cx = _col_x(c_idx)
            cw = round(col_w, 2)
            raw_cell = raw_cells[c_idx] if c_idx < len(raw_cells) else ""
            if isinstance(raw_cell, dict):
                c_txt = str(raw_cell.get("text") or raw_cell.get("label") or raw_cell.get("value") or "—")
                c_det = str(raw_cell.get("detail") or raw_cell.get("subtext") or raw_cell.get("subtitle") or "").strip()
                c_stat = str(raw_cell.get("status") or "")
                c_hi = bool(raw_cell.get("highlight", False))
            else:
                c_txt = str(raw_cell) if str(raw_cell).strip() else "—"
                c_det = ""
                c_stat = ""
                c_hi = False

            bg, fg, _ = _resolve_matrix_cell_palette(c_stat, c_txt)

            cell_bg_id = f"MCELL_BG_S{slide_idx}_R{r_idx + 1}_C{c_idx + 1}"
            ops.append({
                "op": "add-shape",
                "slide": slide_id,
                "shape_type": "ROUND_RECTANGLE",
                "x": cx,
                "y": ry,
                "width": cw,
                "height": rh,
                "background_color": bg,
                "id": cell_bg_id,
            })
            # Borderless pastel fill (matching outline to fill suppresses Google Slides default border)
            ops.append({
                "op": "style-shape",
                "element": cell_bg_id,
                "outline_color": bg,
                "outline_weight": 0.5,
            })

            if c_det and rh >= 32.0:
                ops.append({
                    "op": "add-textbox",
                    "slide": slide_id,
                    "text": c_txt,
                    "x": round(cx + 4.0, 2),
                    "y": round(ry + 3.0, 2),
                    "width": round(cw - 8.0, 2),
                    "height": 15.0,
                    "font_size": 8.8 if n_rows <= 5 else 8.2,
                    "bold": True,
                    "color": fg,
                    "font_family": FONT_FAMILY_BODY,
                    "alignment": "left",
                    "content_alignment": "MIDDLE",
                    "id": f"MCELL_TXT_S{slide_idx}_R{r_idx + 1}_C{c_idx + 1}",
                })
                ops.append({
                    "op": "add-textbox",
                    "slide": slide_id,
                    "text": c_det,
                    "x": round(cx + 4.0, 2),
                    "y": round(ry + 18.5, 2),
                    "width": round(cw - 8.0, 2),
                    "height": round(max(13.5, rh - 20.5), 2),
                    "font_size": 7.8,
                    "color": COLOR_TEXT_BODY,
                    "font_family": FONT_FAMILY_BODY,
                    "alignment": "left",
                    "content_alignment": "MIDDLE",
                    "id": f"MCELL_DET_S{slide_idx}_R{r_idx + 1}_C{c_idx + 1}",
                })
            else:
                ops.append({
                    "op": "add-textbox",
                    "slide": slide_id,
                    "text": c_txt,
                    "x": round(cx + 4.0, 2),
                    "y": ry,
                    "width": round(cw - 8.0, 2),
                    "height": rh,
                    "font_size": 9.0 if n_rows <= 5 else 8.5,
                    "bold": True,
                    "color": fg,
                    "font_family": FONT_FAMILY_BODY,
                    "alignment": "left",
                    "content_alignment": "MIDDLE",
                    "id": f"MCELL_TXT_S{slide_idx}_R{r_idx + 1}_C{c_idx + 1}",
                })

            if c_hi:
                dash_canvas.shape(
                    f"DASH_R{r_idx + 1}_C{c_idx + 1}",
                    "ROUND_RECTANGLE",
                    cx,
                    ry,
                    cw,
                    rh,
                    fill=None,
                    outline=COLOR_ORANGE_COBUILD,
                    weight=1.75,
                    dash="DASH",
                )

    if dash_canvas.requests:
        ops.append({"op": "_raw-requests", "slide": slide_id, "requests": dash_canvas.requests})

    if footnote:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": footnote,
            "x": 36.0,
            "y": 356.0,
            "width": 648.0,
            "height": 22.0,
            "font_size": 9.0,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": f"MFNOTE_S{slide_idx}",
        })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 16: KPI Spotlight (Big Blue Hero Number + "Measured By" List)
# =============================================================================


def generate_kpi_spotlight(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    stat_value: str,
    stat_label: str = "",
    stat_description: str = "",
    status_pill: str = "",
    measured_by_title: str = "MEASURED BY",
    measurements: Optional[list[Union[dict[str, Any], str]]] = None,
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 16: KPI Spotlight (Slide 11 style).

    Zen Editorial KPI Spotlight (pure negative space between columns — no vertical line):
      - Left column: Huge `72pt` Google Blue (`#1A73E8`) Regular figure + Regular label +
        muted description + optional borderless green live status pill.
      - Right column: Uppercase `MEASURED BY` kicker + 2–4 rows separated by hairline
        horizontal rules with Google 4-color `ELLIPSE` dots and Regular metric titles.
    """
    slide_idx = _extract_slide_idx(slide_id)
    val_clean = (stat_value or "0").strip()
    stat_font = 72.0 if len(val_clean) <= 4 else 56.0 if len(val_clean) <= 8 else 40.0

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_CARD_WHITE},
    ]
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    # Left Column: Big Hero Stat + Regular Framing + Optional Borderless Live Pill
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": val_clean,
        "x": 36.0,
        "y": 130.0,
        "width": 292.0,
        "height": 84.0,
        "font_size": stat_font,
        "bold": False,
        "color": COLOR_BLUE_ACCENT,
        "font_family": FONT_FAMILY_HEADING,
        "alignment": "left",
        "id": f"KSPOT_VAL_S{slide_idx}",
    })

    cur_left_y = 220.0
    if stat_label:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": stat_label,
            "x": 36.0,
            "y": cur_left_y,
            "width": 292.0,
            "height": 24.0,
            "font_size": 14.0,
            "bold": False,
            "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": f"KSPOT_LBL_S{slide_idx}",
        })
        cur_left_y += 28.0

    if stat_description:
        desc_bottom = 328.0 if status_pill else 368.0
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": stat_description,
            "x": 36.0,
            "y": cur_left_y,
            "width": 292.0,
            "height": max(48.0, desc_bottom - cur_left_y),
            "font_size": 11.5,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "line_spacing": 140,
            "id": f"KSPOT_DESC_S{slide_idx}",
        })

    if status_pill:
        pill_txt = status_pill.strip()
        if not pill_txt.startswith(("●", "✓", "▶")):
            pill_txt = f"● {pill_txt}"
        pill_w = round(min(292.0, max(124.0, len(pill_txt) * 6.8 + 26.0)), 2)
        pill_bg_id = f"KSPOT_PILL_BG_S{slide_idx}"
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": 36.0,
            "y": 338.0,
            "width": pill_w,
            "height": 30.0,
            "background_color": COLOR_GREEN_LIGHT,
            "id": pill_bg_id,
        })
        ops.append({
            "op": "style-shape",
            "element": pill_bg_id,
            "outline_color": COLOR_GREEN_LIGHT,
            "outline_weight": 0.5,
        })
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": pill_txt,
            "x": 40.0,
            "y": 338.0,
            "width": round(pill_w - 8.0, 2),
            "height": 30.0,
            "font_size": 9.5,
            "bold": True,
            "color": COLOR_GREEN_TEXT,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "content_alignment": "MIDDLE",
            "id": f"KSPOT_PILL_TXT_S{slide_idx}",
        })

    # Right Column: Measured By List (separated from left column by pure negative space)
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": (measured_by_title or "MEASURED BY").upper(),
        "x": 372.0,
        "y": 128.0,
        "width": 312.0,
        "height": 18.0,
        "font_size": 9.0,
        "bold": True,
        "color": COLOR_TEXT_MUTED,
        "font_family": FONT_FAMILY_BODY,
        "alignment": "left",
        "id": f"KSPOT_MKICK_S{slide_idx}",
    })

    items = list(measurements or [])[:4]
    n_m = max(1, len(items))
    row_top = 152.0
    row_h = min(62.0, 218.0 / n_m)

    for idx, raw_m in enumerate(items):
        ry = round(row_top + idx * row_h, 2)
        dot_col = google_accent(idx)[0]
        if isinstance(raw_m, dict):
            m_title = str(raw_m.get("title") or raw_m.get("metric") or raw_m.get("label") or f"Metric {idx + 1}")
            m_desc = str(raw_m.get("description") or raw_m.get("detail") or "")
        else:
            s_raw = str(raw_m).strip()
            if ":" in s_raw:
                parts = s_raw.split(":", 1)
                m_title, m_desc = parts[0].strip(), parts[1].strip()
            else:
                m_title, m_desc = s_raw, ""

        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": 372.0,
            "y": ry,
            "width": 312.0,
            "height": 1.0,
            "background_color": COLOR_CARD_BORDER,
            "id": f"KSPOT_RULE_S{slide_idx}_{idx + 1}",
        })
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ELLIPSE",
            "x": 372.0,
            "y": round(ry + 14.0, 2),
            "width": 8.0,
            "height": 8.0,
            "background_color": dot_col,
            "id": f"KSPOT_DOT_S{slide_idx}_{idx + 1}",
        })
        if m_desc:
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": m_title,
                "x": 388.0,
                "y": round(ry + 8.0, 2),
                "width": 296.0,
                "height": 20.0,
                "font_size": 12.5,
                "bold": False,
                "color": COLOR_TEXT_PRIMARY,
                "font_family": FONT_FAMILY_HEADING,
                "alignment": "left",
                "content_alignment": "MIDDLE",
                "id": f"KSPOT_MTITL_S{slide_idx}_{idx + 1}",
            })
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": m_desc,
                "x": 388.0,
                "y": round(ry + 28.0, 2),
                "width": 296.0,
                "height": round(max(20.0, row_h - 32.0), 2),
                "font_size": 10.0,
                "color": COLOR_TEXT_MUTED,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "left",
                "line_spacing": 125,
                "id": f"KSPOT_MDESC_S{slide_idx}_{idx + 1}",
            })
        else:
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": m_title,
                "x": 388.0,
                "y": round(ry + 6.0, 2),
                "width": 296.0,
                "height": 24.0,
                "font_size": 12.0,
                "bold": False,
                "color": COLOR_TEXT_PRIMARY,
                "font_family": FONT_FAMILY_HEADING,
                "alignment": "left",
                "content_alignment": "MIDDLE",
                "id": f"KSPOT_MTITL_S{slide_idx}_{idx + 1}",
            })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 17: Horizon Staircase (Ascending Bottom-Aligned Roadmap Cards)
# =============================================================================


def generate_horizon_staircase(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    horizons: list[dict[str, Any]],
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 17: Horizon Staircase (Slide 12 style).

    Renders 2–4 ascending-height `ROUND_RECTANGLE` cards bottom-aligned at `Y=374`,
    with adaptive Zen *Ma* sky above concise staircases, rising visually from
    `Agora (Curto Prazo)` → `Médio Prazo` → `Longo Prazo (Futuro)`, Regular titles,
    and the final North Star card softly tinted in Google Blue (`#E8F0FE`).
    """
    slide_idx = _extract_slide_idx(slide_id)
    items = list(horizons or [])[:4]
    n = len(items)
    if n < 2:
        raise ValueError("Horizon staircase requires 2 to 4 horizons")

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_CARD_WHITE},
    ]
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    def _h_density(rh: dict[str, Any]) -> tuple[int, int]:
        rb = rh.get("bullets") or rh.get("items") or rh.get("description") or []
        if isinstance(rb, list):
            return len(rb), sum(len(str(x)) for x in rb)
        s = str(rb or "")
        return max(1, s.count("\n") + 1), len(s)

    h_densities = [_h_density(h) for h in items]
    max_b = max((d[0] for d in h_densities), default=0)
    max_c = max((d[1] for d in h_densities), default=0)

    gap = 18.0 if n <= 3 else 14.0
    col_w = (648.0 - (n - 1) * gap) / n
    bottom_y = 374.0
    if max_b <= 3 and max_c <= 130:
        highest_top_y = 142.0
        step_drop = 24.0 if n <= 3 else 18.0
    else:
        highest_top_y = 114.0
        step_drop = 22.0 if n <= 3 else 16.0

    default_labels = [
        "Agora (Curto Prazo)",
        "Médio Prazo",
        "Longo Prazo (Futuro)",
        "Expansão Contínua",
    ]

    for idx, raw_h in enumerate(items):
        cx = round(36.0 + idx * (col_w + gap), 2)
        cw = round(col_w, 2)
        top_y = round(highest_top_y + (n - 1 - idx) * step_drop, 2)
        ch = round(bottom_y - top_y, 2)

        is_final = bool(raw_h.get("highlight", idx == n - 1))
        solid_hex, text_hex, _ = google_accent(idx)
        bar_col = COLOR_BLUE_ACCENT if is_final else solid_hex
        card_bg = COLOR_BLUE_LIGHT if is_final else COLOR_CARD_WHITE
        card_brd = "#AECBFA" if is_final else COLOR_CARD_BORDER
        tag_fg = COLOR_BLUE_TEXT if is_final else text_hex

        h_tag = str(raw_h.get("horizon") or raw_h.get("tag") or raw_h.get("phase") or default_labels[idx])
        h_title = str(raw_h.get("title") or f"Stage {idx + 1}")
        raw_bullets = raw_h.get("bullets") or raw_h.get("items") or raw_h.get("description") or []
        h_footer = str(raw_h.get("footer") or raw_h.get("governance") or raw_h.get("human_role") or "").strip()

        card_id = f"STAIR_CARD_S{slide_idx}_{idx + 1}"
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": cx,
            "y": top_y,
            "width": cw,
            "height": ch,
            "background_color": card_bg,
            "id": card_id,
        })
        ops.append({
            "op": "style-shape",
            "element": card_id,
            "outline_color": card_brd,
            "outline_weight": 1.5 if is_final else 1.0,
        })
        st_bar_x, st_bar_w = _round_rect_top_bar_bounds(cx, cw, ch)
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ROUND_RECTANGLE",
            "x": st_bar_x,
            "y": top_y,
            "width": st_bar_w,
            "height": 3.0,
            "background_color": bar_col,
            "id": f"STAIR_BAR_S{slide_idx}_{idx + 1}",
        })
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": h_tag.upper(),
            "x": round(cx + 14.0, 2),
            "y": round(top_y + 10.0, 2),
            "width": round(cw - 28.0, 2),
            "height": 16.0,
            "font_size": 8.5,
            "bold": True,
            "color": tag_fg,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": f"STAIR_TAG_S{slide_idx}_{idx + 1}",
        })
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": h_title,
            "x": round(cx + 14.0, 2),
            "y": round(top_y + 28.0, 2),
            "width": round(cw - 28.0, 2),
            "height": 24.0,
            "font_size": 13.5,
            "bold": False,
            "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": f"STAIR_TITL_S{slide_idx}_{idx + 1}",
        })

        body_top = round(top_y + 52.0, 2)
        body_bottom = 336.0 if h_footer else 364.0
        body_txt = _format_bullets(raw_bullets) if isinstance(raw_bullets, list) else str(raw_bullets)
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": body_txt,
            "x": round(cx + 14.0, 2),
            "y": body_top,
            "width": round(cw - 28.0, 2),
            "height": round(max(44.0, body_bottom - body_top), 2),
            "font_size": 10.5,
            "color": COLOR_TEXT_BODY,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "line_spacing": 128,
            "id": f"STAIR_BODY_S{slide_idx}_{idx + 1}",
        })

        if h_footer:
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": h_footer,
                "x": round(cx + 14.0, 2),
                "y": 340.0,
                "width": round(cw - 28.0, 2),
                "height": 28.0,
                "font_size": 9.0,
                "italic": True,
                "color": COLOR_BLUE_TEXT if is_final else COLOR_TEXT_MUTED,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "left",
                "id": f"STAIR_FTR_S{slide_idx}_{idx + 1}",
            })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 18: Closing Ask (Dark Charcoal Takeaway + 3 Colored-Rule Columns)
# =============================================================================


def generate_closing_ask(
    slide_id: str,
    title: str,
    subtitle: str = "",
    kicker: str = "",
    section_kicker: str = "WHAT WE NEED TO GET THERE",
    asks: Optional[list[Union[dict[str, Any], str]]] = None,
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 18: Closing Ask (Slide 18 style).

    Zen Charcoal (`#202124`) executive closing slide: mini 4-color bar, large Regular
    white takeaway headline, optional `#BDC1C6` subtitle, generous dark *Ma* middle,
    gold `#FBBC04` section kicker, and 2–4 borderless Regular columns under `2.5pt`
    Google-colored top rules.
    """
    slide_idx = _extract_slide_idx(slide_id)
    clean_title = (title or "").strip()
    t_len = len(clean_title)
    title_font = 32.0 if t_len <= 58 else 26.0 if t_len <= 98 else 21.0

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_DARK_PRIMARY},
        *_build_mini_4color_bar(
            slide_id=slide_id,
            prefix=f"MBAR_S{slide_idx}",
            x=36.0,
            y=36.0,
            seg_w=20.0,
            seg_h=3.5,
        ),
    ]

    if kicker and kicker.strip():
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": kicker.strip().upper(),
            "x": 124.0,
            "y": 30.0,
            "width": 360.0,
            "height": 16.0,
            "font_size": 9.0,
            "bold": True,
            "color": COLOR_DARK_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": f"KICK_S{slide_idx}_ASK",
        })

    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": clean_title,
        "x": 36.0,
        "y": 56.0,
        "width": 636.0,
        "height": 84.0,
        "font_size": title_font,
        "bold": False,
        "color": COLOR_TEXT_WHITE,
        "font_family": FONT_FAMILY_HEADING,
        "alignment": "left",
        "line_spacing": 120,
        "id": f"TITL_S{slide_idx}_ASK",
    })

    if subtitle:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": subtitle,
            "x": 36.0,
            "y": 144.0,
            "width": 620.0,
            "height": 38.0,
            "font_size": 14.0,
            "color": COLOR_DARK_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": f"SUBT_S{slide_idx}_ASK",
        })

    items = list(asks or [])[:4]
    if items:
        max_desc = max(
            (
                len(str(a.get("description") or a.get("detail") or ""))
                if isinstance(a, dict)
                else len(str(a))
                for a in items
            ),
            default=0,
        )
        sect_y = 212.0 if max_desc > 110 else ZEN_CLOSING_SECT_Y
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": (section_kicker or "WHAT WE NEED TO GET THERE").upper(),
            "x": 36.0,
            "y": sect_y,
            "width": 648.0,
            "height": 18.0,
            "font_size": 9.0,
            "bold": True,
            "color": "#FBBC04",
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": f"SECT_S{slide_idx}_ASK",
        })

        n_a = len(items)
        col_top = sect_y + 24.0
        gap = 24.0 if n_a <= 3 else 16.0
        col_w = (648.0 - (n_a - 1) * gap) / n_a

        for idx, raw_a in enumerate(items):
            cx = round(36.0 + idx * (col_w + gap), 2)
            cw = round(col_w, 2)
            rule_col = google_accent(idx)[0]
            if isinstance(raw_a, dict):
                a_title = str(raw_a.get("title") or raw_a.get("label") or f"Ask {idx + 1}")
                a_desc = str(raw_a.get("description") or raw_a.get("detail") or "")
            else:
                s_raw = str(raw_a).strip()
                if ":" in s_raw:
                    parts = s_raw.split(":", 1)
                    a_title, a_desc = parts[0].strip(), parts[1].strip()
                else:
                    a_title, a_desc = s_raw, ""

            ops.append({
                "op": "add-shape",
                "slide": slide_id,
                "shape_type": "RECTANGLE",
                "x": cx,
                "y": col_top,
                "width": cw,
                "height": 2.5,
                "background_color": rule_col,
                "id": f"ASK_RULE_S{slide_idx}_{idx + 1}",
            })
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": a_title,
                "x": cx,
                "y": round(col_top + 10.0, 2),
                "width": cw,
                "height": 24.0,
                "font_size": 14.0,
                "bold": False,
                "color": COLOR_TEXT_WHITE,
                "font_family": FONT_FAMILY_HEADING,
                "alignment": "left",
                "id": f"ASK_TITL_S{slide_idx}_{idx + 1}",
            })
            if a_desc:
                ops.append({
                    "op": "add-textbox",
                    "slide": slide_id,
                    "text": a_desc,
                    "x": cx,
                    "y": round(col_top + 38.0, 2),
                    "width": cw,
                    "height": round(max(44.0, 374.0 - (col_top + 38.0)), 2),
                    "font_size": 10.5,
                    "color": COLOR_DARK_MUTED,
                    "font_family": FONT_FAMILY_BODY,
                    "alignment": "left",
                    "line_spacing": 135,
                    "id": f"ASK_DESC_S{slide_idx}_{idx + 1}",
                })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# ArchetypeEngine: Unified Dispatcher Interface
# =============================================================================

_ENGINE_ALIASES = {
    "demo": "demo_pivot",
    "image": "image_split",
    "diagram": "image_split",
    "flow": "flow_diagram",
    "native_diagram": "flow_diagram",
    "cycle": "flow_diagram",
    "timeline": "flow_diagram",
    "funnel": "flow_diagram",
    "layered_cake": "flow_diagram",
    "cake": "flow_diagram",
    "swimlanes": "flow_diagram",
    "swimlane": "flow_diagram",
    "layers_swimlane": "flow_diagram",
    "architecture_layers": "flow_diagram",
    "initiative_card": "workstream_card",
    "frente_card": "workstream_card",
    "workstream": "workstream_card",
    "title_cover": "cover",
    "opening": "cover",
    "thesis": "statement_pivot",
    "short_answer": "statement_pivot",
    "provocation": "statement_pivot",
    "matrix": "capability_matrix",
    "comparison_matrix": "capability_matrix",
    "big_number": "kpi_spotlight",
    "pilot_spotlight": "kpi_spotlight",
    "staircase": "horizon_staircase",
    "rising_horizons": "horizon_staircase",
    "north_star": "horizon_staircase",
    "dark_closing": "closing_ask",
    "the_ask": "closing_ask",
    "executive_ask": "closing_ask",
}

# Archetype aliases that also pick the flow_diagram layout.
_FLOW_LAYOUT_HINTS = {
    "cycle": "cycle",
    "timeline": "timeline",
    "funnel": "funnel",
    "layered_cake": "layered_cake",
    "cake": "layered_cake",
    "swimlanes": "swimlanes",
    "swimlane": "swimlanes",
    "layers_swimlane": "swimlanes",
    "architecture_layers": "swimlanes",
}


class ArchetypeEngine:
    """Unified Archetype Coordinate Engine and Batch Payload Dispatcher.

    Provides a centralized dispatcher interface `generate_slide_ops` conforming
    to the contract between preso.engine and downstream compilers/spec parsers.
    """

    ARCHETYPE_DISPATCH = {
        "chapter_divider": generate_chapter_divider,
        "split_cards": generate_split_cards,
        "code_terminal": generate_code_terminal,
        "hero_metrics": generate_hero_metrics,
        "ladder_hierarchy": generate_ladder_hierarchy,
        "executive_grid": generate_executive_grid,
        "dodont_checklist": generate_dodont_checklist,
        "actionable_takeaways": generate_actionable_takeaways,
        "demo_pivot": generate_demo_pivot,
        "image_split": generate_image_split,
        "flow_diagram": generate_flow_diagram,
        "workstream_card": generate_workstream_card,
        "cover": generate_cover,
        "statement_pivot": generate_statement_pivot,
        "capability_matrix": generate_capability_matrix,
        "kpi_spotlight": generate_kpi_spotlight,
        "horizon_staircase": generate_horizon_staircase,
        "closing_ask": generate_closing_ask,
    }

    @classmethod
    def generate_slide_ops(
        cls,
        slide_spec: Any,
        slide_index: int = 1,
    ) -> list[dict[str, Any]]:
        """Dispatches and generates gslides batch operations for any slide specification."""
        data: dict[str, Any]
        if isinstance(slide_spec, dict):
            data = slide_spec
        elif hasattr(slide_spec, "to_dict") and callable(slide_spec.to_dict):
            data = slide_spec.to_dict()
        elif hasattr(slide_spec, "__dict__"):
            data = vars(slide_spec)
        else:
            raise TypeError(f"Cannot serialize slide spec of type {type(slide_spec)}")

        archetype = data.get("archetype", "").strip().lower()
        archetype = archetype.replace("-", "_")
        raw_alias = archetype
        layout_hint = _FLOW_LAYOUT_HINTS.get(archetype, "")
        archetype = _ENGINE_ALIASES.get(archetype, archetype)
        slide_id = data.get("id") or f"SLIDE_{slide_index:02d}_{archetype.upper()}"
        notes = data.get("notes") or data.get("speaker_notes", "")
        title = data.get("title", "")
        subtitle = data.get("subtitle", "")
        kicker = data.get("kicker", "")

        if archetype == "chapter_divider":
            chap_num = data.get("chapter_number", slide_index)
            kicker_text = data.get("kicker", "CHAPTER")
            return generate_chapter_divider(
                slide_id=slide_id,
                chapter_number=chap_num,
                title=title,
                subtitle=subtitle,
                speaker_notes=notes,
                kicker=kicker_text,
            )

        elif archetype == "split_cards":
            cards = data.get("cards", [])
            foundation = data.get("foundation")
            flow_steps = data.get("flow_steps") or data.get("process_strip")
            return generate_split_cards(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                cards=cards,
                speaker_notes=notes,
                foundation=foundation,
                flow_steps=flow_steps,
            )

        elif archetype == "code_terminal":
            terminals = data.get("terminals", [])
            return generate_code_terminal(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                terminals=terminals,
                speaker_notes=notes,
            )

        elif archetype == "hero_metrics":
            metrics = data.get("metrics", [])
            return generate_hero_metrics(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                metrics=metrics,
                speaker_notes=notes,
            )

        elif archetype == "ladder_hierarchy":
            steps = data.get("steps", [])
            return generate_ladder_hierarchy(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                steps=steps,
                speaker_notes=notes,
            )

        elif archetype == "executive_grid":
            quadrants = data.get("quadrants") or data.get("items") or data.get("pillars") or []
            return generate_executive_grid(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                quadrants=quadrants,
                speaker_notes=notes,
            )

        elif archetype == "dodont_checklist":
            chk_dict = data.get("checklist", {}) if isinstance(data.get("checklist"), dict) else {}
            dont_items = data.get("dont_items") or data.get("dont") or chk_dict.get("dont_items") or chk_dict.get("dont") or []
            do_items = data.get("do_items") or data.get("do") or chk_dict.get("do_items") or chk_dict.get("do") or []
            dont_title = str(data.get("dont_title") or chk_dict.get("dont_title") or "")
            do_title = str(data.get("do_title") or chk_dict.get("do_title") or "")
            takeaway = str(data.get("takeaway") or chk_dict.get("takeaway") or "")
            return generate_dodont_checklist(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                dont_items=dont_items,
                do_items=do_items,
                speaker_notes=notes,
                dont_title=dont_title,
                do_title=do_title,
                takeaway=takeaway,
            )

        elif archetype == "actionable_takeaways":
            principles = data.get("principles", [])
            raw_roadmap = data.get("roadmap", {})
            if isinstance(raw_roadmap, dict):
                roadmap_title = raw_roadmap.get("title") or data.get("roadmap_title") or "NEXT STEPS & ROADMAP"
                roadmap_items = (
                    raw_roadmap.get("milestones")
                    or raw_roadmap.get("steps")
                    or raw_roadmap.get("items")
                    or data.get("roadmap_items")
                    or []
                )
                cta_text = (
                    raw_roadmap.get("cta_button_text")
                    or raw_roadmap.get("cta_text")
                    or data.get("cta_text")
                    or "EXECUTE BUILD NOW →"
                )
            else:
                roadmap_title = data.get("roadmap_title", "NEXT STEPS & ROADMAP")
                roadmap_items = data.get("roadmap_items", [])
                cta_text = data.get("cta_text", "EXECUTE BUILD NOW →")

            return generate_actionable_takeaways(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                principles=principles,
                roadmap_title=roadmap_title,
                roadmap_items=roadmap_items,
                cta_text=cta_text,
                speaker_notes=notes,
            )

        elif archetype == "demo_pivot":
            watch_for = data.get("watch_for") or []
            if isinstance(watch_for, str):
                watch_for = [watch_for]
            return generate_demo_pivot(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                watch_for=watch_for,
                speaker_notes=notes,
                kicker=kicker or "LIVE DEMO",
            )

        elif archetype == "image_split":
            return generate_image_split(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                image=data.get("image") or {},
                bullets=data.get("bullets") or [],
                image_side=str(data.get("image_side", "right")),
                image_layout=str(data.get("image_layout", "split")),
                callout=data.get("callout") or data.get("step_callout"),
                speaker_notes=notes,
            )

        elif archetype == "flow_diagram":
            slide_idx = _extract_slide_idx(slide_id, slide_index)
            return generate_flow_diagram(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                diagram=data.get("diagram") or {},
                speaker_notes=notes,
                layout_hint=layout_hint,
                header_ops=_build_header_ops(slide_id, slide_idx, title, subtitle, kicker),
                slide_idx=slide_idx,
            )

        elif archetype == "workstream_card":
            ws = data.get("workstream") if isinstance(data.get("workstream"), dict) else data
            return generate_workstream_card(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                image=ws.get("image") or data.get("image") or {},
                tempo=str(ws.get("tempo") or ws.get("horizon") or ws.get("maturity") or ""),
                receita=str(ws.get("receita") or ws.get("revenue") or ""),
                desafios=ws.get("desafios") or ws.get("challenges") or ws.get("risks") or [],
                diferenciais=ws.get("diferenciais") or ws.get("differentiators") or ws.get("strengths") or [],
                acoes=ws.get("acoes") or ws.get("actions") or ws.get("next_steps") or [],
                speaker_notes=notes,
            )

        elif archetype == "cover":
            return generate_cover(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                breadcrumbs=data.get("breadcrumbs") or data.get("evolution") or [],
                date=str(data.get("date") or data.get("context") or data.get("footer") or ""),
                speaker_notes=notes,
            )

        elif archetype == "statement_pivot":
            default_var = "dark" if raw_alias == "provocation" else "blue"
            return generate_statement_pivot(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                variant=str(data.get("variant") or default_var),
                speaker_notes=notes,
            )

        elif archetype == "capability_matrix":
            return generate_capability_matrix(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                columns=data.get("columns") or [],
                rows=data.get("rows") or [],
                footnote=str(data.get("footnote") or data.get("legend") or data.get("note") or ""),
                row_label_header=str(data.get("row_label_header") or ""),
                speaker_notes=notes,
            )

        elif archetype == "kpi_spotlight":
            return generate_kpi_spotlight(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                stat_value=str(data.get("stat_value") or data.get("value") or "0"),
                stat_label=str(data.get("stat_label") or data.get("unit") or ""),
                stat_description=str(data.get("stat_description") or data.get("description") or ""),
                status_pill=str(data.get("status_pill") or data.get("live_status") or ""),
                measured_by_title=str(
                    data.get("measured_by_title") or data.get("measured_by_label") or "MEASURED BY"
                ),
                measurements=data.get("measurements") or data.get("measured_by") or [],
                speaker_notes=notes,
            )

        elif archetype == "horizon_staircase":
            return generate_horizon_staircase(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                horizons=data.get("horizons") or data.get("stages") or [],
                speaker_notes=notes,
            )

        elif archetype == "closing_ask":
            return generate_closing_ask(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                section_kicker=str(data.get("section_kicker") or "WHAT WE NEED TO GET THERE"),
                asks=data.get("asks") or data.get("columns") or data.get("items") or [],
                speaker_notes=notes,
            )

        else:
            raise ValueError(
                f"Unknown slide archetype: '{archetype}'. Supported archetypes: {list(cls.ARCHETYPE_DISPATCH.keys())}"
            )

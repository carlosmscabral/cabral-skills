"""Blueprint Presentation Slide Archetype Batch Operation Generators.

Implements the 10 Blueprint slide archetypes generating atomic, single-pass
`gslides batch` JSON payloads with deterministic IDs, typography, colors,
and speaker notes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union

from preso.engine.coordinates import (
    BoundingBox,
    calculate_2x2_grid_bounds,
    calculate_asymmetric_split_bounds,
    calculate_card_internal_bounds,
    calculate_header_bounds,
    calculate_n_column_bounds,
)
from preso.engine.design_tokens import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
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
    COLOR_RED_BORDER,
    COLOR_RED_DONT,
    COLOR_RED_LIGHT,
    COLOR_RED_TEXT,
    COLOR_SLATE_DARK,
    COLOR_SLATE_HEADER,
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
    stripe_color: str = COLOR_BLUE_ACCENT


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


def _build_header_ops(
    slide_id: str,
    slide_idx_str: str,
    title: str,
    subtitle: str,
    kicker: str,
) -> list[dict[str, Any]]:
    """Builds standard header operations for content slides (Archetypes 2-8)."""
    bounds = calculate_header_bounds()
    ops: list[dict[str, Any]] = []

    # Category Kicker Pill
    if kicker:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": kicker.upper(),
            "x": bounds["kicker"].x,
            "y": bounds["kicker"].y,
            "width": bounds["kicker"].width,
            "height": bounds["kicker"].height,
            "font_size": FONT_SIZE_KICKER,
            "bold": True,
            "color": COLOR_BLUE_TEXT,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "id": f"HDR_S{slide_idx_str}_PILL",
        })

    # Slide Main Title
    if title:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": title,
            "x": bounds["title"].x,
            "y": bounds["title"].y,
            "width": bounds["title"].width,
            "height": bounds["title"].height,
            "font_size": FONT_SIZE_SLIDE_TITLE,
            "bold": True,
            "color": COLOR_NAVY_PRIMARY,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": f"HDR_S{slide_idx_str}_TITL",
        })

    # Slide Subtitle / 1-Liner Takeaway
    if subtitle:
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": subtitle,
            "x": bounds["subtitle"].x,
            "y": bounds["subtitle"].y,
            "width": bounds["subtitle"].width,
            "height": bounds["subtitle"].height,
            "font_size": FONT_SIZE_SLIDE_SUBTITLE,
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

        # Top Google Rainbow Progress Bar (4 contiguous color segments spanning 648pt)
        {
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": 36.0,
            "y": 36.0,
            "width": 162.0,
            "height": 5.0,
            "background_color": "#EA4335",
            "id": f"BAR_S{slide_idx}_RED",
        },
        {
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": 198.0,
            "y": 36.0,
            "width": 162.0,
            "height": 5.0,
            "background_color": "#FBBC04",
            "id": f"BAR_S{slide_idx}_YEL",
        },
        {
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": 360.0,
            "y": 36.0,
            "width": 162.0,
            "height": 5.0,
            "background_color": "#34A853",
            "id": f"BAR_S{slide_idx}_GRN",
        },
        {
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": 522.0,
            "y": 36.0,
            "width": 162.0,
            "height": 5.0,
            "background_color": "#4285F4",
            "id": f"BAR_S{slide_idx}_BLU",
        },

        # Huge Chapter Number (60pt Bold Black)
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": chap_num_str,
            "x": 36.0,
            "y": 52.0,
            "width": 648.0,
            "height": 56.0,
            "font_size": 56.0,
            "bold": True,
            "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": f"NUM_S{slide_idx}",
        },

        # Dynamic Chapter Title
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": title,
            "x": 36.0,
            "y": title_y,
            "width": 648.0,
            "height": title_height,
            "font_size": title_font_size,
            "bold": True,
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
            "color": COLOR_BLUE_ACCENT,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "line_spacing": 125,
            "id": f"SUBT_S{slide_idx}",
        },
    ]

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 2: 2-Card & 3-Card Split Comparison
# =============================================================================


def generate_split_cards(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    cards: list[Union[dict[str, Any], CardSpec]],
    speaker_notes: str = "",
    foundation: Optional[Union[dict[str, Any], CardSpec, str]] = None,
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 2: Split Card Comparison.

    Supports 2-card and 3-card variants with category pills, accent stripes,
    structured card titles, and bullet lists, with optional bottom foundation banner.
    """
    slide_idx = _extract_slide_idx(slide_id)
    n = len(cards)
    if n < 1:
        raise ValueError("At least 1 card is required for split card archetype")

    gap = 24.0 if n == 2 else 18.0
    if foundation:
        col_bounds = calculate_n_column_bounds(n=n, gap=gap, top_y=98.0, height=184.0)
    else:
        col_bounds = calculate_n_column_bounds(n=n, gap=gap)

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_BG_LIGHT},
    ]

    # Universal Header
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    # Process Cards
    for i, raw_card in enumerate(cards):
        card_num = i + 1
        if isinstance(raw_card, CardSpec):
            c_title = raw_card.title
            c_bullets = raw_card.bullets
            c_cat = raw_card.category
            c_stripe = raw_card.stripe_color
        else:
            c_title = raw_card.get("title", f"Card {card_num}")
            c_bullets = raw_card.get("bullets", [])
            c_cat = raw_card.get("category", "")
            c_stripe = raw_card.get("stripe_color", COLOR_BLUE_ACCENT)

        box = col_bounds[i]
        card_id = f"CARD_S{slide_idx}_C{card_num}"
        stripe_id = f"STRIPE_S{slide_idx}_C{card_num}"
        pill_id = f"PILL_S{slide_idx}_C{card_num}"
        titl_id = f"TITL_S{slide_idx}_C{card_num}"
        div_id = f"DIV_S{slide_idx}_C{card_num}"
        body_id = f"BODY_S{slide_idx}_C{card_num}"

        # Card Container Shape
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
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

        # Top Accent Stripe
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": box.x,
            "y": box.y,
            "width": box.width,
            "height": 5.0,
            "background_color": c_stripe,
            "id": stripe_id,
        })

        # Category Pill (if present)
        inner_w = box.width - 32.0
        cur_y = box.y + (10.0 if foundation else 14.0)
        if c_cat:
            cat_text = c_cat.upper()
            pill_w = min(inner_w, max(80.0, len(cat_text) * 7.5 + 24.0))
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": cat_text,
                "x": box.x + 16.0,
                "y": cur_y,
                "width": pill_w,
                "height": 18.0,
                "font_size": 9.5 if foundation else 10.0,
                "bold": True,
                "color": COLOR_BLUE_TEXT,
                "background_color": COLOR_BLUE_LIGHT,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "center",
                "id": pill_id,
            })
            cur_y += (22.0 if foundation else 24.0)
        else:
            cur_y += 6.0

        # Card Title
        titl_height = 24.0 if foundation else 26.0
        titl_font = 13.0 if foundation else FONT_SIZE_CARD_HEADER
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": c_title,
            "x": box.x + 16.0,
            "y": cur_y,
            "width": inner_w,
            "height": titl_height,
            "font_size": titl_font,
            "bold": True,
            "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": titl_id,
        })
        cur_y += (titl_height + (3.0 if foundation else 4.0))

        # Inner Divider
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": box.x + 16.0,
            "y": cur_y,
            "width": inner_w,
            "height": 1.0,
            "background_color": COLOR_DIVIDER,
            "id": div_id,
        })
        cur_y += (6.0 if foundation else 10.0)

        # Card Bullets Body
        body_text = _format_bullets(c_bullets)
        body_height = max(50.0, (box.y + box.height) - cur_y - 8.0)
        font_size = 10.5 if foundation else FONT_SIZE_CARD_BODY
        line_spacing = 130 if foundation else 140
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": body_text,
            "x": box.x + 16.0,
            "y": cur_y,
            "width": inner_w,
            "height": body_height,
            "font_size": font_size,
            "color": COLOR_TEXT_MUTED,
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
        f_div_id = f"FDIV_S{slide_idx}"
        f_body_id = f"FBODY_S{slide_idx}"

        if isinstance(foundation, dict):
            f_title = foundation.get("title", "Fundação Enterprise")
            f_cat = foundation.get("category", foundation.get("category_pill", "BASE CORPORATIVA"))
            f_bullets = foundation.get("bullets", foundation.get("description", ""))
            f_stripe = foundation.get("stripe_color", foundation.get("theme", COLOR_BLUE_ACCENT))
        else:
            f_title = str(foundation)
            f_cat = "BASE CORPORATIVA"
            f_bullets = ""
            f_stripe = COLOR_BLUE_ACCENT

        # 1. Foundation Container Shape
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
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
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": f_box_x,
            "y": f_box_y,
            "width": f_box_w,
            "height": 4.0,
            "background_color": f_stripe,
            "id": f_stripe_id,
        })

        # 3. Category Pill
        f_cur_y = f_box_y + 8.0
        cat_text = f_cat.upper()
        pill_w = min(170.0, max(80.0, len(cat_text) * 7.0 + 20.0))
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": cat_text,
            "x": f_box_x + 14.0,
            "y": f_cur_y,
            "width": pill_w,
            "height": 18.0,
            "font_size": 9.5,
            "bold": True,
            "color": COLOR_BLUE_TEXT,
            "background_color": COLOR_BLUE_LIGHT,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "center",
            "id": f_pill_id,
        })

        # 4. Foundation Title
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": f_title,
            "x": f_box_x + 20.0 + pill_w,
            "y": f_cur_y - 1.0,
            "width": f_box_w - pill_w - 34.0,
            "height": 20.0,
            "font_size": 13.0,
            "bold": True,
            "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": f_titl_id,
        })

        # 5. Inner Divider
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": f_box_x + 14.0,
            "y": f_cur_y + 22.0,
            "width": f_box_w - 28.0,
            "height": 1.0,
            "background_color": COLOR_DIVIDER,
            "id": f_div_id,
        })

        # 6. Bullets Body
        body_text = _format_bullets(f_bullets) if isinstance(f_bullets, list) else str(f_bullets)
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": body_text,
            "x": f_box_x + 14.0,
            "y": f_cur_y + 26.0,
            "width": f_box_w - 28.0,
            "height": 44.0,
            "font_size": 10.0,
            "color": COLOR_TEXT_MUTED,
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
        {"op": "set-background", "slide": slide_id, "color": COLOR_BG_LIGHT},
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
            "shape_type": "RECTANGLE",
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
            "x": box.x,
            "y": box.y,
            "width": box.width,
            "height": 28.0,
            "background_color": COLOR_SLATE_HEADER,
            "id": term_hdr_id,
        })

        # 3. Traffic Light Dots
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "ELLIPSE",
            "x": box.x + 10.0,
            "y": box.y + 11.0,
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
            "y": box.y + 11.0,
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
            "y": box.y + 11.0,
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
            "y": box.y + 4.0,
            "width": file_w,
            "height": 20.0,
            "font_size": FONT_SIZE_CODE_FILENAME,
            "bold": True,
            "color": COLOR_CODE_FILENAME,
            "font_family": FONT_FAMILY_CODE,
            "alignment": "left",
            "id": file_id,
        })

        # Status Badge (Do / Don't / Verified)
        if badge_text:
            ops.append({
                "op": "add-textbox",
                "slide": slide_id,
                "text": badge_text,
                "x": badge_x,
                "y": box.y + 4.0,
                "width": badge_w,
                "height": 20.0,
                "font_size": FONT_SIZE_BADGE,
                "bold": True,
                "color": badge_color,
                "background_color": badge_bg,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "center",
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
        {"op": "set-background", "slide": slide_id, "color": COLOR_BG_LIGHT},
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
            m_kicker = raw_metric.get("kicker", f"METRIC {m_num:02d}")

        box = col_bounds[i]

        card_id = f"CARD_S{slide_idx}_M{m_num}"
        kicker_id = f"KICK_S{slide_idx}_M{m_num}"
        stat_id = f"STAT_S{slide_idx}_M{m_num}"
        unit_id = f"UNIT_S{slide_idx}_M{m_num}"
        delta_id = f"DELTA_S{slide_idx}_M{m_num}"
        div_id = f"DIV_S{slide_idx}_M{m_num}"
        desc_id = f"DESC_S{slide_idx}_M{m_num}"

        bg_col = COLOR_NAVY_PRIMARY if is_hero else COLOR_CARD_WHITE
        border_col = "#3949AB" if is_hero else COLOR_CARD_BORDER
        stat_col = COLOR_TEXT_WHITE if is_hero else COLOR_BLUE_ACCENT
        kicker_col = COLOR_BLUE_SUBTITLE if is_hero else COLOR_TEXT_MUTED
        unit_col = COLOR_TEXT_WHITE if is_hero else COLOR_TEXT_PRIMARY
        desc_col = COLOR_BLUE_SUBTITLE if is_hero else COLOR_TEXT_MUTED
        div_col = "#3949AB" if is_hero else COLOR_DIVIDER

        # Card Container Shape
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
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
            "bold": True,
            "color": stat_col,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": stat_id,
        })

        # Metric Unit / Title Label
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": unit,
            "x": box.x + 16.0,
            "y": box.y + 96.0,
            "width": box.width - 32.0,
            "height": 22.0,
            "font_size": FONT_SIZE_HERO_UNIT,
            "bold": True,
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
                delta_fg = COLOR_AMBER_TEXT
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
                "height": 22.0,
                "font_size": FONT_SIZE_HERO_DELTA,
                "bold": True,
                "color": delta_fg,
                "background_color": delta_bg,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "center",
                "id": delta_id,
            })

        # Divider Line
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": box.x + 16.0,
            "y": box.y + 154.0,
            "width": box.width - 32.0,
            "height": 1.0,
            "background_color": div_col,
            "id": div_id,
        })

        # Description / Context
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": desc,
            "x": box.x + 16.0,
            "y": box.y + 162.0,
            "width": box.width - 32.0,
            "height": 98.0,
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

    Features: 4-step horizontal pipeline, step number badges, top accent stripes,
    directional connector arrow lines, step titles, and descriptions.
    """
    slide_idx = _extract_slide_idx(slide_id)
    n = len(steps)
    if n < 2:
        raise ValueError("At least 2 steps are required for a stepped ladder flow")

    gap = 24.0
    col_bounds = calculate_n_column_bounds(n=n, gap=gap)

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_BG_LIGHT},
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
            "shape_type": "RECTANGLE",
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
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": box.x,
            "y": box.y,
            "width": box.width,
            "height": 4.0,
            "background_color": COLOR_BLUE_ACCENT,
            "id": stripe_id,
        })

        # 3. Step Number Badge
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
            "color": COLOR_TEXT_WHITE,
            "background_color": COLOR_BLUE_ACCENT,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "center",
            "id": badge_id,
        })

        # 4. Step Title
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": s_title,
            "x": box.x + 12.0,
            "y": box.y + 50.0,
            "width": box.width - 24.0,
            "height": 32.0,
            "font_size": 14.0,
            "bold": True,
            "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": titl_id,
        })

        # 5. Step Divider
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": box.x + 12.0,
            "y": box.y + 86.0,
            "width": box.width - 24.0,
            "height": 1.0,
            "background_color": COLOR_DIVIDER,
            "id": div_id,
        })

        # 6. Step Description
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": s_desc,
            "x": box.x + 12.0,
            "y": box.y + 94.0,
            "width": box.width - 24.0,
            "height": 168.0,
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
                "color": COLOR_BLUE_ACCENT,
                "end_arrow": "FILL_ARROW",
                "id": conn_id,
            })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops


# =============================================================================
# Archetype 6: Executive 1-Liner Grid (2x2 Quadrants)
# =============================================================================


def generate_executive_grid(
    slide_id: str,
    title: str,
    subtitle: str,
    kicker: str,
    quadrants: list[Union[dict[str, Any], QuadrantSpec]],
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 6: Executive 1-Liner Grid.

    Features: 4-quadrant 2x2 grid, vertical blue accent bar, number badge pill,
    bold 1-liner header, and concise narrative description.
    """
    slide_idx = _extract_slide_idx(slide_id)
    if len(quadrants) != 4:
        raise ValueError(f"Archetype 6 requires exactly 4 quadrants, got {len(quadrants)}")

    grid_bounds = calculate_2x2_grid_bounds()

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_BG_LIGHT},
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
            num_val = raw_q.get("number", q_num)
            num_str = f"{int(num_val):02d}" if str(num_val).isdigit() else str(num_val)
            q_title = raw_q.get("title", f"Pillar {q_num}")
            q_desc = raw_q.get("description", "")

        box = grid_bounds[i]

        quad_id = f"QUAD_S{slide_idx}_Q{q_num}"
        stripe_id = f"STRIPE_S{slide_idx}_Q{q_num}"
        pill_id = f"PILL_S{slide_idx}_Q{q_num}"
        titl_id = f"TITL_S{slide_idx}_Q{q_num}"
        body_id = f"BODY_S{slide_idx}_Q{q_num}"

        # 1. Quadrant Container Shape
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
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

        # 2. Left Vertical Blue Accent Stripe
        ops.append({
            "op": "add-shape",
            "slide": slide_id,
            "shape_type": "RECTANGLE",
            "x": box.x,
            "y": box.y,
            "width": 4.0,
            "height": box.height,
            "background_color": COLOR_BLUE_ACCENT,
            "id": stripe_id,
        })

        # 3. Number Pill [01]
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": num_str,
            "x": box.x + 16.0,
            "y": box.y + 12.0,
            "width": 38.0,
            "height": 22.0,
            "font_size": 11.0,
            "bold": True,
            "color": COLOR_BLUE_TEXT,
            "background_color": COLOR_BLUE_LIGHT,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "center",
            "id": pill_id,
        })

        # 4. Pillar Header 1-Liner
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": q_title,
            "x": box.x + 60.0,
            "y": box.y + 12.0,
            "width": box.width - 76.0,
            "height": 24.0,
            "font_size": 14.0,
            "bold": True,
            "color": COLOR_TEXT_PRIMARY,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "left",
            "id": titl_id,
        })

        # 5. Pillar Body Narrative
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": q_desc,
            "x": box.x + 16.0,
            "y": box.y + 42.0,
            "width": box.width - 32.0,
            "height": 76.0,
            "font_size": 11.5,
            "color": COLOR_TEXT_MUTED,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "left",
            "line_spacing": 135,
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

    Features: Side-by-side anti-pattern (red banner) vs blueprint standard (green banner),
    high-contrast card containers, check/cross bullets, optional synthesis takeaway pill,
    and speaker notes.
    """
    slide_idx = _extract_slide_idx(slide_id)
    col_bounds = calculate_n_column_bounds(n=2, gap=24.0)

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_BG_LIGHT},
    ]

    # Universal Header
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    # Parse Don't and Do Items
    dont_list = dont_items.get("items", []) if isinstance(dont_items, dict) else dont_items
    do_list = do_items.get("items", []) if isinstance(do_items, dict) else do_items

    dont_banner_title = "✗ ANTI-PATTERNS (DON'T)"
    do_banner_title = "✓ BLUEPRINT STANDARD (DO)"

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
        "shape_type": "RECTANGLE",
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
        "x": box_dont.x,
        "y": box_dont.y,
        "width": box_dont.width,
        "height": 38.0,
        "background_color": COLOR_RED_LIGHT,
        "id": f"BANNER_S{slide_idx}_DONT",
    })
    # Banner Text
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": dont_banner_title,
        "x": box_dont.x + 14.0,
        "y": box_dont.y + 8.0,
        "width": box_dont.width - 28.0,
        "height": 22.0,
        "font_size": 12.5,
        "bold": True,
        "color": COLOR_RED_TEXT,
        "font_family": FONT_FAMILY_BODY,
        "alignment": "left",
        "id": f"TITL_S{slide_idx}_DONT",
    })
    # Banner Bottom Line
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "RECTANGLE",
        "x": box_dont.x,
        "y": box_dont.y + 38.0,
        "width": box_dont.width,
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

    # 2. Right Card: Do / Blueprint Standard
    box_do = col_bounds[1]
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "RECTANGLE",
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
        "x": box_do.x,
        "y": box_do.y,
        "width": box_do.width,
        "height": 38.0,
        "background_color": COLOR_GREEN_LIGHT,
        "id": f"BANNER_S{slide_idx}_DO",
    })
    # Banner Text
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": do_banner_title,
        "x": box_do.x + 14.0,
        "y": box_do.y + 8.0,
        "width": box_do.width - 28.0,
        "height": 22.0,
        "font_size": 12.5,
        "bold": True,
        "color": COLOR_GREEN_TEXT,
        "font_family": FONT_FAMILY_BODY,
        "alignment": "left",
        "id": f"TITL_S{slide_idx}_DO",
    })
    # Banner Bottom Line
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "RECTANGLE",
        "x": box_do.x,
        "y": box_do.y + 38.0,
        "width": box_do.width,
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

    Features: Asymmetric split layout (3 action principles on left + dark navy roadmap
    and blue CTA button on right).
    """
    slide_idx = _extract_slide_idx(slide_id)
    left_box, right_box = calculate_asymmetric_split_bounds()

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_BG_LIGHT},
    ]

    # Universal Header
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    # =========================================================================
    # Left Panel: 3 Action Principles Container
    # =========================================================================
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "RECTANGLE",
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

        # Number Badge Pill
        ops.append({
            "op": "add-textbox",
            "slide": slide_id,
            "text": num_str,
            "x": left_box.x + 16.0,
            "y": geom["badge_y"],
            "width": 38.0,
            "height": 22.0,
            "font_size": 11.0,
            "bold": True,
            "color": COLOR_BLUE_TEXT,
            "background_color": COLOR_BLUE_LIGHT,
            "font_family": FONT_FAMILY_BODY,
            "alignment": "center",
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
    # Right Panel: Dark Navy Milestone Roadmap & CTA Button
    # =========================================================================
    # 2. Right Dark Navy Strategy Panel
    clean_roadmap_title = (roadmap_title or "NEXT STEPS & ROADMAP").strip().upper()
    title_len = len(clean_roadmap_title)

    # Dynamic title height & divider placement based on title length
    if title_len <= 20:
        # 1-line title (e.g. "NEXT STEPS & ROADMAP")
        rtitle_font_size = 13.0
        rtitle_h = 22.0
        rdiv_y = right_box.y + 40.0
        rbody_y = right_box.y + 48.0
    else:
        # 2-line title (e.g. "10-MINUTE DEPLOYMENT ROADMAP")
        rtitle_font_size = 12.0
        rtitle_h = 32.0
        rdiv_y = right_box.y + 52.0
        rbody_y = right_box.y + 60.0

    # Calculate CTA button dimensions and position
    if cta_text:
        btn_h = 34.0
        btn_y = right_box.y + right_box.height - 44.0
        rbody_h = max(60.0, btn_y - rbody_y - 10.0)
    else:
        btn_h = 0.0
        btn_y = right_box.y + right_box.height
        rbody_h = right_box.height - (rbody_y - right_box.y) - 16.0

    # Format body bullets and scale typography
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
        "shape_type": "RECTANGLE",
        "x": right_box.x,
        "y": right_box.y,
        "width": right_box.width,
        "height": right_box.height,
        "background_color": COLOR_NAVY_PRIMARY,
        "id": f"PANEL_S{slide_idx}_RIGHT",
    })
    ops.append({
        "op": "style-shape",
        "element": f"PANEL_S{slide_idx}_RIGHT",
        "outline_color": "#3949AB",
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

    # Inner Roadmap Divider (Positioned safely below title)
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "RECTANGLE",
        "x": right_box.x + 16.0,
        "y": rdiv_y,
        "width": right_box.width - 32.0,
        "height": 1.0,
        "background_color": "#3949AB",
        "id": f"DIV_S{slide_idx}_ROADMAP",
    })

    # Roadmap Items Body (Positioned between divider and CTA button)
    ops.append({
        "op": "add-textbox",
        "slide": slide_id,
        "text": roadmap_body,
        "x": right_box.x + 16.0,
        "y": rbody_y,
        "width": right_box.width - 32.0,
        "height": rbody_h,
        "font_size": rbody_font_size,
        "color": COLOR_BLUE_SUBTITLE,
        "font_family": FONT_FAMILY_BODY,
        "alignment": "left",
        "line_spacing": rbody_spacing,
        "id": f"BODY_S{slide_idx}_ROADMAP",
    })

    # Action CTA Button (Positioned at bottom with safe clearance)
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
            "y": btn_y + 7.0,
            "width": right_box.width - 32.0,
            "height": 20.0,
            "font_size": 11.5,
            "bold": True,
            "color": COLOR_TEXT_WHITE,
            "font_family": FONT_FAMILY_HEADING,
            "alignment": "center",
            "id": f"BTN_TXT_S{slide_idx}_CTA",
        })

    if speaker_notes:
        ops.append({"op": "set-notes", "slide": slide_id, "text": speaker_notes})

    return ops



# =============================================================================
# Archetype 9: Demo Pivot (Navy "switch to live demo" slide)
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

    Dark navy slide that signals the switch to a live demo: a red (#C5221F, AA on white text) "▶ LIVE DEMO"
    pill, a large white title (what the demo proves), an optional subtitle, and
    up to 3 "watch for" chips telling the audience what to notice.
    """
    slide_idx = _extract_slide_idx(slide_id)
    clean_title = (title or "").strip()
    title_font = 40.0 if len(clean_title) <= 30 else 32.0 if len(clean_title) <= 55 else 26.0
    items = [str(w).strip() for w in (watch_for or []) if str(w).strip()][:3]

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_NAVY_PRIMARY},
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": f"▶ {(kicker or 'LIVE DEMO').upper()}",
            "x": 36.0,
            "y": 92.0,
            "width": 150.0,
            "height": 26.0,
            "font_size": 12.0,
            "bold": True,
            "color": COLOR_TEXT_WHITE,
            "background_color": "#C5221F",
            "font_family": FONT_FAMILY_BODY,
            "alignment": "center",
            "id": f"PILL_S{slide_idx}_DEMO",
        },
        {
            "op": "add-textbox",
            "slide": slide_id,
            "text": clean_title,
            "x": 36.0,
            "y": 130.0,
            "width": 648.0,
            "height": 96.0,
            "font_size": title_font,
            "bold": True,
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
            "font_size": 16.0,
            "color": COLOR_BLUE_SUBTITLE,
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
            "color": COLOR_BLUE_SUBTITLE,
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
                "background_color": COLOR_NAVY_SURFACE,
                "font_family": FONT_FAMILY_BODY,
                "alignment": "center",
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
    speaker_notes: str = "",
) -> list[dict[str, Any]]:
    """Generates gslides batch operations for Archetype 10: Image Split.

    The escape hatch for visuals the archetype grid cannot express (Mermaid /
    draw.io diagrams rendered to PNG, product screenshots, charts):

    - `split`: bullets card (≤4 bullets) beside a framed image panel.
    - `full`: framed image across the whole content area.

    URL images are emitted as batch `add-image` ops. Local files are emitted as
    internal `_pending-image` markers that the compiler lifts into
    `BatchResult.pending_images`; the CLI uploads them after the batch runs.
    """
    slide_idx = _extract_slide_idx(slide_id)
    img = _normalize_image(image)
    layout = (image_layout or "split").strip().lower()
    side = (image_side or "right").strip().lower()
    caption = str(img.get("caption", "") or "").strip()

    ops: list[dict[str, Any]] = [
        {"op": "add-slide", "layout": "BLANK", "id": slide_id},
        {"op": "set-background", "slide": slide_id, "color": COLOR_BG_LIGHT},
    ]
    ops.extend(_build_header_ops(slide_id, slide_idx, title, subtitle, kicker))

    top_y, height = 100.0, 275.0
    if layout == "full":
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
            "shape_type": "RECTANGLE",
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
            "x": text_box.x,
            "y": text_box.y,
            "width": text_box.width,
            "height": 5.0,
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

    # Image frame
    frame_id = f"FRAME_S{slide_idx}_IMG"
    ops.append({
        "op": "add-shape",
        "slide": slide_id,
        "shape_type": "RECTANGLE",
        "x": img_box.x,
        "y": img_box.y,
        "width": img_box.width,
        "height": img_box.height,
        "background_color": COLOR_CARD_WHITE,
        "id": frame_id,
    })
    ops.append({
        "op": "style-shape",
        "element": frame_id,
        "outline_color": COLOR_CARD_BORDER,
        "outline_weight": 1.0,
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
    }

    @classmethod
    def generate_slide_ops(
        cls,
        slide_spec: Any,
        slide_index: int = 1,
    ) -> list[dict[str, Any]]:
        """Dispatches and generates gslides batch operations for any slide specification.

        Args:
            slide_spec: A Slide specification object or dictionary with 'archetype' and content.
            slide_index: 1-based slide index in the presentation.

        Returns:
            List of gslides batch operations.

        Raises:
            ValueError: If archetype type is unsupported.
        """
        # Extract dictionary representation if dataclass or object
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
        # Handle kebab-case and snake_case
        archetype = archetype.replace("-", "_")
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
            return generate_split_cards(
                slide_id=slide_id,
                title=title,
                subtitle=subtitle,
                kicker=kicker,
                cards=cards,
                speaker_notes=notes,
                foundation=foundation,
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
            quadrants = data.get("quadrants", [])
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
            
            # Support roadmap as dict or direct fields
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
                speaker_notes=notes,
            )

        else:
            raise ValueError(
                f"Unknown slide archetype: '{archetype}'. Supported archetypes: {list(cls.ARCHETYPE_DISPATCH.keys())}"
            )

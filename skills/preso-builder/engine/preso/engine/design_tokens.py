"""The AI Factory Blueprint Presentation Builder Design Tokens.

Defines canvas geometry, strict color palette tokens, typography scales,
and WCAG-compliant color helper functions.
"""

from __future__ import annotations

import re
from typing import Union

# =============================================================================
# 1. Canvas Standard Dimensions (16:9 Widescreen)
# =============================================================================
CANVAS_WIDTH: float = 720.0
CANVAS_HEIGHT: float = 405.0
CANVAS_ASPECT_RATIO: str = "16:9"

CANVAS_EMU_WIDTH: int = 9_144_000
CANVAS_EMU_HEIGHT: int = 5_143_500
PT_TO_EMU: int = 12_700

# Safe Margins
MARGIN_LEFT: float = 36.0
MARGIN_RIGHT: float = 36.0
MARGIN_TOP: float = 28.0
MARGIN_BOTTOM: float = 30.0

# Usable Zones
HEADER_BASELINE: float = 92.0
CONTENT_TOP: float = 100.0
USABLE_WIDTH: float = CANVAS_WIDTH - MARGIN_LEFT - MARGIN_RIGHT  # 648.0 pt
USABLE_HEIGHT: float = (CANVAS_HEIGHT - MARGIN_BOTTOM) - CONTENT_TOP  # 275.0 pt

# =============================================================================
# 2. Master Color Palette Tokens
# =============================================================================
# Navy Core
COLOR_NAVY_PRIMARY: str = "#1E2761"
COLOR_NAVY_SURFACE: str = "#2D3A8C"
COLOR_NAVY_DEEP: str = "#141A3E"

# Slate / Dark Terminal
COLOR_SLATE_DARK: str = "#202124"
COLOR_SLATE_HEADER: str = "#2D3035"

# Neutral / Canvas / Cards
COLOR_BG_LIGHT: str = "#F8F9FA"
COLOR_CARD_WHITE: str = "#FFFFFF"
COLOR_CARD_BORDER: str = "#DADCE0"
COLOR_DIVIDER: str = "#E0E0E0"
COLOR_TRANSPARENT: str = "transparent"

# Accent Blue
COLOR_BLUE_ACCENT: str = "#1A73E8"
COLOR_BLUE_LIGHT: str = "#E8F0FE"
COLOR_BLUE_SUBTITLE: str = "#CADCFC"

# Semantic Status: Green / Do
COLOR_GREEN_DO: str = "#1E8E3E"
COLOR_GREEN_LIGHT: str = "#E6F4EA"
COLOR_GREEN_BORDER: str = "#A8DAB5"

# Semantic Status: Red / Don't
COLOR_RED_DONT: str = "#D93025"
COLOR_RED_LIGHT: str = "#FCE8E6"
COLOR_RED_BORDER: str = "#F6AEA9"

# Semantic Status: Amber / Warning
COLOR_AMBER_WARN: str = "#F9AB00"
COLOR_AMBER_LIGHT: str = "#FEF7E0"

# Text Colors
COLOR_TEXT_PRIMARY: str = "#202124"
COLOR_TEXT_MUTED: str = "#5F6368"
COLOR_TEXT_TERTIARY: str = "#80868B"
COLOR_TEXT_WHITE: str = "#FFFFFF"
COLOR_TEXT_CODE: str = "#CADCFC"
COLOR_CODE_FILENAME: str = "#BDC1C6"

# High-Contrast Text Tokens (WCAG 2.1 AA Compliant on Tinted Surfaces)
COLOR_BLUE_TEXT: str = "#174EA6"  # Google Blue 800 (CR > 5.5:1 on #E8F0FE, > 5.9:1 on #F8F9FA)
COLOR_GREEN_TEXT: str = "#137333"  # Google Green 800 (CR > 4.8:1 on #E6F4EA, white on #137333 > 5.3:1)
COLOR_RED_TEXT: str = "#C5221F"  # Google Red 800 (CR > 4.8:1 on #FCE8E6, white on #C5221F > 5.4:1)
COLOR_AMBER_TEXT: str = "#7A4100"  # Google Amber 900 (CR > 5.0:1 on #FEF7E0)

# Terminal Traffic Light Dots
COLOR_DOT_RED: str = "#EA4335"
COLOR_DOT_YELLOW: str = "#FBBC04"
COLOR_DOT_GREEN: str = "#34A853"

# =============================================================================
# 3. Typography Hierarchy & Font Scales
# =============================================================================
FONT_FAMILY_HEADING: str = "Google Sans"
FONT_FAMILY_BODY: str = "Google Sans Text"
FONT_FAMILY_CODE: str = "Roboto Mono"

FONT_SIZE_CHAPTER_NUM: float = 84.0
FONT_SIZE_CHAPTER_TITLE: float = 36.0
FONT_SIZE_CHAPTER_SUBTITLE: float = 16.0
FONT_SIZE_SLIDE_TITLE: float = 24.0
FONT_SIZE_SLIDE_SUBTITLE: float = 13.0
FONT_SIZE_KICKER: float = 10.0
FONT_SIZE_CARD_HEADER: float = 16.0
FONT_SIZE_CARD_BODY: float = 12.0
FONT_SIZE_HERO_STAT: float = 54.0
FONT_SIZE_HERO_UNIT: float = 13.0
FONT_SIZE_HERO_DELTA: float = 11.0
FONT_SIZE_CODE_BODY: float = 10.5
FONT_SIZE_CODE_FILENAME: float = 11.0
FONT_SIZE_BADGE: float = 10.5
FONT_SIZE_FOOTER: float = 9.5

# =============================================================================
# 4. Color Helper Functions & WCAG Contrast Math
# =============================================================================
_HEX_COLOR_RE = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")


def ensure_hex(color_str: str) -> str:
    """Ensures a valid 6-character hex string format `#RRGGBB` or `transparent`.

    Args:
        color_str: Raw color string (e.g. '#1e2761', '1E2761', '#fff', 'transparent').

    Returns:
        Standard uppercase `#RRGGBB` hex string or 'transparent'.

    Raises:
        ValueError: If the hex color string is malformed.
    """
    cleaned = color_str.strip()
    if cleaned.lower() == "transparent":
        return "transparent"
    match = _HEX_COLOR_RE.match(cleaned)
    if not match:
        raise ValueError(f"Invalid hex color: {color_str}")
    hex_body = match.group(1)
    if len(hex_body) == 3:
        hex_body = "".join(c * 2 for c in hex_body)
    return f"#{hex_body.upper()}"


def hex_to_rgb(hex_code: str) -> tuple[int, int, int]:
    """Converts a hex color string to integer RGB tuple (0-255).

    Args:
        hex_code: Hex string (e.g. '#1E2761', '1e2761', '#fff').

    Returns:
        Tuple of (r, g, b) integers in range 0..255.
    """
    std_hex = ensure_hex(hex_code)
    if std_hex == "transparent":
        return (0, 0, 0)
    return (
        int(std_hex[1:3], 16),
        int(std_hex[3:5], 16),
        int(std_hex[5:7], 16),
    )


def hex_to_rgb_float(hex_code: str) -> tuple[float, float, float]:
    """Converts a hex color string to floating point RGB tuple (0.0-1.0).

    Args:
        hex_code: Hex string.

    Returns:
        Tuple of (r, g, b) floats in range 0.0..1.0.
    """
    r, g, b = hex_to_rgb(hex_code)
    return (r / 255.0, g / 255.0, b / 255.0)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Converts integer RGB values (0-255) to uppercase hex `#RRGGBB`.

    Args:
        r: Red component (0-255).
        g: Green component (0-255).
        b: Blue component (0-255).

    Returns:
        Formatted `#RRGGBB` string.
    """
    r_clamped = max(0, min(255, int(r)))
    g_clamped = max(0, min(255, int(g)))
    b_clamped = max(0, min(255, int(b)))
    return f"#{r_clamped:02X}{g_clamped:02X}{b_clamped:02X}"


def relative_luminance(
    color: Union[str, tuple[int, int, int], tuple[float, float, float]]
) -> float:
    """Calculates WCAG 2.1 relative luminance for a color.

    Formula: L = 0.2126 * R + 0.7152 * G + 0.0722 * B
    where R, G, B are linear channel luminances.

    Args:
        color: Hex string, (r, g, b) integer tuple (0-255), or float tuple (0.0-1.0).

    Returns:
        Relative luminance float in [0.0, 1.0].
    """
    if isinstance(color, str):
        r_f, g_f, b_f = hex_to_rgb_float(color)
    elif isinstance(color, (tuple, list)):
        if all(isinstance(c, int) for c in color) and any(c > 1 for c in color):
            r_f, g_f, b_f = [c / 255.0 for c in color]
        else:
            r_f, g_f, b_f = [float(c) for c in color]
    else:
        raise TypeError(f"Unsupported color type: {type(color)}")

    def _linearize(channel: float) -> float:
        if channel <= 0.04045:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    r_lin = _linearize(r_f)
    g_lin = _linearize(g_f)
    b_lin = _linearize(b_f)
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def contrast_ratio(
    color_a: Union[str, tuple[int, int, int], tuple[float, float, float]],
    color_b: Union[str, tuple[int, int, int], tuple[float, float, float]],
) -> float:
    """Calculates WCAG 2.1 contrast ratio between two colors.

    Formula: (L1 + 0.05) / (L2 + 0.05) where L1 is the lighter color.

    Args:
        color_a: First color (hex string or RGB tuple).
        color_b: Second color (hex string or RGB tuple).

    Returns:
        Contrast ratio float >= 1.0.
    """
    l1 = relative_luminance(color_a)
    l2 = relative_luminance(color_b)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def is_wcag_aa(
    fg_color: Union[str, tuple[int, int, int]],
    bg_color: Union[str, tuple[int, int, int]],
    is_large_text: bool = False,
) -> bool:
    """Determines whether a color pairing meets WCAG 2.1 AA compliance.

    Args:
        fg_color: Foreground text color.
        bg_color: Background fill color.
        is_large_text: True if text is >= 18pt or >= 14pt bold.

    Returns:
        True if contrast ratio meets or exceeds AA threshold (4.5:1 or 3.0:1).
    """
    ratio = contrast_ratio(fg_color, bg_color)
    threshold = 3.0 if is_large_text else 4.5
    return ratio >= threshold


def is_wcag_aaa(
    fg_color: Union[str, tuple[int, int, int]],
    bg_color: Union[str, tuple[int, int, int]],
    is_large_text: bool = False,
) -> bool:
    """Determines whether a color pairing meets WCAG 2.1 AAA compliance.

    Args:
        fg_color: Foreground text color.
        bg_color: Background fill color.
        is_large_text: True if text is >= 18pt or >= 14pt bold.

    Returns:
        True if contrast ratio meets or exceeds AAA threshold (7.0:1 or 4.5:1).
    """
    ratio = contrast_ratio(fg_color, bg_color)
    threshold = 4.5 if is_large_text else 7.0
    return ratio >= threshold

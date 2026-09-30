"""Shared text-fit heuristics used by both the spec validator and the QA verifier.

A single source of truth for "does this text fit in this box?" so that the
pre-build validator and the post-compile verifier can never disagree again.

The model is intentionally simple (average glyph width x font size) and is
calibrated to Google Sans / Google Sans Text / Roboto Mono as rendered by
Google Slides. It is a *risk estimate*, not a renderer: the authoritative
check is always the rendered-thumbnail audit (`preso audit`).
"""

from __future__ import annotations

from dataclasses import dataclass
import math

# Average glyph width as a fraction of font size.
CHAR_WIDTH_PROPORTIONAL: float = 0.52
CHAR_WIDTH_MONO: float = 0.60

# Horizontal inner padding Slides applies inside a textbox (each side, pt).
TEXTBOX_INNER_PADDING: float = 4.0

# Line height multiplier used for multi-line estimates.
LINE_HEIGHT_FACTOR: float = 1.20

# Overflow tolerance: text is only flagged when the estimated height exceeds
# the box by more than this ratio AND this absolute amount.
OVERFLOW_TOLERANCE_RATIO: float = 1.15
OVERFLOW_TOLERANCE_PT: float = 5.0


@dataclass(frozen=True)
class FitResult:
    """Outcome of a text-fit estimate for one textbox."""

    estimated_lines: int
    required_height: float
    box_height: float
    chars_per_line: int
    capacity_chars: int
    overflow: bool

    @property
    def margin_pct(self) -> float:
        """Percentage of vertical slack left in the box (negative = overflow)."""
        if self.box_height <= 0:
            return 0.0
        return round(((self.box_height - self.required_height) / self.box_height) * 100.0, 1)


def is_mono_font(font_family: str, element_id: str = "") -> bool:
    """Returns True when the textbox should be measured as monospace."""
    fam = (font_family or "").lower()
    return "mono" in fam or "code" in (element_id or "").lower()


def chars_per_line(box_width: float, font_size: float, mono: bool = False) -> int:
    """Estimated characters that fit on a single line of a textbox."""
    c_w = CHAR_WIDTH_MONO if mono else CHAR_WIDTH_PROPORTIONAL
    usable_w = max(10.0, box_width - 2 * TEXTBOX_INNER_PADDING)
    return max(1, math.floor(usable_w / (max(font_size, 1.0) * c_w)))


def max_lines(box_height: float, font_size: float) -> int:
    """Estimated number of lines that fit vertically inside a textbox."""
    tolerated = max(box_height * OVERFLOW_TOLERANCE_RATIO, box_height + OVERFLOW_TOLERANCE_PT)
    return max(1, math.floor((tolerated - 4.0) / (font_size * LINE_HEIGHT_FACTOR)))


def estimate_fit(
    text: str,
    box_width: float,
    box_height: float,
    font_size: float,
    mono: bool = False,
) -> FitResult:
    """Estimates wrapped line count and required height for text in a box."""
    cpl = chars_per_line(box_width, font_size, mono=mono)
    total_lines = 0
    for paragraph in (text or "").split("\n"):
        if not paragraph:
            total_lines += 1
            continue
        total_lines += max(1, math.ceil(len(paragraph) / cpl))

    if total_lines <= 1:
        req_height = font_size * 1.05
    else:
        req_height = total_lines * (font_size * LINE_HEIGHT_FACTOR) + 4.0

    overflow = req_height > max(box_height * OVERFLOW_TOLERANCE_RATIO, box_height + OVERFLOW_TOLERANCE_PT)
    capacity = cpl * max_lines(box_height, font_size)
    return FitResult(
        estimated_lines=total_lines,
        required_height=round(req_height, 1),
        box_height=box_height,
        chars_per_line=cpl,
        capacity_chars=capacity,
        overflow=overflow,
    )


def excess_chars(text: str, fit: FitResult) -> int:
    """Rough number of characters to cut so the text fits (0 when it fits)."""
    if not fit.overflow:
        return 0
    return max(1, len((text or "").replace("\n", "")) - fit.capacity_chars)

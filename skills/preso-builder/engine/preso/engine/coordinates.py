"""Pure Mathematical Layout Engine and Coordinate Calculations for Google Slides.

Provides deterministic coordinate generators, bounding box collision math,
and N-column / grid partition algorithms matching the Blueprint design system.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from preso.engine.design_tokens import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    CONTENT_TOP,
    MARGIN_BOTTOM,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    USABLE_HEIGHT,
    USABLE_WIDTH,
)


@dataclass(frozen=True)
class BoundingBox:
    """Represents a 2D rectangular bounding box in slide point coordinates."""

    x: float
    y: float
    width: float
    height: float

    @property
    def left(self) -> float:
        return self.x

    @property
    def top(self) -> float:
        return self.y

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center_x(self) -> float:
        return self.x + (self.width / 2.0)

    @property
    def center_y(self) -> float:
        return self.y + (self.height / 2.0)

    @property
    def area(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height)

    def intersects(self, other: BoundingBox) -> bool:
        """Determines if two bounding boxes overlap with positive intersection area."""
        # Non-overlapping conditions
        if (
            self.right <= other.left
            or self.left >= other.right
            or self.bottom <= other.top
            or self.top >= other.bottom
        ):
            return False
        return True

    def contains(self, other: BoundingBox) -> bool:
        """Determines if this bounding box completely encloses another bounding box."""
        return (
            self.left <= other.left
            and self.top <= other.top
            and self.right >= other.right
            and self.bottom >= other.bottom
        )

    def contains_point(self, px: float, py: float) -> bool:
        """Checks if a given coordinate (px, py) lies inside the bounding box."""
        return self.left <= px <= self.right and self.top <= py <= self.bottom

    def intersection(self, other: BoundingBox) -> Optional[BoundingBox]:
        """Calculates the intersection bounding box of two boxes, or None if disjoint."""
        if not self.intersects(other):
            return None
        ix = max(self.left, other.left)
        iy = max(self.top, other.top)
        iright = min(self.right, other.right)
        ibottom = min(self.bottom, other.bottom)
        return BoundingBox(
            x=round(ix, 2),
            y=round(iy, 2),
            width=round(iright - ix, 2),
            height=round(ibottom - iy, 2),
        )

    def union(self, other: BoundingBox) -> BoundingBox:
        """Calculates the minimal bounding box enclosing both boxes."""
        ux = min(self.left, other.left)
        uy = min(self.top, other.top)
        uright = max(self.right, other.right)
        ubottom = max(self.bottom, other.bottom)
        return BoundingBox(
            x=round(ux, 2),
            y=round(uy, 2),
            width=round(uright - ux, 2),
            height=round(ubottom - uy, 2),
        )

    def clamp(
        self,
        min_x: float = 0.0,
        min_y: float = 0.0,
        max_x: float = CANVAS_WIDTH,
        max_y: float = CANVAS_HEIGHT,
    ) -> BoundingBox:
        """Clamps the bounding box coordinates inside the given rectangular window."""
        cx = max(min_x, min(self.x, max_x))
        cy = max(min_y, min(self.y, max_y))
        c_right = max(cx, min(self.right, max_x))
        c_bottom = max(cy, min(self.bottom, max_y))
        return BoundingBox(
            x=round(cx, 2),
            y=round(cy, 2),
            width=round(c_right - cx, 2),
            height=round(c_bottom - cy, 2),
        )

    def rounded(self, digits: int = 2) -> BoundingBox:
        """Returns a new BoundingBox with values rounded to the given precision."""
        return BoundingBox(
            x=round(self.x, digits),
            y=round(self.y, digits),
            width=round(self.width, digits),
            height=round(self.height, digits),
        )

    def to_dict(self) -> dict[str, float]:
        """Serializes the bounding box to a dictionary format."""
        return {
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "width": round(self.width, 2),
            "height": round(self.height, 2),
        }


# =============================================================================
# Layout Functions
# =============================================================================


def calculate_header_bounds(
    margin_left: float = MARGIN_LEFT,
    top_y: float = 26.0,
    usable_width: float = USABLE_WIDTH,
) -> dict[str, BoundingBox]:
    """Calculates standardized header bounding boxes for content slides (Archetypes 2-8).

    Args:
        margin_left: Left margin offset (default: 36.0 pt).
        top_y: Top baseline for category kicker pill (default: 26.0 pt).
        usable_width: Available horizontal width (default: 648.0 pt).

    Returns:
        Dictionary containing 'kicker', 'title', and 'subtitle' BoundingBox objects.
    """
    kicker = BoundingBox(x=margin_left, y=top_y, width=160.0, height=18.0)
    title = BoundingBox(
        x=margin_left, y=top_y + 22.0, width=usable_width, height=28.0
    )  # y: 48.0
    subtitle = BoundingBox(
        x=margin_left, y=top_y + 50.0, width=usable_width, height=18.0
    )  # y: 76.0
    return {
        "kicker": kicker.rounded(),
        "title": title.rounded(),
        "subtitle": subtitle.rounded(),
    }


def calculate_n_column_bounds(
    n: int,
    left_margin: float = MARGIN_LEFT,
    right_margin: float = MARGIN_RIGHT,
    top_y: float = CONTENT_TOP,
    height: float = USABLE_HEIGHT,
    gap: float = 18.0,
    canvas_width: float = CANVAS_WIDTH,
) -> list[BoundingBox]:
    """Calculates exact bounding box coordinates for N side-by-side columns.

    Formula:
        W_avail = canvas_width - left_margin - right_margin
        W_col = (W_avail - (n - 1) * gap) / n
        X_i = left_margin + i * (W_col + gap)

    Args:
        n: Number of columns (>= 1).
        left_margin: Left canvas margin (default: 36.0 pt).
        right_margin: Right canvas margin (default: 36.0 pt).
        top_y: Top coordinate anchor (default: 100.0 pt).
        height: Column height (default: 275.0 pt).
        gap: Gap distance between adjacent columns (default: 18.0 pt).
        canvas_width: Total slide canvas width (default: 720.0 pt).

    Returns:
        List of N BoundingBox objects from left to right.

    Raises:
        ValueError: If n < 1.
    """
    if n < 1:
        raise ValueError(f"Number of columns must be >= 1, got {n}")

    usable_w = canvas_width - left_margin - right_margin
    total_gaps = (n - 1) * gap
    col_w = (usable_w - total_gaps) / float(n)

    columns = []
    for i in range(n):
        x = left_margin + i * (col_w + gap)
        columns.append(
            BoundingBox(
                x=round(x, 2),
                y=round(top_y, 2),
                width=round(col_w, 2),
                height=round(height, 2),
            )
        )
    return columns


def calculate_2x2_grid_bounds(
    left_margin: float = MARGIN_LEFT,
    right_margin: float = MARGIN_RIGHT,
    top_y: float = CONTENT_TOP,
    bottom_margin: float = MARGIN_BOTTOM,
    gap_x: float = 24.0,
    gap_y: float = 15.0,
    canvas_width: float = CANVAS_WIDTH,
    canvas_height: float = CANVAS_HEIGHT,
) -> list[BoundingBox]:
    """Calculates coordinates for a 2x2 executive quadrant grid (4 cards).

    Order returned: [Q1 (Top-Left), Q2 (Top-Right), Q3 (Bottom-Left), Q4 (Bottom-Right)].

    Args:
        left_margin: Left margin (default: 36.0 pt).
        right_margin: Right margin (default: 36.0 pt).
        top_y: Top starting position (default: 100.0 pt).
        bottom_margin: Bottom margin (default: 30.0 pt).
        gap_x: Horizontal gap between column 0 and column 1 (default: 24.0 pt).
        gap_y: Vertical gap between row 0 and row 1 (default: 15.0 pt).
        canvas_width: Canvas width (default: 720.0 pt).
        canvas_height: Canvas height (default: 405.0 pt).

    Returns:
        List of 4 BoundingBox objects [Q1, Q2, Q3, Q4].
    """
    usable_w = canvas_width - left_margin - right_margin
    usable_h = canvas_height - top_y - bottom_margin

    col_w = (usable_w - gap_x) / 2.0
    row_h = (usable_h - gap_y) / 2.0

    quadrants = []
    for row in range(2):
        y = top_y + row * (row_h + gap_y)
        for col in range(2):
            x = left_margin + col * (col_w + gap_x)
            quadrants.append(
                BoundingBox(
                    x=round(x, 2),
                    y=round(y, 2),
                    width=round(col_w, 2),
                    height=round(row_h, 2),
                )
            )
    return quadrants


def calculate_card_internal_bounds(
    card_bounds: BoundingBox,
    has_top_stripe: bool = True,
    has_category_pill: bool = True,
    padding_x: float = 16.0,
    padding_top: float = 14.0,
) -> dict[str, BoundingBox]:
    """Calculates internal component coordinates inside a standard card container.

    Args:
        card_bounds: Outer bounding box of the card container.
        has_top_stripe: Whether the card has a 5pt top accent stripe.
        has_category_pill: Whether the card includes a category pill tag.
        padding_x: Horizontal inner padding (default: 16.0 pt).
        padding_top: Top inner padding (default: 14.0 pt).

    Returns:
        Dictionary of BoundingBox objects for 'container', 'stripe', 'pill', 'title', 'divider', 'body'.
    """
    bx = card_bounds.x
    by = card_bounds.y
    bw = card_bounds.width
    bh = card_bounds.height

    inner_w = bw - (2 * padding_x)

    stripe = (
        BoundingBox(x=bx, y=by, width=bw, height=5.0)
        if has_top_stripe
        else BoundingBox(x=bx, y=by, width=0, height=0)
    )
    pill = (
        BoundingBox(
            x=bx + padding_x, y=by + padding_top, width=75.0, height=18.0
        )
        if has_category_pill
        else BoundingBox(x=bx, y=by, width=0, height=0)
    )
    title = BoundingBox(x=bx + padding_x, y=by + 38.0, width=inner_w, height=26.0)
    divider = BoundingBox(
        x=bx + padding_x, y=by + 68.0, width=inner_w, height=1.0
    )
    body_h = max(0.0, bh - 92.0)
    body = BoundingBox(
        x=bx + padding_x, y=by + 78.0, width=inner_w, height=body_h
    )

    return {
        "container": card_bounds,
        "stripe": stripe.rounded(),
        "pill": pill.rounded(),
        "title": title.rounded(),
        "divider": divider.rounded(),
        "body": body.rounded(),
    }


def calculate_asymmetric_split_bounds(
    left_width: float = 380.0,
    right_width: float = 244.0,
    gap: float = 24.0,
    left_margin: float = MARGIN_LEFT,
    top_y: float = CONTENT_TOP,
    height: float = USABLE_HEIGHT,
) -> tuple[BoundingBox, BoundingBox]:
    """Calculates bounding boxes for an asymmetric 2-panel layout (e.g. Archetype 8).

    Default values: Left panel = 380 pt, Right panel = 244 pt, Gap = 24 pt (total 648 pt).

    Args:
        left_width: Width of left panel in pt.
        right_width: Width of right panel in pt.
        gap: Gap between panels in pt.
        left_margin: Left starting margin.
        top_y: Top starting coordinate.
        height: Height of both panels.

    Returns:
        Tuple of (left_box, right_box) BoundingBox instances.
    """
    left_box = BoundingBox(
        x=round(left_margin, 2),
        y=round(top_y, 2),
        width=round(left_width, 2),
        height=round(height, 2),
    )
    right_x = left_margin + left_width + gap
    right_box = BoundingBox(
        x=round(right_x, 2),
        y=round(top_y, 2),
        width=round(right_width, 2),
        height=round(height, 2),
    )
    return left_box, right_box


# =============================================================================
# Collision and Canvas Bounds Checkers
# =============================================================================


def check_collision(box_a: BoundingBox, box_b: BoundingBox) -> bool:
    """Checks whether two bounding boxes collide / overlap."""
    return box_a.intersects(box_b)


def check_canvas_bounds(
    box: BoundingBox,
    canvas_width: float = CANVAS_WIDTH,
    canvas_height: float = CANVAS_HEIGHT,
    margin_left: float = 0.0,
    margin_top: float = 0.0,
    margin_right: float = 0.0,
    margin_bottom: float = 0.0,
) -> bool:
    """Validates that a bounding box is fully contained within the safe canvas bounds.

    Args:
        box: Bounding box to test.
        canvas_width: Width of canvas (720.0 pt).
        canvas_height: Height of canvas (405.0 pt).
        margin_left: Minimum allowed X.
        margin_top: Minimum allowed Y.
        margin_right: Safe margin on right.
        margin_bottom: Safe margin on bottom.

    Returns:
        True if bounding box is strictly within bounds, False otherwise.
    """
    min_x = margin_left
    min_y = margin_top
    max_x = canvas_width - margin_right
    max_y = canvas_height - margin_bottom

    return (
        box.left >= min_x - 1e-4
        and box.top >= min_y - 1e-4
        and box.right <= max_x + 1e-4
        and box.bottom <= max_y + 1e-4
    )


def find_collisions(boxes: list[BoundingBox]) -> list[tuple[int, int]]:
    """Identifies all pairwise overlapping boxes in a list.

    Args:
        boxes: List of BoundingBox instances.

    Returns:
        List of index pairs (i, j) where box i and box j overlap (with i < j).
    """
    collisions = []
    n = len(boxes)
    for i in range(n):
        for j in range(i + 1, n):
            if boxes[i].intersects(boxes[j]):
                collisions.append((i, j))
    return collisions

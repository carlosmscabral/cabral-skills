"""Unit tests for preso.engine.coordinates module."""

import unittest

from preso.engine.coordinates import (
    BoundingBox,
    calculate_2x2_grid_bounds,
    calculate_asymmetric_split_bounds,
    calculate_card_internal_bounds,
    calculate_header_bounds,
    calculate_n_column_bounds,
    check_canvas_bounds,
    check_collision,
    find_collisions,
)
from preso.engine.design_tokens import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    CONTENT_TOP,
    MARGIN_BOTTOM,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    MARGIN_TOP,
    USABLE_HEIGHT,
    USABLE_WIDTH,
)


class TestBoundingBox(unittest.TestCase):
    """Tests BoundingBox geometry, properties, and boolean operations."""

    def setUp(self):
        self.box1 = BoundingBox(x=10.0, y=20.0, width=100.0, height=50.0)
        self.box2 = BoundingBox(x=50.0, y=30.0, width=100.0, height=50.0)
        self.box_disjoint = BoundingBox(x=200.0, y=200.0, width=50.0, height=50.0)
        self.box_touching = BoundingBox(x=110.0, y=20.0, width=50.0, height=50.0)

    def test_properties(self):
        self.assertEqual(self.box1.left, 10.0)
        self.assertEqual(self.box1.top, 20.0)
        self.assertEqual(self.box1.right, 110.0)
        self.assertEqual(self.box1.bottom, 70.0)
        self.assertEqual(self.box1.center_x, 60.0)
        self.assertEqual(self.box1.center_y, 45.0)
        self.assertEqual(self.box1.area, 5000.0)

    def test_intersects(self):
        self.assertTrue(self.box1.intersects(self.box2))
        self.assertTrue(self.box2.intersects(self.box1))
        self.assertFalse(self.box1.intersects(self.box_disjoint))
        # Edge-touching without area is considered non-intersecting
        self.assertFalse(self.box1.intersects(self.box_touching))

    def test_contains(self):
        outer = BoundingBox(x=0.0, y=0.0, width=200.0, height=200.0)
        inner = BoundingBox(x=20.0, y=20.0, width=50.0, height=50.0)
        partial = BoundingBox(x=150.0, y=150.0, width=100.0, height=100.0)

        self.assertTrue(outer.contains(inner))
        self.assertTrue(outer.contains(outer))
        self.assertFalse(outer.contains(partial))
        self.assertFalse(inner.contains(outer))

    def test_contains_point(self):
        self.assertTrue(self.box1.contains_point(10.0, 20.0))  # top-left
        self.assertTrue(self.box1.contains_point(110.0, 70.0))  # bottom-right
        self.assertTrue(self.box1.contains_point(60.0, 45.0))  # center
        self.assertFalse(self.box1.contains_point(9.9, 20.0))
        self.assertFalse(self.box1.contains_point(110.1, 70.0))

    def test_intersection(self):
        # Overlapping intersection
        inter = self.box1.intersection(self.box2)
        self.assertIsNotNone(inter)
        self.assertEqual(inter.x, 50.0)
        self.assertEqual(inter.y, 30.0)
        self.assertEqual(inter.width, 60.0)  # 110 - 50 = 60
        self.assertEqual(inter.height, 40.0)  # 70 - 30 = 40

        # Disjoint intersection returns None
        self.assertIsNone(self.box1.intersection(self.box_disjoint))

    def test_union(self):
        u = self.box1.union(self.box2)
        self.assertEqual(u.x, 10.0)
        self.assertEqual(u.y, 20.0)
        self.assertEqual(u.right, 150.0)
        self.assertEqual(u.bottom, 80.0)

    def test_clamp(self):
        out_of_bounds = BoundingBox(x=-20.0, y=-10.0, width=100.0, height=800.0)
        clamped = out_of_bounds.clamp(min_x=0.0, min_y=0.0, max_x=720.0, max_y=405.0)
        self.assertEqual(clamped.x, 0.0)
        self.assertEqual(clamped.y, 0.0)
        self.assertEqual(clamped.right, 80.0)
        self.assertEqual(clamped.bottom, 405.0)

    def test_to_dict_and_rounded(self):
        b = BoundingBox(x=10.3456, y=20.7891, width=30.1234, height=40.5678)
        d = b.to_dict()
        self.assertEqual(d, {"x": 10.35, "y": 20.79, "width": 30.12, "height": 40.57})
        r = b.rounded(1)
        self.assertEqual(r, BoundingBox(x=10.3, y=20.8, width=30.1, height=40.6))


class TestLayoutAlgorithms(unittest.TestCase):
    """Tests mathematical coordinate functions for headers, columns, and grids."""

    def test_calculate_header_bounds(self):
        bounds = calculate_header_bounds()
        self.assertIn("kicker", bounds)
        self.assertIn("title", bounds)
        self.assertIn("subtitle", bounds)

        k = bounds["kicker"]
        t = bounds["title"]
        s = bounds["subtitle"]

        self.assertEqual(k.x, MARGIN_LEFT)
        self.assertEqual(k.y, 26.0)
        self.assertEqual(t.x, MARGIN_LEFT)
        self.assertEqual(t.y, 48.0)
        self.assertEqual(t.width, USABLE_WIDTH)
        self.assertEqual(s.x, MARGIN_LEFT)
        self.assertEqual(s.y, 76.0)
        self.assertEqual(s.width, USABLE_WIDTH)

        # Header area must end before content top (100.0 pt)
        self.assertLess(s.bottom, CONTENT_TOP)

    def test_calculate_n_column_bounds_single_col(self):
        cols = calculate_n_column_bounds(n=1)
        self.assertEqual(len(cols), 1)
        self.assertEqual(cols[0].x, MARGIN_LEFT)
        self.assertEqual(cols[0].y, CONTENT_TOP)
        self.assertEqual(cols[0].width, USABLE_WIDTH)
        self.assertEqual(cols[0].height, USABLE_HEIGHT)

    def test_calculate_n_column_bounds_2_card(self):
        cols = calculate_n_column_bounds(n=2, gap=24.0)
        self.assertEqual(len(cols), 2)
        # Card 1: x = 36.0, w = 312.0
        self.assertEqual(cols[0].x, 36.0)
        self.assertEqual(cols[0].width, 312.0)
        self.assertEqual(cols[0].height, 275.0)
        # Card 2: x = 372.0, w = 312.0
        self.assertEqual(cols[1].x, 372.0)
        self.assertEqual(cols[1].width, 312.0)
        # Verify right boundary matches right margin
        self.assertEqual(cols[1].right, CANVAS_WIDTH - MARGIN_RIGHT)
        # No overlap
        self.assertFalse(cols[0].intersects(cols[1]))

    def test_calculate_n_column_bounds_3_card(self):
        cols = calculate_n_column_bounds(n=3, gap=18.0)
        self.assertEqual(len(cols), 3)
        # Card 1: x = 36.0, w = 204.0
        self.assertEqual(cols[0].x, 36.0)
        self.assertEqual(cols[0].width, 204.0)
        # Card 2: x = 258.0, w = 204.0
        self.assertEqual(cols[1].x, 258.0)
        self.assertEqual(cols[1].width, 204.0)
        # Card 3: x = 480.0, w = 204.0
        self.assertEqual(cols[2].x, 480.0)
        self.assertEqual(cols[2].width, 204.0)
        # Verify right boundary
        self.assertEqual(cols[2].right, CANVAS_WIDTH - MARGIN_RIGHT)
        # All mutually disjoint
        self.assertEqual(len(find_collisions(cols)), 0)

    def test_calculate_n_column_bounds_4_step(self):
        cols = calculate_n_column_bounds(n=4, gap=24.0)
        self.assertEqual(len(cols), 4)
        # W_col = (648 - 72) / 4 = 144.0
        for i in range(4):
            self.assertEqual(cols[i].width, 144.0)
            self.assertEqual(cols[i].height, 275.0)
            self.assertTrue(check_canvas_bounds(cols[i]))
        self.assertEqual(cols[0].x, 36.0)
        self.assertEqual(cols[1].x, 204.0)
        self.assertEqual(cols[2].x, 372.0)
        self.assertEqual(cols[3].x, 540.0)
        self.assertEqual(cols[3].right, CANVAS_WIDTH - MARGIN_RIGHT)
        self.assertEqual(len(find_collisions(cols)), 0)

    def test_calculate_n_column_bounds_invalid_n(self):
        with self.assertRaises(ValueError):
            calculate_n_column_bounds(n=0)
        with self.assertRaises(ValueError):
            calculate_n_column_bounds(n=-1)

    def test_calculate_2x2_grid_bounds(self):
        quads = calculate_2x2_grid_bounds(gap_x=24.0, gap_y=15.0)
        self.assertEqual(len(quads), 4)

        q1, q2, q3, q4 = quads
        # Check Q1 (Top-Left)
        self.assertEqual(q1.x, 36.0)
        self.assertEqual(q1.y, 100.0)
        self.assertEqual(q1.width, 312.0)
        self.assertEqual(q1.height, 130.0)

        # Check Q2 (Top-Right)
        self.assertEqual(q2.x, 372.0)
        self.assertEqual(q2.y, 100.0)
        self.assertEqual(q2.width, 312.0)
        self.assertEqual(q2.height, 130.0)

        # Check Q3 (Bottom-Left)
        self.assertEqual(q3.x, 36.0)
        self.assertEqual(q3.y, 245.0)
        self.assertEqual(q3.width, 312.0)
        self.assertEqual(q3.height, 130.0)

        # Check Q4 (Bottom-Right)
        self.assertEqual(q4.x, 372.0)
        self.assertEqual(q4.y, 245.0)
        self.assertEqual(q4.width, 312.0)
        self.assertEqual(q4.height, 130.0)

        # Bottom bounds check (y = 245 + 130 = 375 = 405 - 30)
        self.assertEqual(q3.bottom, CANVAS_HEIGHT - MARGIN_BOTTOM)
        self.assertEqual(q4.bottom, CANVAS_HEIGHT - MARGIN_BOTTOM)

        # Zero collisions among all 4 quadrants
        self.assertEqual(len(find_collisions(quads)), 0)

    def test_calculate_card_internal_bounds(self):
        card = BoundingBox(x=36.0, y=100.0, width=312.0, height=275.0)
        internals = calculate_card_internal_bounds(card)

        self.assertIn("container", internals)
        self.assertIn("stripe", internals)
        self.assertIn("pill", internals)
        self.assertIn("title", internals)
        self.assertIn("divider", internals)
        self.assertIn("body", internals)

        # All internal boxes must be fully contained within the card container
        self.assertTrue(card.contains(internals["stripe"]))
        self.assertTrue(card.contains(internals["pill"]))
        self.assertTrue(card.contains(internals["title"]))
        self.assertTrue(card.contains(internals["divider"]))
        self.assertTrue(card.contains(internals["body"]))

    def test_calculate_asymmetric_split_bounds(self):
        left, right = calculate_asymmetric_split_bounds(
            left_width=380.0, right_width=244.0, gap=24.0
        )
        self.assertEqual(left.x, 36.0)
        self.assertEqual(left.width, 380.0)
        self.assertEqual(left.height, 275.0)

        self.assertEqual(right.x, 440.0)
        self.assertEqual(right.width, 244.0)
        self.assertEqual(right.height, 275.0)

        # Total width check: 380 + 24 + 244 = 648
        self.assertEqual(left.width + 24.0 + right.width, USABLE_WIDTH)
        self.assertEqual(right.right, CANVAS_WIDTH - MARGIN_RIGHT)
        self.assertFalse(left.intersects(right))


class TestCollisionAndCanvasCheckers(unittest.TestCase):
    """Tests collision detection and canvas boundary validators."""

    def test_check_collision(self):
        b1 = BoundingBox(x=0, y=0, width=50, height=50)
        b2 = BoundingBox(x=25, y=25, width=50, height=50)
        b3 = BoundingBox(x=100, y=100, width=50, height=50)

        self.assertTrue(check_collision(b1, b2))
        self.assertFalse(check_collision(b1, b3))

    def test_check_canvas_bounds(self):
        valid_box = BoundingBox(x=36, y=28, width=648, height=347)
        self.assertTrue(
            check_canvas_bounds(
                valid_box,
                margin_left=36,
                margin_top=28,
                margin_right=36,
                margin_bottom=30,
            )
        )

        out_left = BoundingBox(x=10, y=28, width=100, height=100)
        self.assertFalse(check_canvas_bounds(out_left, margin_left=36))

        out_bottom = BoundingBox(x=36, y=300, width=100, height=100)
        self.assertFalse(check_canvas_bounds(out_bottom, margin_bottom=30))

    def test_find_collisions(self):
        b1 = BoundingBox(x=0, y=0, width=50, height=50)
        b2 = BoundingBox(x=25, y=25, width=50, height=50)
        b3 = BoundingBox(x=100, y=100, width=50, height=50)
        b4 = BoundingBox(x=120, y=120, width=50, height=50)

        collisions = find_collisions([b1, b2, b3, b4])
        self.assertIn((0, 1), collisions)
        self.assertIn((2, 3), collisions)
        self.assertEqual(len(collisions), 2)


if __name__ == "__main__":
    unittest.main()

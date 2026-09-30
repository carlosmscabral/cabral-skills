"""Unit tests for preso.engine.design_tokens module."""

import unittest

from preso.engine.design_tokens import (
    CANVAS_ASPECT_RATIO,
    CANVAS_EMU_HEIGHT,
    CANVAS_EMU_WIDTH,
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
    COLOR_NAVY_DEEP,
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
    COLOR_TEXT_TERTIARY,
    COLOR_TEXT_WHITE,
    COLOR_TRANSPARENT,
    CONTENT_TOP,
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
    FONT_SIZE_FOOTER,
    FONT_SIZE_HERO_DELTA,
    FONT_SIZE_HERO_STAT,
    FONT_SIZE_HERO_UNIT,
    FONT_SIZE_KICKER,
    FONT_SIZE_SLIDE_SUBTITLE,
    FONT_SIZE_SLIDE_TITLE,
    HEADER_BASELINE,
    MARGIN_BOTTOM,
    MARGIN_LEFT,
    MARGIN_RIGHT,
    MARGIN_TOP,
    PT_TO_EMU,
    USABLE_HEIGHT,
    USABLE_WIDTH,
    contrast_ratio,
    ensure_hex,
    hex_to_rgb,
    hex_to_rgb_float,
    is_wcag_aa,
    is_wcag_aaa,
    relative_luminance,
    rgb_to_hex,
)


class TestDesignTokens(unittest.TestCase):
    """Tests design token constants and canvas geometry."""

    def test_canvas_dimensions(self):
        self.assertEqual(CANVAS_WIDTH, 720.0)
        self.assertEqual(CANVAS_HEIGHT, 405.0)
        self.assertEqual(CANVAS_ASPECT_RATIO, "16:9")
        self.assertEqual(MARGIN_LEFT, 36.0)
        self.assertEqual(MARGIN_RIGHT, 36.0)
        self.assertEqual(MARGIN_TOP, 28.0)
        self.assertEqual(MARGIN_BOTTOM, 30.0)
        self.assertEqual(CONTENT_TOP, 100.0)
        self.assertEqual(HEADER_BASELINE, 92.0)
        self.assertEqual(USABLE_WIDTH, 648.0)
        self.assertEqual(USABLE_HEIGHT, 275.0)
        self.assertEqual(CANVAS_EMU_WIDTH, 9144000)
        self.assertEqual(CANVAS_EMU_HEIGHT, 5143500)
        self.assertEqual(PT_TO_EMU, 12700)
        self.assertEqual(CANVAS_WIDTH * PT_TO_EMU, CANVAS_EMU_WIDTH)
        self.assertEqual(CANVAS_HEIGHT * PT_TO_EMU, CANVAS_EMU_HEIGHT)

    def test_color_token_values(self):
        tokens = [
            COLOR_NAVY_PRIMARY,
            COLOR_NAVY_SURFACE,
            COLOR_NAVY_DEEP,
            COLOR_SLATE_DARK,
            COLOR_SLATE_HEADER,
            COLOR_BG_LIGHT,
            COLOR_CARD_WHITE,
            COLOR_CARD_BORDER,
            COLOR_BLUE_ACCENT,
            COLOR_BLUE_LIGHT,
            COLOR_BLUE_SUBTITLE,
            COLOR_BLUE_TEXT,
            COLOR_GREEN_DO,
            COLOR_GREEN_LIGHT,
            COLOR_GREEN_BORDER,
            COLOR_GREEN_TEXT,
            COLOR_RED_DONT,
            COLOR_RED_LIGHT,
            COLOR_RED_BORDER,
            COLOR_RED_TEXT,
            COLOR_AMBER_WARN,
            COLOR_AMBER_LIGHT,
            COLOR_AMBER_TEXT,
            COLOR_TEXT_PRIMARY,
            COLOR_TEXT_MUTED,
            COLOR_TEXT_TERTIARY,
            COLOR_TEXT_WHITE,
            COLOR_TEXT_CODE,
            COLOR_CODE_FILENAME,
            COLOR_DOT_RED,
            COLOR_DOT_YELLOW,
            COLOR_DOT_GREEN,
            COLOR_DIVIDER,
        ]
        for token in tokens:
            self.assertTrue(token.startswith("#"), f"Token {token} should start with #")
            self.assertEqual(len(token), 7, f"Token {token} should be #RRGGBB")
            self.assertEqual(token, ensure_hex(token))

        self.assertEqual(COLOR_TRANSPARENT, "transparent")
        self.assertEqual(ensure_hex("transparent"), "transparent")

    def test_typography_tokens(self):
        self.assertEqual(FONT_FAMILY_HEADING, "Google Sans")
        self.assertEqual(FONT_FAMILY_BODY, "Google Sans Text")
        self.assertEqual(FONT_FAMILY_CODE, "Roboto Mono")

        sizes = [
            FONT_SIZE_CHAPTER_NUM,
            FONT_SIZE_CHAPTER_TITLE,
            FONT_SIZE_CHAPTER_SUBTITLE,
            FONT_SIZE_SLIDE_TITLE,
            FONT_SIZE_SLIDE_SUBTITLE,
            FONT_SIZE_KICKER,
            FONT_SIZE_CARD_HEADER,
            FONT_SIZE_CARD_BODY,
            FONT_SIZE_HERO_STAT,
            FONT_SIZE_HERO_UNIT,
            FONT_SIZE_HERO_DELTA,
            FONT_SIZE_CODE_BODY,
            FONT_SIZE_CODE_FILENAME,
            FONT_SIZE_BADGE,
            FONT_SIZE_FOOTER,
        ]
        for sz in sizes:
            self.assertGreater(sz, 0.0)

        self.assertEqual(FONT_SIZE_CHAPTER_NUM, 84.0)
        self.assertEqual(FONT_SIZE_CHAPTER_TITLE, 36.0)
        self.assertEqual(FONT_SIZE_HERO_STAT, 54.0)


class TestColorUtilities(unittest.TestCase):
    """Tests color conversion and WCAG math functions."""

    def test_ensure_hex(self):
        self.assertEqual(ensure_hex("#1e2761"), "#1E2761")
        self.assertEqual(ensure_hex("1E2761"), "#1E2761")
        self.assertEqual(ensure_hex("#fff"), "#FFFFFF")
        self.assertEqual(ensure_hex("fff"), "#FFFFFF")
        self.assertEqual(ensure_hex("#000"), "#000000")
        self.assertEqual(ensure_hex("transparent"), "transparent")
        self.assertEqual(ensure_hex("TRANSPARENT"), "transparent")

        with self.assertRaises(ValueError):
            ensure_hex("#GGGGGG")
        with self.assertRaises(ValueError):
            ensure_hex("12345")
        with self.assertRaises(ValueError):
            ensure_hex("")

    def test_hex_to_rgb(self):
        self.assertEqual(hex_to_rgb("#FFFFFF"), (255, 255, 255))
        self.assertEqual(hex_to_rgb("#000000"), (0, 0, 0))
        self.assertEqual(hex_to_rgb("#1E2761"), (30, 39, 97))
        self.assertEqual(hex_to_rgb("#1A73E8"), (26, 115, 232))
        self.assertEqual(hex_to_rgb("transparent"), (0, 0, 0))

    def test_hex_to_rgb_float(self):
        r, g, b = hex_to_rgb_float("#FFFFFF")
        self.assertAlmostEqual(r, 1.0)
        self.assertAlmostEqual(g, 1.0)
        self.assertAlmostEqual(b, 1.0)

        r0, g0, b0 = hex_to_rgb_float("#000000")
        self.assertAlmostEqual(r0, 0.0)
        self.assertAlmostEqual(g0, 0.0)
        self.assertAlmostEqual(b0, 0.0)

    def test_rgb_to_hex(self):
        self.assertEqual(rgb_to_hex(255, 255, 255), "#FFFFFF")
        self.assertEqual(rgb_to_hex(0, 0, 0), "#000000")
        self.assertEqual(rgb_to_hex(30, 39, 97), "#1E2761")
        # Test clamping
        self.assertEqual(rgb_to_hex(300, -10, 100), "#FF0064")

    def test_relative_luminance(self):
        self.assertAlmostEqual(relative_luminance("#000000"), 0.0, places=4)
        self.assertAlmostEqual(relative_luminance("#FFFFFF"), 1.0, places=4)
        self.assertAlmostEqual(relative_luminance((255, 255, 255)), 1.0, places=4)
        self.assertAlmostEqual(relative_luminance((0, 0, 0)), 0.0, places=4)
        lum_navy = relative_luminance(COLOR_NAVY_PRIMARY)
        self.assertGreater(lum_navy, 0.0)
        self.assertLess(lum_navy, 0.1)

    def test_contrast_ratio(self):
        # Black vs White is 21:1
        self.assertAlmostEqual(contrast_ratio("#FFFFFF", "#000000"), 21.0, places=1)
        # Symmetry
        self.assertAlmostEqual(
            contrast_ratio("#FFFFFF", "#1E2761"),
            contrast_ratio("#1E2761", "#FFFFFF"),
        )
        # Same color is 1:1
        self.assertAlmostEqual(contrast_ratio("#1E2761", "#1E2761"), 1.0)
        # White on Navy is AAA compliant (> 7.0:1 and ~13.8:1)
        cr_white_navy = contrast_ratio(COLOR_TEXT_WHITE, COLOR_NAVY_PRIMARY)
        self.assertGreater(cr_white_navy, 13.5)

    def test_wcag_compliance_levels(self):
        # White on Navy (#1E2761) passes AAA
        self.assertTrue(is_wcag_aa(COLOR_TEXT_WHITE, COLOR_NAVY_PRIMARY))
        self.assertTrue(is_wcag_aaa(COLOR_TEXT_WHITE, COLOR_NAVY_PRIMARY))

        # Ice blue (#CADCFC) on Navy (#1E2761) passes AAA (> 10:1)
        self.assertTrue(is_wcag_aa(COLOR_BLUE_SUBTITLE, COLOR_NAVY_PRIMARY))
        self.assertTrue(is_wcag_aaa(COLOR_BLUE_SUBTITLE, COLOR_NAVY_PRIMARY))

        # Dark slate (#202124) on White (#FFFFFF) passes AAA (> 16:1)
        self.assertTrue(is_wcag_aa(COLOR_TEXT_PRIMARY, COLOR_CARD_WHITE))
        self.assertTrue(is_wcag_aaa(COLOR_TEXT_PRIMARY, COLOR_CARD_WHITE))

        # Muted text (#5F6368) on White passes AA
        self.assertTrue(is_wcag_aa(COLOR_TEXT_MUTED, COLOR_CARD_WHITE))

        # Google blue (#1A73E8) on White passes AA (4.52:1)
        self.assertTrue(is_wcag_aa(COLOR_BLUE_ACCENT, COLOR_CARD_WHITE))

        # High-contrast text tokens meet WCAG AA (>= 4.5:1) on their target tinted backgrounds
        self.assertTrue(is_wcag_aa(COLOR_BLUE_TEXT, COLOR_BG_LIGHT))  # > 5.9:1
        self.assertTrue(is_wcag_aa(COLOR_BLUE_TEXT, COLOR_BLUE_LIGHT))  # > 5.5:1
        self.assertTrue(is_wcag_aa(COLOR_GREEN_TEXT, COLOR_GREEN_LIGHT))  # > 4.8:1
        self.assertTrue(is_wcag_aa(COLOR_TEXT_WHITE, COLOR_GREEN_TEXT))  # > 5.3:1
        self.assertTrue(is_wcag_aa(COLOR_RED_TEXT, COLOR_RED_LIGHT))  # > 4.8:1
        self.assertTrue(is_wcag_aa(COLOR_TEXT_WHITE, COLOR_RED_TEXT))  # > 5.4:1
        self.assertTrue(is_wcag_aa(COLOR_AMBER_TEXT, COLOR_AMBER_LIGHT))  # > 5.0:1

        # Large text check
        self.assertTrue(is_wcag_aa("#767676", "#FFFFFF", is_large_text=True))


if __name__ == "__main__":
    unittest.main()

"""Multimodal Visual QA Verifier for The AI Factory Blueprint Presentations.

Performs deterministic mathematical and visual verification on presentation specifications,
generated atomic batch payloads, and rendered Google Slides presentations:
1. Spec validation and text character budget compliance.
2. Bounding box safe canvas containment within 720x405pt canvas and overlap collision math.
3. WCAG 2.1 AA/AAA contrast ratio verification across all foreground/background pairings.
4. Text capacity and line overflow estimation heuristics.
5. Thumbnail export verification and visual audit via GSlidesClient.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
import re
from typing import Any, Optional, Union

from preso.compiler.batch_generator import BatchCompiler, BatchResult
from preso.compiler.gslides_client import GSlidesClient
from preso.engine import text_fit
from preso.engine.design_tokens import (
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    COLOR_BG_LIGHT,
    COLOR_CARD_WHITE,
    COLOR_NAVY_PRIMARY,
    COLOR_NAVY_SURFACE,
    COLOR_SLATE_DARK,
    COLOR_SLATE_HEADER,
    FONT_FAMILY_BODY,
    FONT_FAMILY_HEADING,
    contrast_ratio,
    ensure_hex,
    is_wcag_aa,
    is_wcag_aaa,
)
from preso.spec.models import PresentationSpec, SlideSpec
from preso.spec.validator import SpecValidator, ValidationResult

# =============================================================================
# Canvas & Margin Boundaries
# =============================================================================

SAFE_MARGIN_LEFT: float = 25.0
SAFE_MARGIN_RIGHT: float = 25.0
SAFE_MARGIN_TOP: float = 20.0
SAFE_MARGIN_BOTTOM: float = 20.0

SAFE_BOUNDS_X_MIN: float = SAFE_MARGIN_LEFT
SAFE_BOUNDS_Y_MIN: float = SAFE_MARGIN_TOP
SAFE_BOUNDS_X_MAX: float = CANVAS_WIDTH - SAFE_MARGIN_RIGHT  # 695.0
SAFE_BOUNDS_Y_MAX: float = CANVAS_HEIGHT - SAFE_MARGIN_BOTTOM  # 385.0


# =============================================================================
# QA Report Data Model
# =============================================================================


@dataclass
class QAReport:
    """Structured artifact containing the full evaluation results of a presentation QA pass."""

    is_passing: bool = True
    total_checks: int = 0
    passed_checks: int = 0
    violations: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[dict[str, Any]] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    detailed_checks: list[dict[str, Any]] = field(default_factory=list)
    slide_reports: list[dict[str, Any]] = field(default_factory=list)

    @property
    def failed_checks(self) -> int:
        """Returns the total number of failed check items."""
        return self.total_checks - self.passed_checks

    @property
    def error_count(self) -> int:
        """Returns total error violations count."""
        return len([v for v in self.violations if v.get("severity") == "error"])

    @property
    def warning_count(self) -> int:
        """Returns total warning count."""
        return len(self.warnings) + len(
            [v for v in self.violations if v.get("severity") == "warning"]
        )

    @property
    def pass_rate_pct(self) -> float:
        """Calculates pass rate percentage (0.0 - 100.0)."""
        if self.total_checks == 0:
            return 100.0
        return round((self.passed_checks / self.total_checks) * 100.0, 2)

    def is_clean(self) -> bool:
        """Returns True if there are zero errors and zero warnings."""
        return self.is_passing and len(self.violations) == 0 and len(self.warnings) == 0

    def to_dict(self) -> dict[str, Any]:
        """Serializes the QA report into a standard dictionary."""
        return {
            "is_passing": self.is_passing,
            "total_checks": self.total_checks,
            "passed_checks": self.passed_checks,
            "failed_checks": self.failed_checks,
            "pass_rate_pct": self.pass_rate_pct,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "violations": self.violations,
            "warnings": self.warnings,
            "metrics": self.metrics,
            "detailed_checks": self.detailed_checks,
            "slide_reports": self.slide_reports,
        }

    def to_json(self, indent: int = 2) -> str:
        """Serializes the QA report into a formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def summary(self) -> str:
        """Returns a formatted executive summary string for CLI and logs."""
        status_badge = "PASS" if self.is_passing else "FAIL"
        lines = [
            f"================================================================================",
            f"QA VERIFICATION REPORT: {status_badge} ({self.passed_checks}/{self.total_checks} checks passed, {self.pass_rate_pct:.1f}%)",
            f"================================================================================",
            f"Total Checks:     {self.total_checks}",
            f"Passed:           {self.passed_checks}",
            f"Violations/Errors:{len(self.violations)}",
            f"Warnings:         {len(self.warnings)}",
            f"Slides Evaluated: {self.metrics.get('slide_count', 0)}",
            f"WCAG Compliance:  {self.metrics.get('wcag_aa_compliance_pct', 100.0):.1f}% AA ({self.metrics.get('wcag_aaa_passes', 0)} AAA)",
            f"Min Contrast:     {self.metrics.get('min_contrast_ratio', 0.0):.2f}:1 (Avg: {self.metrics.get('avg_contrast_ratio', 0.0):.2f}:1)",
            f"Geometry Status:  {'CLEAN' if self.metrics.get('geometry_violations', 0) == 0 else 'VIOLATIONS DETECTED'}",
            f"Slides w/ Notes:  {self.metrics.get('speaker_notes_valid_count', 0)}/{self.metrics.get('speaker_notes_total_slides', 0)} (optional)",
        ]
        if self.violations:
            lines.append("--------------------------------------------------------------------------------")
            lines.append("VIOLATIONS:")
            for idx, v in enumerate(self.violations, start=1):
                sev = v.get("severity", "error").upper()
                chk = v.get("check_type", "general")
                slide = v.get("slide_index", "?")
                msg = v.get("message", "")
                lines.append(f"  {idx}. [{sev}] [Slide {slide}] [{chk}] {msg}")
        if self.warnings:
            lines.append("--------------------------------------------------------------------------------")
            lines.append("WARNINGS:")
            for idx, w in enumerate(self.warnings, start=1):
                chk = w.get("check_type", "general")
                slide = w.get("slide_index", "?")
                msg = w.get("message", "")
                lines.append(f"  {idx}. [WARN] [Slide {slide}] [{chk}] {msg}")
        lines.append("================================================================================")
        return "\n".join(lines)


# =============================================================================
# QAVerifier Engine
# =============================================================================


class QAVerifier:
    """Automated multimodal verification engine for presentations.

    Executes a comprehensive verification battery:
    1. Spec validation against schema rules and text-budget limits.
    2. Geometry & layout bounding box clamping and non-overlap detection.
    3. WCAG 2.1 AA/AAA contrast ratio calculations.
    4. Text capacity and line overflow estimation.
    5. Speaker notes coverage (informational only; notes are optional).
    6. Slide thumbnail export & visual asset verification.
    """

    def __init__(
        self,
        gslides_client: Optional[GSlidesClient] = None,
        strict_mode: bool = False,
    ) -> None:
        """Initializes the QAVerifier.

        Args:
            gslides_client: Optional GSlidesClient instance for live API calls.
            strict_mode: If True, treats warnings as failure-inducing violations.
        """
        self.gslides_client = gslides_client or GSlidesClient(dry_run=True)
        self.strict_mode = strict_mode

    # -------------------------------------------------------------------------
    # 1. Spec Verification
    # -------------------------------------------------------------------------

    def verify_spec(
        self,
        spec: Union[PresentationSpec, dict[str, Any], Path, str],
    ) -> tuple[bool, list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """Validates presentation specification against schema constraints and text budgets.

        Returns:
            Tuple of (is_valid, violations, warnings, metrics).
        """
        violations: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        metrics: dict[str, Any] = {
            "spec_checks_total": 0,
            "spec_checks_passed": 0,
        }

        # Parse spec if needed
        p_spec: PresentationSpec
        if isinstance(spec, PresentationSpec):
            p_spec = spec
        elif isinstance(spec, (Path, str)):
            p_spec = PresentationSpec.from_yaml(spec)
        elif isinstance(spec, dict):
            p_spec = PresentationSpec.from_dict(spec)
        else:
            raise TypeError(f"Unsupported spec type: {type(spec)}")

        # Run SpecValidator
        val_result: ValidationResult = SpecValidator.validate(p_spec)
        metrics["spec_checks_total"] = 1 + len(val_result.errors) + len(val_result.warnings)

        if val_result.is_valid:
            metrics["spec_checks_passed"] += 1
        else:
            for err in val_result.errors:
                violations.append({
                    "check_type": "spec_schema",
                    "severity": "error",
                    "slide_index": 0,
                    "message": err,
                    "details": {"validator_error": err},
                })

        for warn in val_result.warnings:
            warnings.append({
                "check_type": "spec_warning",
                "severity": "warning",
                "slide_index": 0,
                "message": warn,
                "details": {"validator_warning": warn},
            })

        metrics["spec_valid"] = val_result.is_valid
        metrics["spec_error_count"] = len(val_result.errors)
        metrics["spec_warning_count"] = len(val_result.warnings)

        return val_result.is_valid, violations, warnings, metrics

    # -------------------------------------------------------------------------
    # 2. Geometry & Canvas Containment Verification
    # -------------------------------------------------------------------------

    def verify_batch_geometry(
        self,
        operations: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
        """Validates bounding boxes for canvas containment and collision non-overlap.

        Args:
            operations: List of batch operations conforming to gslides schema.

        Returns:
            Tuple of (violations, warnings, metrics, element_records).
        """
        violations: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        element_records: list[dict[str, Any]] = []

        # Group operations by slide
        slides_ops: list[dict[str, Any]] = []
        current_slide: dict[str, Any] = {"id": "ROOT", "ops": [], "slide_index": 0}

        slide_counter = 0
        for op in operations:
            op_name = op.get("op", "")
            if op_name == "add-slide":
                slide_counter += 1
                current_slide = {
                    "id": op.get("id", f"SLIDE_{slide_counter}"),
                    "ops": [op],
                    "slide_index": slide_counter,
                }
                slides_ops.append(current_slide)
            else:
                if not slides_ops:
                    slide_counter = 1
                    current_slide = {
                        "id": "SLIDE_01",
                        "ops": [op],
                        "slide_index": 1,
                    }
                    slides_ops.append(current_slide)
                else:
                    slides_ops[-1]["ops"].append(op)

        total_geom_checks = 0
        passed_geom_checks = 0
        overlap_violations = 0
        out_of_bounds_violations = 0

        for slide_data in slides_ops:
            slide_id = slide_data["id"]
            slide_idx = slide_data["slide_index"]
            ops = slide_data["ops"]

            # Collect visual elements on this slide
            visual_elements: list[dict[str, Any]] = []
            for op in ops:
                op_type = op.get("op")
                if op_type in ("add-shape", "add-textbox", "add-line", "add-table"):
                    x = float(op.get("x", 0.0))
                    y = float(op.get("y", 0.0))
                    w = float(op.get("width", 0.0))
                    h = float(op.get("height", 0.0))
                    elem_id = op.get("id", f"elem_{len(visual_elements)}")
                    shape_type = op.get("shape", op_type)
                    is_bg = (
                        (w >= 700.0 and h >= 400.0)
                        or "bg" in elem_id.lower()
                        or "background" in elem_id.lower()
                    )

                    elem_info = {
                        "slide_id": slide_id,
                        "slide_index": slide_idx,
                        "id": elem_id,
                        "op": op_type,
                        "shape_type": shape_type,
                        "x": x,
                        "y": y,
                        "width": w,
                        "height": h,
                        "x_max": x + w,
                        "y_max": y + h,
                        "is_background": is_bg,
                        "raw_op": op,
                    }
                    visual_elements.append(elem_info)
                    element_records.append(elem_info)

            # Check 1: Canvas containment for every element
            for elem in visual_elements:
                total_geom_checks += 1
                x = elem["x"]
                y = elem["y"]
                w = elem["width"]
                h = elem["height"]
                elem_id = elem["id"]
                is_bg = elem["is_background"]

                # Strict canvas containment bounds (720x405 pt)
                eps = 0.5  # rounding tolerance
                is_contained = (
                    x >= -eps
                    and y >= -eps
                    and (x + w) <= (CANVAS_WIDTH + eps)
                    and (y + h) <= (CANVAS_HEIGHT + eps)
                )

                if not is_contained:
                    out_of_bounds_violations += 1
                    violations.append({
                        "check_type": "geometry_canvas_overflow",
                        "severity": "error",
                        "slide_index": slide_idx,
                        "element_id": elem_id,
                        "message": (
                            f"Element '{elem_id}' exceeds canvas boundaries: "
                            f"bounds=({x:.1f}, {y:.1f}, {w:.1f}, {h:.1f}), "
                            f"max=({x+w:.1f}, {y+h:.1f}) vs canvas=(720, 405)"
                        ),
                        "details": elem,
                    })
                else:
                    passed_geom_checks += 1

                # Safe margin check for interactive content (non-background)
                if not is_bg and w < 700.0:
                    if x < 15.0 or y < 15.0 or (x + w) > 705.0 or (y + h) > 395.0:
                        warnings.append({
                            "check_type": "geometry_margin_warning",
                            "severity": "warning",
                            "slide_index": slide_idx,
                            "element_id": elem_id,
                            "message": (
                                f"Element '{elem_id}' is close to canvas edge: "
                                f"bounds=({x:.1f}, {y:.1f}, {w:.1f}, {h:.1f})"
                            ),
                            "details": elem,
                        })

            # Check 2: Overlap collision math between sibling content elements
            # Filter to non-background elements
            content_elems = [e for e in visual_elements if not e["is_background"]]
            for i in range(len(content_elems)):
                for j in range(i + 1, len(content_elems)):
                    e1 = content_elems[i]
                    e2 = content_elems[j]

                    # Skip parent-child containment (e.g. textbox inside a card shape)
                    # Check if e1 encloses e2 or e2 encloses e1
                    e1_contains_e2 = (
                        e1["x"] <= e2["x"] + 1.0
                        and e1["y"] <= e2["y"] + 1.0
                        and e1["x_max"] >= e2["x_max"] - 1.0
                        and e1["y_max"] >= e2["y_max"] - 1.0
                    )
                    e2_contains_e1 = (
                        e2["x"] <= e1["x"] + 1.0
                        and e2["y"] <= e1["y"] + 1.0
                        and e2["x_max"] >= e1["x_max"] - 1.0
                        and e2["y_max"] >= e1["y_max"] - 1.0
                    )

                    if e1_contains_e2 or e2_contains_e1:
                        # Legitimate container-child relationship (e.g. card box + card text)
                        continue

                    # Skip decorative lines/dividers and dots
                    if (
                        e1["op"] == "add-line"
                        or e2["op"] == "add-line"
                        or e1["width"] <= 15.0
                        or e2["width"] <= 15.0
                        or e1["height"] <= 15.0
                        or e2["height"] <= 15.0
                    ):
                        continue

                    # Calculate 2D intersection
                    overlap_w = max(
                        0.0,
                        min(e1["x_max"], e2["x_max"]) - max(e1["x"], e2["x"]),
                    )
                    overlap_h = max(
                        0.0,
                        min(e1["y_max"], e2["y_max"]) - max(e1["y"], e2["y"]),
                    )
                    overlap_area = overlap_w * overlap_h

                    total_geom_checks += 1
                    # A significant collision between distinct sibling items (> 5 pt^2)
                    if overlap_area > 5.0:
                        overlap_violations += 1
                        violations.append({
                            "check_type": "geometry_overlap_collision",
                            "severity": "error",
                            "slide_index": slide_idx,
                            "element_id": f"{e1['id']} <-> {e2['id']}",
                            "message": (
                                f"Improper overlap ({overlap_area:.1f} pt²) between sibling elements "
                                f"'{e1['id']}' and '{e2['id']}' on Slide {slide_idx}"
                            ),
                            "details": {
                                "element_1": e1["id"],
                                "element_2": e2["id"],
                                "overlap_area": overlap_area,
                                "bounds_1": (e1["x"], e1["y"], e1["width"], e1["height"]),
                                "bounds_2": (e2["x"], e2["y"], e2["width"], e2["height"]),
                            },
                        })
                    else:
                        passed_geom_checks += 1

        metrics = {
            "geometry_checks_total": total_geom_checks,
            "geometry_checks_passed": passed_geom_checks,
            "geometry_violations": out_of_bounds_violations + overlap_violations,
            "out_of_bounds_count": out_of_bounds_violations,
            "overlap_collision_count": overlap_violations,
            "total_elements_evaluated": len(element_records),
        }

        return violations, warnings, metrics, element_records

    # -------------------------------------------------------------------------
    # 3. WCAG 2.1 AA/AAA Contrast Ratio Verification
    # -------------------------------------------------------------------------

    def verify_contrast(
        self,
        operations: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
        """Evaluates WCAG 2.1 AA and AAA contrast compliance across all text/background pairings.

        Args:
            operations: Batch operations array.

        Returns:
            Tuple of (violations, warnings, metrics, contrast_records).
        """
        violations: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        contrast_records: list[dict[str, Any]] = []

        # Track slide backgrounds and shapes per slide
        current_slide_id = "SLIDE_01"
        current_slide_idx = 1
        slide_backgrounds: dict[str, str] = {}
        slide_shapes: dict[str, list[dict[str, Any]]] = {}

        for op in operations:
            op_type = op.get("op")
            if op_type == "add-slide":
                current_slide_id = op.get("id", f"SLIDE_{len(slide_backgrounds)+1}")
                current_slide_idx = len(slide_backgrounds) + 1
                slide_backgrounds[current_slide_id] = "#FFFFFF"
                slide_shapes[current_slide_id] = []
            elif op_type == "set-background":
                bg_color = op.get("color", "#FFFFFF")
                slide_backgrounds[current_slide_id] = bg_color
            elif op_type == "add-shape":
                slide_shapes.setdefault(current_slide_id, []).append(op)

        total_contrast_checks = 0
        aa_passes = 0
        aaa_passes = 0
        failures = 0
        contrast_ratios: list[float] = []

        current_slide_id = "SLIDE_01"
        current_slide_idx = 1

        for op in operations:
            op_type = op.get("op")
            if op_type == "add-slide":
                current_slide_id = op.get("id", "SLIDE_01")
                # find index
                current_slide_idx = list(slide_backgrounds.keys()).index(current_slide_id) + 1
                continue

            if op_type == "add-textbox":
                total_contrast_checks += 1
                elem_id = op.get("id", "text")
                text = op.get("text", "")
                fg_raw = op.get("color", "#202124")
                font_size = float(op.get("font_size", 12.0))
                is_bold = bool(op.get("bold", False))
                is_large = font_size >= 18.0 or (font_size >= 14.0 and is_bold)

                # Normalize foreground
                try:
                    fg = ensure_hex(fg_raw)
                except ValueError:
                    fg = "#202124"

                # Determine effective background color
                explicit_bg = op.get("background_color")
                if explicit_bg and explicit_bg.lower() != "transparent":
                    try:
                        bg = ensure_hex(explicit_bg)
                    except ValueError:
                        bg = "#FFFFFF"
                else:
                    # Check containing shapes on this slide
                    tb_x = float(op.get("x", 0.0))
                    tb_y = float(op.get("y", 0.0))
                    tb_w = float(op.get("width", 0.0))
                    tb_h = float(op.get("height", 0.0))
                    center_x = tb_x + tb_w / 2.0
                    center_y = tb_y + tb_h / 2.0

                    slide_bg = slide_backgrounds.get(current_slide_id, "#FFFFFF")
                    containing_bg = slide_bg

                    shapes = slide_shapes.get(current_slide_id, [])
                    # Sort shapes by area ascending (innermost shape first)
                    sorted_shapes = sorted(
                        shapes,
                        key=lambda s: float(s.get("width", 0.0)) * float(s.get("height", 0.0)),
                    )
                    for s in sorted_shapes:
                        sx = float(s.get("x", 0.0))
                        sy = float(s.get("y", 0.0))
                        sw = float(s.get("width", 0.0))
                        sh = float(s.get("height", 0.0))
                        if sx <= center_x <= sx + sw and sy <= center_y <= sy + sh:
                            s_bg = s.get("background_color")
                            if s_bg and s_bg.lower() != "transparent":
                                try:
                                    containing_bg = ensure_hex(s_bg)
                                except ValueError:
                                    pass
                                break

                    bg = containing_bg

                # Calculate contrast ratio
                cr = contrast_ratio(fg, bg)
                contrast_ratios.append(cr)
                aa = is_wcag_aa(fg, bg, is_large_text=is_large)
                aaa = is_wcag_aaa(fg, bg, is_large_text=is_large)

                rec = {
                    "slide_id": current_slide_id,
                    "slide_index": current_slide_idx,
                    "element_id": elem_id,
                    "text_sample": (text.replace("\n", " ")[:35] + ("..." if len(text) > 35 else "")),
                    "fg_color": fg,
                    "bg_color": bg,
                    "font_size": font_size,
                    "is_bold": is_bold,
                    "is_large_text": is_large,
                    "contrast_ratio": round(cr, 2),
                    "wcag_aa": aa,
                    "wcag_aaa": aaa,
                    "threshold_required": "3.0:1 (large text)" if is_large else "4.5:1 (normal text)",
                }
                contrast_records.append(rec)

                if aa:
                    aa_passes += 1
                else:
                    failures += 1
                    violations.append({
                        "check_type": "wcag_contrast_aa_failure",
                        "severity": "error",
                        "slide_index": current_slide_idx,
                        "element_id": elem_id,
                        "message": (
                            f"WCAG AA contrast violation on Slide {current_slide_idx} ({elem_id}): "
                            f"{fg} on {bg} yields {cr:.2f}:1 (requires {rec['threshold_required']})"
                        ),
                        "details": rec,
                    })

                if aaa:
                    aaa_passes += 1

        min_cr = min(contrast_ratios) if contrast_ratios else 0.0
        max_cr = max(contrast_ratios) if contrast_ratios else 0.0
        avg_cr = sum(contrast_ratios) / len(contrast_ratios) if contrast_ratios else 0.0
        aa_rate = (aa_passes / total_contrast_checks * 100.0) if total_contrast_checks > 0 else 100.0

        metrics = {
            "contrast_checks_total": total_contrast_checks,
            "contrast_aa_passes": aa_passes,
            "contrast_aaa_passes": aaa_passes,
            "contrast_failures": failures,
            "wcag_aa_compliance_pct": round(aa_rate, 2),
            "min_contrast_ratio": round(min_cr, 2),
            "max_contrast_ratio": round(max_cr, 2),
            "avg_contrast_ratio": round(avg_cr, 2),
        }

        return violations, warnings, metrics, contrast_records

    # -------------------------------------------------------------------------
    # 4. Text Capacity & Overflow Estimation
    # -------------------------------------------------------------------------

    def verify_text_overflow(
        self,
        operations: list[dict[str, Any]],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
        """Calculates line wrap and height requirements to detect text overflow."""
        violations: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        overflow_records: list[dict[str, Any]] = []

        total_text_checks = 0
        overflow_warnings = 0

        current_slide_idx = 0
        for op in operations:
            if op.get("op") == "add-slide":
                current_slide_idx += 1
                continue

            if op.get("op") == "add-textbox":
                total_text_checks += 1
                elem_id = op.get("id", "text")
                text = op.get("text", "")
                font_size = float(op.get("font_size", 12.0))
                font_family = op.get("font_family", FONT_FAMILY_BODY)
                box_w = float(op.get("width", 200.0))
                box_h = float(op.get("height", 50.0))

                fit = text_fit.estimate_fit(
                    text,
                    box_width=box_w,
                    box_height=box_h,
                    font_size=font_size,
                    mono=text_fit.is_mono_font(font_family, elem_id),
                )
                over_by = text_fit.excess_chars(text, fit)
                total_lines = fit.estimated_lines
                req_height = fit.required_height
                margin_pct = fit.margin_pct
                is_overflow = fit.overflow

                rec = {
                    "slide_index": current_slide_idx,
                    "element_id": elem_id,
                    "char_count": len(text),
                    "font_size": font_size,
                    "box_width": box_w,
                    "box_height": box_h,
                    "estimated_lines": total_lines,
                    "required_height": round(req_height, 1),
                    "margin_pct": margin_pct,
                    "capacity_chars": fit.capacity_chars,
                    "excess_chars": over_by,
                    "overflow": is_overflow,
                }
                overflow_records.append(rec)

                if is_overflow:
                    overflow_warnings += 1
                    warnings.append({
                        "check_type": "text_overflow_risk",
                        "severity": "warning",
                        "slide_index": current_slide_idx,
                        "element_id": elem_id,
                        "message": (
                            f"Potential text overflow in '{elem_id}' on Slide {current_slide_idx}: "
                            f"est. required height {req_height:.1f}pt > box height {box_h:.1f}pt "
                            f"(cut ~{over_by} chars; capacity ~{fit.capacity_chars})"
                        ),
                        "details": rec,
                    })

        metrics = {
            "text_overflow_checks_total": total_text_checks,
            "text_overflow_warnings": overflow_warnings,
            "text_capacity_pass_rate_pct": (
                round((total_text_checks - overflow_warnings) / total_text_checks * 100.0, 2)
                if total_text_checks > 0
                else 100.0
            ),
        }

        return violations, warnings, metrics, overflow_records

    # -------------------------------------------------------------------------
    # 5. Speaker Notes Completeness Audit
    # -------------------------------------------------------------------------

    def verify_speaker_notes(
        self,
        spec: Optional[PresentationSpec] = None,
        operations: Optional[list[dict[str, Any]]] = None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """Reports speaker-notes coverage as informational metrics only.

        Speaker notes are optional: missing or short notes never produce a
        violation or warning and do not affect the pass rate.
        """
        notes_list: list[str] = []
        if spec is not None:
            notes_list = [(s.speaker_notes or s.notes or "").strip() for s in spec.all_slides()]
        elif operations is not None:
            slide_notes: dict[int, str] = {}
            current_slide_idx = 0
            for op in operations:
                if op.get("op") == "add-slide":
                    current_slide_idx += 1
                    slide_notes[current_slide_idx] = ""
                elif op.get("op") == "set-notes":
                    slide_notes[current_slide_idx] = str(op.get("text") or op.get("notes") or "").strip()
            notes_list = list(slide_notes.values())

        total_slides = len(notes_list)
        with_notes = sum(1 for n in notes_list if n)
        word_counts = [len(n.split()) for n in notes_list if n]
        coverage = (with_notes / total_slides * 100.0) if total_slides > 0 else 0.0
        avg_words = sum(word_counts) / len(word_counts) if word_counts else 0.0

        metrics = {
            "speaker_notes_total_slides": total_slides,
            "speaker_notes_valid_count": with_notes,
            "speaker_notes_coverage_pct": round(coverage, 2),
            "speaker_notes_avg_words": round(avg_words, 1),
        }
        return [], [], metrics

    # -------------------------------------------------------------------------
    # 6. Live Thumbnail Verification
    # -------------------------------------------------------------------------

    def verify_live_deck_thumbnails(
        self,
        presentation_id: str,
        output_dir: Union[str, Path],
    ) -> tuple[list[Path], list[dict[str, Any]], dict[str, Any]]:
        """Exports slide thumbnails via GSlidesClient and verifies image artifacts.

        Args:
            presentation_id: Google Slides deck ID.
            output_dir: Target directory to save PNG thumbnails.

        Returns:
            Tuple of (exported_paths, warnings, metrics).
        """
        warnings: list[dict[str, Any]] = []
        exported_paths: list[Path] = []
        out_path = Path(output_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)
        # Remove renders from previous builds (slide IDs change between builds,
        # so old files would otherwise accumulate and pollute the audit).
        for stale in out_path.glob("slide_*.png"):
            try:
                stale.unlink()
            except OSError:
                pass

        try:
            slides = self.gslides_client.list_slides(presentation_id)
            if not slides:
                slides = [{"objectId": "p", "index": 0}]

            for idx, s in enumerate(slides, start=1):
                slide_id = str(s.get("objectId", s.get("id", f"slide_{idx}")))
                dest_file = out_path / f"slide_{idx:02d}_{slide_id}.png"
                exported = self.gslides_client.export_thumbnail(
                    presentation_id=presentation_id,
                    slide_id=slide_id,
                    output_path=dest_file,
                )
                if exported.exists() and exported.stat().st_size > 0:
                    exported_paths.append(exported)

            status = f"Exported {len(exported_paths)} thumbnails."
        except Exception as e:
            status = f"Thumbnail export skipped: {e}"
            warnings.append({
                "check_type": "thumbnail_export_warning",
                "severity": "warning",
                "slide_index": 0,
                "message": f"Could not export live deck thumbnails: {e}",
            })

        metrics = {
            "thumbnails_exported": len(exported_paths),
            "thumbnail_export_status": status,
        }

        return exported_paths, warnings, metrics

    # -------------------------------------------------------------------------
    # Master Verification Orchestrator
    # -------------------------------------------------------------------------

    def verify(
        self,
        spec: Optional[Union[PresentationSpec, dict[str, Any], Path, str]] = None,
        batch_result: Optional[Union[BatchResult, list[dict[str, Any]]]] = None,
        presentation_id: Optional[str] = None,
        thumbnail_dir: Optional[Union[str, Path]] = None,
    ) -> QAReport:
        """Executes the complete multimodal visual QA battery.

        Args:
            spec: Presentation specification.
            batch_result: Batch compilation result or raw operations array.
            presentation_id: Optional live presentation ID for thumbnail export.
            thumbnail_dir: Destination directory for thumbnails.

        Returns:
            Comprehensive QAReport artifact.
        """
        all_violations: list[dict[str, Any]] = []
        all_warnings: list[dict[str, Any]] = []
        combined_metrics: dict[str, Any] = {}
        all_detailed_checks: list[dict[str, Any]] = []
        slide_reports: list[dict[str, Any]] = []

        total_checks = 0
        passed_checks = 0

        # Step 1: Spec Validation
        parsed_spec: Optional[PresentationSpec] = None
        if spec is not None:
            if isinstance(spec, PresentationSpec):
                parsed_spec = spec
            elif isinstance(spec, (Path, str)):
                parsed_spec = PresentationSpec.from_yaml(spec)
            elif isinstance(spec, dict):
                parsed_spec = PresentationSpec.from_dict(spec)

            if parsed_spec is not None:
                spec_valid, spec_viols, spec_warns, spec_metrics = self.verify_spec(parsed_spec)
                all_violations.extend(spec_viols)
                all_warnings.extend(spec_warns)
                combined_metrics.update(spec_metrics)
                total_checks += spec_metrics.get("spec_checks_total", 1)
                passed_checks += spec_metrics.get("spec_checks_passed", 0)

        # Step 2: Compile Batch Payload if not provided
        ops: list[dict[str, Any]] = []
        if batch_result is not None:
            if isinstance(batch_result, BatchResult):
                ops = batch_result.operations
                combined_metrics.update(batch_result.stats)
            elif isinstance(batch_result, list):
                ops = batch_result
        elif parsed_spec is not None:
            compiler = BatchCompiler()
            compiled = compiler.compile(parsed_spec)
            ops = compiled.operations
            combined_metrics.update(compiled.stats)

        # Step 3: Geometry & Canvas Containment Checks
        if ops:
            geom_viols, geom_warns, geom_metrics, elem_records = self.verify_batch_geometry(ops)
            all_violations.extend(geom_viols)
            all_warnings.extend(geom_warns)
            combined_metrics.update(geom_metrics)
            total_checks += geom_metrics.get("geometry_checks_total", 0)
            passed_checks += geom_metrics.get("geometry_checks_passed", 0)

            # Step 4: WCAG Contrast Checks
            c_viols, c_warns, c_metrics, contrast_records = self.verify_contrast(ops)
            all_violations.extend(c_viols)
            all_warnings.extend(c_warns)
            combined_metrics.update(c_metrics)
            all_detailed_checks.extend(contrast_records)
            total_checks += c_metrics.get("contrast_checks_total", 0)
            passed_checks += c_metrics.get("contrast_aa_passes", 0)

            # Step 5: Text Overflow Checks
            t_viols, t_warns, t_metrics, text_records = self.verify_text_overflow(ops)
            all_violations.extend(t_viols)
            all_warnings.extend(t_warns)
            combined_metrics.update(t_metrics)
            total_checks += t_metrics.get("text_overflow_checks_total", 0)
            passed_checks += (
                t_metrics.get("text_overflow_checks_total", 0)
                - t_metrics.get("text_overflow_warnings", 0)
            )

        # Step 6: Speaker Notes (optional; informational coverage only)
        notes_viols, notes_warns, notes_metrics = self.verify_speaker_notes(
            spec=parsed_spec,
            operations=ops if not parsed_spec else None,
        )
        all_violations.extend(notes_viols)
        all_warnings.extend(notes_warns)
        combined_metrics.update(notes_metrics)  # informational only; not scored

        # Step 7: Live Thumbnail Export
        if presentation_id and thumbnail_dir:
            _, thumb_warns, thumb_metrics = self.verify_live_deck_thumbnails(
                presentation_id=presentation_id,
                output_dir=thumbnail_dir,
            )
            all_warnings.extend(thumb_warns)
            combined_metrics.update(thumb_metrics)

        # Build Per-Slide Summary Reports
        if parsed_spec is not None:
            slides = parsed_spec.all_slides()
            for idx, s in enumerate(slides, start=1):
                slide_viols = [v for v in all_violations if v.get("slide_index") == idx]
                slide_warns = [w for w in all_warnings if w.get("slide_index") == idx]
                slide_contrast = [
                    c for c in all_detailed_checks if c.get("slide_index") == idx
                ]
                min_slide_cr = (
                    min([c["contrast_ratio"] for c in slide_contrast])
                    if slide_contrast
                    else 0.0
                )

                slide_reports.append({
                    "slide_index": idx,
                    "slide_id": s.id or f"SLIDE_{idx:02d}",
                    "archetype": s.archetype,
                    "title": s.title,
                    "subtitle": s.subtitle,
                    "speaker_notes_words": len((s.speaker_notes or "").split()),
                    "contrast_min_cr": min_slide_cr,
                    "contrast_status": "PASS" if not any(v.get("check_type") == "wcag_contrast_aa_failure" for v in slide_viols) else "FAIL",
                    "geometry_status": "PASS" if not any("geometry" in v.get("check_type", "") for v in slide_viols) else "FAIL",
                    "violations_count": len(slide_viols),
                    "warnings_count": len(slide_warns),
                    "is_passing": len(slide_viols) == 0,
                })
            combined_metrics["slide_count"] = len(slides)
        else:
            combined_metrics["slide_count"] = combined_metrics.get("slide_count", 0)

        # Overall Status
        has_errors = any(v.get("severity") == "error" for v in all_violations)
        if self.strict_mode and all_warnings:
            is_passing = False
        else:
            is_passing = not has_errors

        # Guarantee at least 1 check
        if total_checks == 0:
            total_checks = 1
            passed_checks = 1 if is_passing else 0

        return QAReport(
            is_passing=is_passing,
            total_checks=total_checks,
            passed_checks=passed_checks,
            violations=all_violations,
            warnings=all_warnings,
            metrics=combined_metrics,
            detailed_checks=all_detailed_checks,
            slide_reports=slide_reports,
        )

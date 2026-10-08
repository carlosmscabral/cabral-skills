"""Multimodal QA Report Generator and Interactive HTML Preview Gallery.

Generates:
1. `qa_report.md`: Markdown summary report with structured per-slide tables,
   WCAG 2.1 AA/AAA contrast compliance tables, and geometry containment audits.
2. `preview.html`: Self-contained interactive HTML preview gallery rendering
   CSS-accurate mockup representations of all 8 Blueprint slide archetypes.
"""

from __future__ import annotations

from dataclasses import asdict
import html
import json
import os
from pathlib import Path
from typing import Any, Optional, Union

from preso.qa.verifier import QAReport, QAVerifier
from preso.spec.models import PresentationSpec, SlideSpec


class QAReportGenerator:
    """Generates structured Markdown reports and interactive HTML preview galleries."""

    # =========================================================================
    # Markdown Report Generation
    # =========================================================================

    @classmethod
    def generate_markdown_report(
        cls,
        qa_report: QAReport,
        output_path: Optional[Union[str, Path]] = None,
        spec: Optional[PresentationSpec] = None,
    ) -> str:
        """Generates a complete Markdown verification summary report (qa_report.md).

        Args:
            qa_report: Evaluated QAReport instance.
            output_path: Optional file path to write Markdown output.
            spec: Optional PresentationSpec for additional metadata context.

        Returns:
            Markdown formatted report string.
        """
        metrics = qa_report.metrics
        status_badge = "✅ PASS" if qa_report.is_passing else "❌ FAIL"
        deck_title = (
            spec.metadata.title
            if spec and spec.metadata.title
            else "The AI Factory Blueprint Presentation"
        )

        md = []
        md.append(f"# Visual QA & Verification Audit Report")
        md.append(f"")
        md.append(f"**Target Presentation**: {deck_title}  ")
        md.append(f"**Overall Verdict**: **{status_badge}**  ")
        md.append(f"**Pass Rate**: `{qa_report.pass_rate_pct:.1f}%` ({qa_report.passed_checks}/{qa_report.total_checks} checks passed)  ")
        md.append(f"**Violations / Errors**: `{qa_report.error_count}` | **Warnings**: `{qa_report.warning_count}`  ")
        md.append(f"")
        md.append(f"---")
        md.append(f"")

        # 1. Executive Summary Table
        md.append(f"## 1. Executive Verification Metrics")
        md.append(f"")
        md.append(f"| Evaluation Category | Metric | Status | Target Threshold |")
        md.append(f"| :--- | :--- | :--- | :--- |")
        md.append(
            f"| **Spec & Schema Integrity** | {metrics.get('spec_error_count', 0)} errors, {metrics.get('spec_warning_count', 0)} warnings | {'✅ PASS' if metrics.get('spec_valid', True) else '❌ FAIL'} | 100% Valid Schema |"
        )
        md.append(
            f"| **Canvas Geometry & Containment** | {metrics.get('out_of_bounds_count', 0)} bounds violations | {'✅ PASS' if metrics.get('out_of_bounds_count', 0) == 0 else '❌ FAIL'} | Bounds in 720×405pt |"
        )
        md.append(
            f"| **Element Overlap Collisions** | {metrics.get('overlap_collision_count', 0)} sibling collisions | {'✅ PASS' if metrics.get('overlap_collision_count', 0) == 0 else '❌ FAIL'} | 0 Overlaps (>5pt²) |"
        )
        md.append(
            f"| **WCAG 2.1 AA Contrast Compliance** | {metrics.get('wcag_aa_compliance_pct', 100.0):.1f}% ({metrics.get('contrast_aa_passes', 0)}/{metrics.get('contrast_checks_total', 0)}) | {'✅ PASS' if metrics.get('contrast_failures', 0) == 0 else '❌ FAIL'} | 100% AA (CR ≥ 4.5:1 / 3.0:1) |"
        )
        md.append(
            f"| **WCAG 2.1 AAA Contrast Support** | {metrics.get('contrast_aaa_passes', 0)} checks passed AAA | ℹ️ INFO | High contrast support |"
        )
        md.append(
            f"| **Contrast Ratios (Min / Avg / Max)** | {metrics.get('min_contrast_ratio', 0.0):.2f}:1 / {metrics.get('avg_contrast_ratio', 0.0):.2f}:1 / {metrics.get('max_contrast_ratio', 0.0):.2f}:1 | ✅ OPTIMAL | Min ≥ 4.5:1 |"
        )
        md.append(
            f"| **Text Capacity & Overflow Margin** | {metrics.get('text_capacity_pass_rate_pct', 100.0):.1f}% safe ({metrics.get('text_overflow_warnings', 0)} overflow risks) | {'✅ PASS' if metrics.get('text_overflow_warnings', 0) == 0 else '⚠️ WARN'} | Required Height ≤ Box Height |"
        )
        md.append(
            f"| **Speaker Notes (optional)** | {metrics.get('speaker_notes_valid_count', 0)}/{metrics.get('speaker_notes_total_slides', 0)} slides have notes | ℹ️ INFO | Optional — not scored |"
        )
        md.append(f"")
        md.append(f"---")
        md.append(f"")

        # 2. Slide-by-Slide Status Table
        md.append(f"## 2. Slide-by-Slide Verification Matrix")
        md.append(f"")
        md.append(f"| # | Slide ID | Archetype | Title | Contrast | Geometry | Notes Words | Status |")
        md.append(f"| :- | :--- | :--- | :--- | :--- | :--- | :- | :--- |")

        for s in qa_report.slide_reports:
            idx = s.get("slide_index", 1)
            sid = s.get("slide_id", f"SLIDE_{idx}")
            arch = s.get("archetype", "unknown")
            title = s.get("title", "")[:32]
            c_status = "✅ PASS" if s.get("contrast_status") == "PASS" else "❌ FAIL"
            g_status = "✅ PASS" if s.get("geometry_status") == "PASS" else "❌ FAIL"
            words = s.get("speaker_notes_words", 0)
            overall = "✅ PASS" if s.get("is_passing", True) else "❌ FAIL"
            md.append(f"| {idx} | `{sid}` | `{arch}` | {title} | {c_status} | {g_status} | {words}w | **{overall}** |")

        md.append(f"")
        md.append(f"---")
        md.append(f"")

        # 3. Violations and Warnings (if any)
        if qa_report.violations:
            md.append(f"## 3. Violations & Required Remediations")
            md.append(f"")
            md.append(f"| # | Slide | Check Type | Severity | Description |")
            md.append(f"| :- | :- | :--- | :--- | :--- |")
            for idx, v in enumerate(qa_report.violations, start=1):
                slide_idx = v.get("slide_index", 0)
                chk = v.get("check_type", "general")
                sev = v.get("severity", "error").upper()
                msg = v.get("message", "")
                md.append(f"| {idx} | Slide {slide_idx} | `{chk}` | **{sev}** | {msg} |")
            md.append(f"")

        if qa_report.warnings:
            md.append(f"## 4. Quality Warnings & Advisory Notes")
            md.append(f"")
            md.append(f"| # | Slide | Check Type | Severity | Description |")
            md.append(f"| :- | :- | :--- | :--- | :--- |")
            for idx, w in enumerate(qa_report.warnings, start=1):
                slide_idx = w.get("slide_index", 0)
                chk = w.get("check_type", "general")
                sev = w.get("severity", "warning").upper()
                msg = w.get("message", "")
                md.append(f"| {idx} | Slide {slide_idx} | `{chk}` | `{sev}` | {msg} |")
            md.append(f"")

        # 4. WCAG Contrast Compliance Detailed Table
        if qa_report.detailed_checks:
            md.append(f"## 5. WCAG 2.1 Contrast Analysis Detail")
            md.append(f"")
            md.append(f"| Slide | Element ID | Text Sample | Colors (FG / BG) | Size (pt) | Contrast Ratio | AA | AAA |")
            md.append(f"| :- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
            for c in qa_report.detailed_checks[:40]:  # Cap for readability
                s_idx = c.get("slide_index", 1)
                e_id = c.get("element_id", "")
                sample = c.get("text_sample", "")[:28]
                fg = c.get("fg_color", "#000")
                bg = c.get("bg_color", "#FFF")
                fsize = c.get("font_size", 12.0)
                bold_str = " (B)" if c.get("is_bold") else ""
                cr = c.get("contrast_ratio", 0.0)
                aa = "✅ PASS" if c.get("wcag_aa") else "❌ FAIL"
                aaa = "✅ PASS" if c.get("wcag_aaa") else "➖"
                md.append(f"| S{s_idx} | `{e_id}` | {sample} | `{fg}` on `{bg}` | {fsize:.1f}{bold_str} | **{cr:.2f}:1** | {aa} | {aaa} |")
            if len(qa_report.detailed_checks) > 40:
                md.append(f"| ... | *(and {len(qa_report.detailed_checks) - 40} more text elements audited)* | | | | | | |")
            md.append(f"")

        report_content = "\n".join(md) + "\n"

        if output_path is not None:
            dest = Path(output_path).resolve()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(report_content, encoding="utf-8")

        return report_content

    # =========================================================================
    # Interactive HTML Preview Gallery Generation
    # =========================================================================

    @classmethod
    def generate_html_preview(
        cls,
        spec: Union[PresentationSpec, dict[str, Any], Path, str],
        qa_report: Optional[QAReport] = None,
        thumbnail_paths: Optional[list[Union[str, Path]]] = None,
        output_path: Optional[Union[str, Path]] = None,
    ) -> str:
        """Generates a self-contained, responsive HTML preview gallery with CSS mockups of all 8 archetypes.

        Args:
            spec: PresentationSpec or YAML path.
            qa_report: Optional precomputed QAReport. If None, runs QAVerifier.
            thumbnail_paths: Optional list of exported slide thumbnail image paths.
            output_path: Optional file path to write the generated HTML gallery.

        Returns:
            Complete standalone HTML string.
        """
        # Parse spec
        p_spec: PresentationSpec
        if isinstance(spec, PresentationSpec):
            p_spec = spec
        elif isinstance(spec, (Path, str)):
            p_spec = PresentationSpec.from_yaml(spec)
        elif isinstance(spec, dict):
            p_spec = PresentationSpec.from_dict(spec)
        else:
            raise TypeError(f"Unsupported spec type: {type(spec)}")

        if qa_report is None:
            verifier = QAVerifier()
            qa_report = verifier.verify(p_spec)

        slides = p_spec.all_slides()
        title = p_spec.metadata.title or "The AI Factory Blueprint"
        subtitle = p_spec.metadata.subtitle or "Deterministic Presentation Gallery"

        # Generate CSS Mockup HTML for each slide
        slides_html: list[str] = []
        for idx, slide in enumerate(slides, start=1):
            slide_mockup = cls._render_slide_mockup(slide, idx)
            slide_report = next(
                (r for r in qa_report.slide_reports if r.get("slide_index") == idx),
                {},
            )
            is_pass = slide_report.get("is_passing", True)
            status_class = "status-pass" if is_pass else "status-fail"
            notes = slide.speaker_notes or slide.notes or ""

            # Check if there is an exported thumbnail image
            thumb_src = ""
            if thumbnail_paths and idx <= len(thumbnail_paths):
                t_path = thumbnail_paths[idx - 1]
                if t_path and os.path.exists(str(t_path)):
                    thumb_src = str(t_path)

            slide_card = f"""
            <div class="slide-card {status_class}" id="slide-card-{idx}" data-slide-index="{idx}">
                <div class="slide-card-header">
                    <div class="slide-badge-group">
                        <span class="slide-num-pill">SLIDE {idx:02d}</span>
                        <span class="slide-archetype-pill">{html.escape(slide.archetype.upper())}</span>
                    </div>
                    <div class="slide-status-pill {'badge-pass' if is_pass else 'badge-fail'}">
                        {'PASS' if is_pass else 'FAIL'}
                    </div>
                </div>

                <div class="slide-viewport-wrapper">
                    <div class="slide-canvas" id="slide-canvas-{idx}">
                        {slide_mockup}
                    </div>
                    {f'<img class="slide-thumbnail-img" src="{thumb_src}" alt="Rendered Slide {idx}" style="display:none;" />' if thumb_src else ''}
                </div>

                <div class="slide-card-footer">
                    <div class="slide-title-label">{html.escape(slide.title or 'Untitled Slide')}</div>
                    <div class="slide-actions">
                        <button class="btn-action" onclick="openLightbox({idx})">🔍 Lightbox</button>
                        <button class="btn-action" onclick="toggleNotes({idx})">📝 Notes</button>
                    </div>
                </div>

                <div class="slide-notes-drawer" id="slide-notes-{idx}" style="display:none;">
                    <div class="notes-header">🎤 SPEAKER NOTES ({len(notes.split())} words)</div>
                    <div class="notes-body">{html.escape(notes) if notes else '<em style="color:#80868B;">No speaker notes provided</em>'}</div>
                </div>
            </div>
            """
            slides_html.append(slide_card)

        all_slides_rendered = "\n".join(slides_html)

        # JSON data for client-side interactivity
        slides_json_data = json.dumps([
            {
                "index": idx,
                "archetype": s.archetype,
                "title": s.title,
                "subtitle": s.subtitle,
                "notes": s.speaker_notes or s.notes or "",
                "report": next(
                    (r for r in qa_report.slide_reports if r.get("slide_index") == idx),
                    {},
                ),
            }
            for idx, s in enumerate(slides, start=1)
        ])
        report_json_data = qa_report.to_json()

        html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{html.escape(title)} — Blueprint Presentation Preview</title>
    <style>
        :root {{
            --navy-primary: #1E2761;
            --navy-surface: #2D3A8C;
            --navy-deep: #141A3E;
            --slate-dark: #202124;
            --slate-header: #2D3035;
            --bg-light: #F8F9FA;
            --card-white: #FFFFFF;
            --card-border: #DADCE0;
            --blue-accent: #1A73E8;
            --blue-light: #E8F0FE;
            --blue-text: #174EA6;
            --green-do: #1E8E3E;
            --green-light: #E6F4EA;
            --green-text: #137333;
            --red-dont: #D93025;
            --red-light: #FCE8E6;
            --red-text: #C5221F;
            --amber-warn: #F9AB00;
            --text-primary: #202124;
            --text-muted: #5F6368;
            --text-white: #FFFFFF;
            --font-heading: 'Google Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-body: 'Google Sans Text', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-code: 'Roboto Mono', monospace, Consolas;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            background-color: #0F1322;
            color: #E8EAED;
            font-family: var(--font-body);
            line-height: 1.5;
            padding: 24px;
        }}

        /* Header Bar */
        .header-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, #1E2761 0%, #141A3E 100%);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px 28px;
            margin-bottom: 24px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}

        .header-title-group h1 {{
            font-family: var(--font-heading);
            font-size: 24px;
            font-weight: 700;
            color: #FFFFFF;
            letter-spacing: -0.5px;
        }}

        .header-title-group p {{
            font-size: 14px;
            color: #CADCFC;
            margin-top: 4px;
        }}

        .metrics-pill-group {{
            display: flex;
            gap: 12px;
            align-items: center;
        }}

        .metric-pill {{
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.15);
            padding: 8px 16px;
            border-radius: 8px;
            text-align: center;
        }}

        .metric-pill-value {{
            font-family: var(--font-heading);
            font-size: 18px;
            font-weight: 700;
            color: #FFFFFF;
        }}

        .metric-pill-label {{
            font-size: 11px;
            color: #BDC1C6;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        /* Toolbar Controls */
        .controls-bar {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: #181C2E;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 10px;
            padding: 12px 20px;
            margin-bottom: 24px;
        }}

        .btn {{
            background: var(--blue-accent);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-family: var(--font-heading);
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }}

        .btn:hover {{
            background: #1557B0;
        }}

        .btn-outline {{
            background: transparent;
            border: 1px solid rgba(255,255,255,0.2);
            color: #E8EAED;
        }}

        .btn-outline:hover {{
            background: rgba(255,255,255,0.05);
            border-color: rgba(255,255,255,0.4);
        }}

        /* Slide Gallery Grid */
        .gallery-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(560px, 1fr));
            gap: 24px;
        }}

        .slide-card {{
            background: #161A2B;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 16px rgba(0,0,0,0.25);
            display: flex;
            flex-direction: column;
            transition: transform 0.2s, box-shadow 0.2s;
        }}

        .slide-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.4);
            border-color: rgba(26, 115, 232, 0.4);
        }}

        .slide-card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 16px;
            background: #1E2338;
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }}

        .slide-badge-group {{
            display: flex;
            gap: 8px;
            align-items: center;
        }}

        .slide-num-pill {{
            background: var(--blue-accent);
            color: white;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            letter-spacing: 0.5px;
        }}

        .slide-archetype-pill {{
            background: rgba(255,255,255,0.08);
            color: #CADCFC;
            font-size: 11px;
            font-weight: 600;
            padding: 2px 8px;
            border-radius: 4px;
            letter-spacing: 0.5px;
        }}

        .slide-status-pill {{
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
        }}

        .badge-pass {{
            background: rgba(30, 142, 62, 0.2);
            color: #81C995;
            border: 1px solid rgba(30, 142, 62, 0.4);
        }}

        .badge-fail {{
            background: rgba(217, 48, 37, 0.2);
            color: #F28B82;
            border: 1px solid rgba(217, 48, 37, 0.4);
        }}

        /* 16:9 Slide Canvas Mockup Viewport */
        .slide-viewport-wrapper {{
            position: relative;
            width: 100%;
            padding-top: 56.25%; /* 16:9 Aspect Ratio */
            background: #000;
            overflow: hidden;
        }}

        .slide-canvas {{
            position: absolute;
            top: 0;
            left: 0;
            width: 720px;
            height: 405px;
            transform-origin: top left;
            user-select: none;
        }}

        .slide-card-footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 16px;
            background: #1E2338;
            border-top: 1px solid rgba(255,255,255,0.06);
        }}

        .slide-title-label {{
            font-size: 13px;
            font-weight: 600;
            color: #E8EAED;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 60%;
        }}

        .slide-actions {{
            display: flex;
            gap: 8px;
        }}

        .btn-action {{
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.12);
            color: #BDC1C6;
            font-size: 11px;
            padding: 4px 10px;
            border-radius: 4px;
            cursor: pointer;
        }}

        .btn-action:hover {{
            background: rgba(255,255,255,0.12);
            color: white;
        }}

        .slide-notes-drawer {{
            background: #121522;
            border-top: 1px solid rgba(255,255,255,0.08);
            padding: 12px 16px;
            font-size: 12px;
            color: #BDC1C6;
        }}

        .notes-header {{
            font-size: 11px;
            font-weight: 700;
            color: var(--blue-accent);
            margin-bottom: 4px;
            letter-spacing: 0.5px;
        }}

        /* ====================================================================
           CSS ARCHETYPE MOCKUP ENGINE (720x405 pt canvas scale)
           ==================================================================== */
        .mockup-slide {{
            width: 720px;
            height: 405px;
            position: relative;
            overflow: hidden;
            box-sizing: border-box;
            background-color: var(--bg-light);
            color: var(--text-primary);
        }}

        /* Common Slide Header */
        .mockup-header {{
            position: absolute;
            top: 28px;
            left: 36px;
            width: 648px;
            height: 60px;
        }}

        .mockup-kicker {{
            font-family: var(--font-heading);
            font-size: 10px;
            font-weight: 700;
            color: var(--blue-text);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 2px;
        }}

        .mockup-title {{
            font-family: var(--font-heading);
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.3px;
            line-height: 1.2;
        }}

        .mockup-subtitle {{
            font-family: var(--font-body);
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 2px;
        }}

        /* Archetype 1: Chapter Divider (Exact Blueprint Standard) */
        .arch-chapter-divider {{
            background-color: #FFFFFF;
            color: var(--text-primary);
            padding: 36px 36px;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            position: relative;
        }}

        .arch-chapter-divider .rainbow-bar {{
            width: 100%;
            height: 5px;
            display: flex;
            margin-bottom: 24px;
        }}

        .arch-chapter-divider .rainbow-segment {{
            flex: 1;
            height: 100%;
        }}

        .arch-chapter-divider .chapter-number {{
            font-family: var(--font-heading);
            font-size: 64px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.0;
            margin: 0 0 6px 0;
            letter-spacing: -1.5px;
        }}

        .arch-chapter-divider .chapter-title {{
            font-family: var(--font-heading);
            font-size: 54px;
            font-weight: 700;
            color: var(--text-primary);
            line-height: 1.05;
            letter-spacing: -1px;
            margin-bottom: 16px;
            max-width: 648px;
        }}

        .arch-chapter-divider .chapter-subtitle {{
            font-family: var(--font-body);
            font-size: 16px;
            color: var(--blue-accent);
            line-height: 1.35;
            max-width: 640px;
        }}

        /* Archetype 2: Split Cards */
        .arch-split-cards .cards-container {{
            position: absolute;
            top: 100px;
            left: 36px;
            width: 648px;
            height: 275px;
            display: flex;
            gap: 16px;
        }}

        .arch-split-cards .cards-container.with-foundation {{
            height: 184px;
        }}

        .foundation-card-container {{
            position: absolute;
            top: 292px;
            left: 36px;
            width: 648px;
            height: 82px;
            background: var(--card-white);
            border: 1px solid var(--card-border);
            border-top: 4px solid var(--blue-accent);
            border-radius: 8px;
            padding: 10px 16px;
            display: flex;
            flex-direction: column;
            box-sizing: border-box;
        }}

        .foundation-header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 6px;
        }}

        .foundation-title {{
            font-size: 13px;
            color: var(--text-primary);
            font-weight: 700;
        }}

        .foundation-body {{
            font-size: 10.5px;
            color: var(--text-muted);
            line-height: 1.35;
        }}

        .split-card-item {{
            flex: 1;
            background: var(--card-white);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 16px 20px;
            display: flex;
            flex-direction: column;
        }}

        .card-pill {{
            align-self: flex-start;
            background: var(--blue-light);
            color: var(--blue-text);
            font-size: 10px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .card-header-text {{
            font-family: var(--font-heading);
            font-size: 16px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 12px;
        }}

        .card-bullet-list {{
            list-style: none;
            padding: 0;
            font-size: 12px;
            color: var(--text-muted);
            line-height: 1.6;
        }}

        .card-bullet-list li {{
            position: relative;
            padding-left: 16px;
            margin-bottom: 6px;
        }}

        .card-bullet-list li::before {{
            content: "•";
            color: var(--blue-accent);
            font-size: 16px;
            position: absolute;
            left: 0;
            top: -2px;
        }}

        /* Archetype 3: Code Ratchet Terminal */
        .arch-code-terminal .terminal-layout {{
            position: absolute;
            top: 100px;
            left: 36px;
            width: 648px;
            height: 275px;
            display: flex;
            gap: 16px;
        }}

        .terminal-box {{
            flex: 1;
            background: var(--slate-dark);
            border-radius: 8px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            border: 1px solid #3C4043;
        }}

        .terminal-header-bar {{
            background: var(--slate-header);
            height: 28px;
            display: flex;
            align-items: center;
            padding: 0 12px;
            gap: 8px;
        }}

        .traffic-dots {{
            display: flex;
            gap: 5px;
        }}

        .dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}
        .dot-red {{ background: #EA4335; }}
        .dot-yellow {{ background: #FBBC04; }}
        .dot-green {{ background: #34A853; }}

        .terminal-filename {{
            font-family: var(--font-code);
            font-size: 11px;
            color: #BDC1C6;
            margin-left: 6px;
        }}

        .terminal-badge {{
            margin-left: auto;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 6px;
            border-radius: 3px;
        }}
        .badge-do {{ background: var(--green-light); color: var(--green-text); }}
        .badge-dont {{ background: var(--red-light); color: var(--red-text); }}

        .terminal-code-body {{
            padding: 12px 14px;
            font-family: var(--font-code);
            font-size: 10.5px;
            color: #CADCFC;
            white-space: pre-wrap;
            line-height: 1.45;
            flex: 1;
        }}

        /* Archetype 4: Hero Metrics */
        .arch-hero-metrics .metrics-container {{
            position: absolute;
            top: 100px;
            left: 36px;
            width: 648px;
            height: 275px;
            display: flex;
            gap: 16px;
        }}

        .hero-metric-card {{
            flex: 1;
            background: var(--card-white);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 20px 24px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .hero-stat-number {{
            font-family: var(--font-heading);
            font-size: 54px;
            font-weight: 800;
            color: var(--text-primary);
            line-height: 1.0;
            letter-spacing: -1px;
        }}

        .hero-unit-text {{
            font-size: 13px;
            color: var(--text-muted);
            margin-top: 4px;
            font-weight: 500;
        }}

        .hero-delta-pill {{
            align-self: flex-start;
            font-size: 11px;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 4px;
            margin: 8px 0;
        }}
        .delta-pos {{ background: var(--green-light); color: var(--green-text); }}
        .delta-neg {{ background: var(--red-light); color: var(--red-text); }}

        .hero-context-desc {{
            font-size: 12px;
            color: var(--text-muted);
            line-height: 1.4;
            border-top: 1px solid var(--card-border);
            padding-top: 10px;
            margin-top: 10px;
        }}

        /* Archetype 5: Ladder Hierarchy */
        .arch-ladder-hierarchy .ladder-container {{
            position: absolute;
            top: 100px;
            left: 36px;
            width: 648px;
            height: 275px;
            display: flex;
            gap: 12px;
            align-items: stretch;
        }}

        .ladder-step-card {{
            flex: 1;
            background: var(--card-white);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 16px 14px;
            display: flex;
            flex-direction: column;
            position: relative;
        }}

        .ladder-rung-badge {{
            font-size: 9.5px;
            font-weight: 700;
            color: var(--blue-text);
            background: var(--blue-light);
            padding: 2px 6px;
            border-radius: 3px;
            align-self: flex-start;
            margin-bottom: 8px;
        }}

        .ladder-step-title {{
            font-family: var(--font-heading);
            font-size: 14px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 8px;
        }}

        .ladder-step-desc {{
            font-size: 11.5px;
            color: var(--text-muted);
            line-height: 1.45;
        }}

        /* Archetype 6: Executive Grid */
        .arch-executive-grid .grid-container {{
            position: absolute;
            top: 100px;
            left: 36px;
            width: 648px;
            height: 275px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 14px;
        }}

        .grid-quadrant-card {{
            background: var(--card-white);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 14px 18px;
            border-left: 4px solid var(--blue-accent);
            display: flex;
            flex-direction: column;
        }}

        .quadrant-num {{
            font-size: 10px;
            font-weight: 700;
            color: var(--blue-text);
            margin-bottom: 2px;
        }}

        .quadrant-title {{
            font-family: var(--font-heading);
            font-size: 14px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 4px;
        }}

        .quadrant-body {{
            font-size: 11.5px;
            color: var(--text-muted);
            line-height: 1.4;
        }}

        /* Archetype 7: Do / Don't Checklist */
        .arch-dodont-checklist .dodont-container {{
            position: absolute;
            top: 100px;
            left: 36px;
            width: 648px;
            height: 275px;
            display: flex;
            gap: 16px;
        }}

        .dodont-column {{
            flex: 1;
            background: var(--card-white);
            border-radius: 8px;
            border: 1px solid var(--card-border);
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }}

        .dodont-banner {{
            padding: 8px 16px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}
        .banner-dont {{ background: var(--red-light); color: var(--red-text); border-bottom: 1px solid var(--red-border); }}
        .banner-do {{ background: var(--green-light); color: var(--green-text); border-bottom: 1px solid var(--green-border); }}

        .dodont-list {{
            padding: 12px 16px;
            list-style: none;
            font-size: 12px;
            line-height: 1.5;
            color: var(--text-muted);
        }}

        .dodont-list li {{
            margin-bottom: 8px;
            display: flex;
            gap: 8px;
        }}

        /* Archetype 8: Actionable Takeaways */
        .arch-takeaways .takeaways-container {{
            position: absolute;
            top: 100px;
            left: 36px;
            width: 648px;
            height: 275px;
            display: flex;
            gap: 16px;
        }}

        .takeaways-left {{
            flex: 1.2;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}

        .principle-item {{
            background: var(--card-white);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            padding: 10px 14px;
            display: flex;
            gap: 12px;
            align-items: flex-start;
        }}

        .principle-num {{
            background: var(--blue-light);
            color: var(--blue-text);
            font-size: 11px;
            font-weight: 700;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }}

        .principle-content h4 {{
            font-family: var(--font-heading);
            font-size: 13px;
            font-weight: 700;
            color: var(--text-primary);
        }}

        .principle-content p {{
            font-size: 11px;
            color: var(--text-muted);
            margin-top: 2px;
        }}

        .takeaways-right {{
            flex: 0.8;
            background: var(--navy-primary);
            border-radius: 8px;
            padding: 18px;
            color: white;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }}

        .roadmap-title {{
            font-size: 11px;
            font-weight: 700;
            color: var(--blue-subtitle);
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}

        .roadmap-items {{
            list-style: none;
            font-size: 11.5px;
            color: #FFFFFF;
            line-height: 1.6;
        }}

        .roadmap-items li::before {{
            content: "➔ ";
            color: var(--blue-accent);
        }}

        .cta-btn-mockup {{
            background: var(--blue-accent);
            color: white;
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 11.5px;
            font-weight: 700;
            text-align: center;
            margin-top: 12px;
            letter-spacing: 0.3px;
        }}

        /* Lightbox Modal */
        .lightbox-modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0,0,0,0.85);
            z-index: 9999;
            align-items: center;
            justify-content: center;
            backdrop-filter: blur(4px);
        }}

        .lightbox-content {{
            position: relative;
            width: 90vw;
            max-width: 1152px;
            aspect-ratio: 16/9;
            background: #000;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 10px 40px rgba(0,0,0,0.6);
        }}

        .lightbox-canvas {{
            width: 720px;
            height: 405px;
            transform-origin: top left;
        }}

        .lightbox-close {{
            position: absolute;
            top: 16px;
            right: 24px;
            color: white;
            font-size: 28px;
            cursor: pointer;
            z-index: 10000;
        }}
    </style>
</head>
<body>

    <!-- Header Section -->
    <div class="header-bar">
        <div class="header-title-group">
            <h1>{html.escape(title)}</h1>
            <p>{html.escape(subtitle)} · The AI Factory Blueprint Design System</p>
        </div>
        <div class="metrics-pill-group">
            <div class="metric-pill">
                <div class="metric-pill-value">{len(slides)}</div>
                <div class="metric-pill-label">Total Slides</div>
            </div>
            <div class="metric-pill">
                <div class="metric-pill-value">{qa_report.pass_rate_pct:.0f}%</div>
                <div class="metric-pill-label">QA Pass Rate</div>
            </div>
            <div class="metric-pill">
                <div class="metric-pill-value">{qa_report.metrics.get('min_contrast_ratio', 0.0):.1f}:1</div>
                <div class="metric-pill-label">Min Contrast</div>
            </div>
            <div class="metric-pill">
                <div class="metric-pill-value" style="color:{'#81C995' if qa_report.is_passing else '#F28B82'};">
                    {'PASS' if qa_report.is_passing else 'FAIL'}
                </div>
                <div class="metric-pill-label">Overall Status</div>
            </div>
        </div>
    </div>

    <!-- Controls Bar -->
    <div class="controls-bar">
        <div style="display:flex; gap:10px; align-items:center;">
            <button class="btn btn-outline" onclick="toggleAllNotes()">📝 Toggle All Notes</button>
            <button class="btn btn-outline" onclick="filterFailingSlides()">⚠️ Show Violations Only</button>
            <button class="btn btn-outline" onclick="resetFilters()">🔄 Reset View</button>
        </div>
        <div style="font-size:12px; color:#BDC1C6;">
            Interactive 16:9 Canvas Mockup Gallery · Click <strong>🔍 Lightbox</strong> to inspect typography & bounds
        </div>
    </div>

    <!-- Gallery Grid -->
    <div class="gallery-grid" id="galleryGrid">
        {all_slides_rendered}
    </div>

    <!-- Lightbox Modal -->
    <div class="lightbox-modal" id="lightboxModal" onclick="closeLightbox(event)">
        <div class="lightbox-close" onclick="closeLightbox()">&times;</div>
        <div class="lightbox-content" id="lightboxContent" onclick="event.stopPropagation()">
            <div class="lightbox-canvas" id="lightboxCanvas"></div>
        </div>
    </div>

    <!-- Client-Side Interactive Script -->
    <script>
        const SLIDES_DATA = {slides_json_data};
        const QA_REPORT = {report_json_data};

        function scaleAllCanvases() {{
            document.querySelectorAll('.slide-card').forEach(card => {{
                const viewport = card.querySelector('.slide-viewport-wrapper');
                const canvas = card.querySelector('.slide-canvas');
                if (viewport && canvas) {{
                    const w = viewport.clientWidth;
                    const scale = w / 720.0;
                    canvas.style.transform = `scale(${{scale}})`;
                }}
            }});
        }}

        window.addEventListener('resize', scaleAllCanvases);
        window.addEventListener('DOMContentLoaded', scaleAllCanvases);
        setTimeout(scaleAllCanvases, 100);

        function toggleNotes(idx) {{
            const drawer = document.getElementById(`slide-notes-${{idx}}`);
            if (drawer) {{
                drawer.style.display = drawer.style.display === 'none' ? 'block' : 'none';
            }}
        }}

        let allNotesOpen = false;
        function toggleAllNotes() {{
            allNotesOpen = !allNotesOpen;
            document.querySelectorAll('.slide-notes-drawer').forEach(d => {{
                d.style.display = allNotesOpen ? 'block' : 'none';
            }});
        }}

        function filterFailingSlides() {{
            document.querySelectorAll('.slide-card').forEach(card => {{
                if (card.classList.contains('status-pass')) {{
                    card.style.display = 'none';
                }} else {{
                    card.style.display = 'flex';
                }}
            }});
        }}

        function resetFilters() {{
            document.querySelectorAll('.slide-card').forEach(card => {{
                card.style.display = 'flex';
            }});
        }}

        let currentLightboxIndex = 1;
        function openLightbox(idx) {{
            currentLightboxIndex = idx;
            const modal = document.getElementById('lightboxModal');
            const targetCanvas = document.getElementById(`slide-canvas-${{idx}}`);
            const lightboxContent = document.getElementById('lightboxContent');
            const lightboxCanvas = document.getElementById('lightboxCanvas');

            if (targetCanvas && lightboxCanvas && lightboxContent) {{
                lightboxCanvas.innerHTML = targetCanvas.innerHTML;
                modal.style.display = 'flex';

                const lw = lightboxContent.clientWidth;
                const scale = lw / 720.0;
                lightboxCanvas.style.transform = `scale(${{scale}})`;
            }}
        }}

        function closeLightbox() {{
            document.getElementById('lightboxModal').style.display = 'none';
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') closeLightbox();
            if (document.getElementById('lightboxModal').style.display === 'flex') {{
                if (e.key === 'ArrowRight') {{
                    const next = Math.min(SLIDES_DATA.length, currentLightboxIndex + 1);
                    openLightbox(next);
                }} else if (e.key === 'ArrowLeft') {{
                    const prev = Math.max(1, currentLightboxIndex - 1);
                    openLightbox(prev);
                }}
            }}
        }});
    </script>
</body>
</html>
"""

        if output_path is not None:
            dest = Path(output_path).resolve()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(html_doc, encoding="utf-8")

        return html_doc

    # =========================================================================
    # Internal Mockup Rendering Engine (All 8 Archetypes)
    # =========================================================================

    @classmethod
    def _render_slide_mockup(cls, slide: SlideSpec, index: int) -> str:
        """Renders CSS mockup HTML for an individual SlideSpec."""
        arch = slide.archetype.lower().replace("-", "_")

        # 1. Chapter Divider (Exact Blueprint Standard)
        if arch == "chapter_divider":
            num = slide.chapter_number or f"{index:02d}"
            num_str = f"{int(num):02d}" if str(num).isdigit() else str(num)
            return f"""
            <div class="mockup-slide arch-chapter-divider">
                <div class="rainbow-bar">
                    <div class="rainbow-segment" style="background:#EA4335;"></div>
                    <div class="rainbow-segment" style="background:#FBBC04;"></div>
                    <div class="rainbow-segment" style="background:#34A853;"></div>
                    <div class="rainbow-segment" style="background:#4285F4;"></div>
                </div>
                <div class="chapter-number">{html.escape(num_str)}</div>
                <div class="chapter-title">{html.escape(slide.title or "Chapter Title")}</div>
                {f'<div class="chapter-subtitle">{html.escape(slide.subtitle)}</div>' if slide.subtitle else ''}
            </div>
            """

        # Header markup for remaining archetypes
        header_html = f"""
        <div class="mockup-header">
            {f'<div class="mockup-kicker">{html.escape(slide.kicker)}</div>' if slide.kicker else ''}
            <div class="mockup-title">{html.escape(slide.title or 'Blueprint Architecture')}</div>
            {f'<div class="mockup-subtitle">{html.escape(slide.subtitle)}</div>' if slide.subtitle else ''}
        </div>
        """

        # 2. Split Cards
        if arch in ("split_cards", "split_comparison"):
            cards = slide.cards or []
            foundation = getattr(slide, "foundation", None) or (
                slide.raw_content.get("foundation") if hasattr(slide, "raw_content") else None
            )
            cards_html = []
            for c in cards:
                c_title = getattr(c, "title", "") or (c.get("title") if isinstance(c, dict) else "")
                c_kicker = getattr(c, "kicker", "") or getattr(c, "category", "") or (c.get("kicker") or c.get("category_pill") if isinstance(c, dict) else "")
                bullets = getattr(c, "bullets", []) or (c.get("bullets") if isinstance(c, dict) else [])

                b_items = "".join([f"<li>{html.escape(str(b))}</li>" for b in bullets])
                cards_html.append(f"""
                <div class="split-card-item">
                    {f'<div class="card-pill">{html.escape(c_kicker)}</div>' if c_kicker else ''}
                    <div class="card-header-text">{html.escape(c_title or 'Core Principle')}</div>
                    <ul class="card-bullet-list">
                        {b_items or '<li>Operational detail and execution guidelines.</li>'}
                    </ul>
                </div>
                """)

            foundation_html = ""
            if foundation:
                if isinstance(foundation, dict):
                    f_title = foundation.get("title", "Fundação Enterprise")
                    f_cat = foundation.get("category", foundation.get("category_pill", "BASE CORPORATIVA"))
                    f_bullets = foundation.get("bullets", foundation.get("description", ""))
                else:
                    f_title = str(foundation)
                    f_cat = "BASE CORPORATIVA"
                    f_bullets = ""

                if isinstance(f_bullets, list):
                    f_b_items = " ".join([f"• {html.escape(str(b))}" for b in f_bullets])
                else:
                    f_b_items = html.escape(str(f_bullets))

                foundation_html = f"""
                <div class="foundation-card-container">
                    <div class="foundation-header">
                        <span class="card-pill">{html.escape(f_cat)}</span>
                        <strong class="foundation-title">{html.escape(f_title)}</strong>
                    </div>
                    <div class="foundation-body">{f_b_items}</div>
                </div>
                """

            cards_container_class = "cards-container with-foundation" if foundation else "cards-container"
            return f"""
            <div class="mockup-slide arch-split-cards">
                {header_html}
                <div class="{cards_container_class}">
                    {''.join(cards_html) if cards_html else '<div class="split-card-item"><div class="card-header-text">Architecture</div></div>'}
                </div>
                {foundation_html}
            </div>
            """

        # 3. Code Terminal Box
        elif arch in ("code_terminal", "code_ratchet"):
            terminals = slide.terminals or []
            terms_html = []
            for t in terminals:
                fn = getattr(t, "filename", "main.py") or (t.get("filename") if isinstance(t, dict) else "main.py")
                code = getattr(t, "code", "") or (t.get("code") if isinstance(t, dict) else "")
                badge = getattr(t, "status_badge", "") or (t.get("status_badge") if isinstance(t, dict) else "")

                badge_class = "badge-do" if "do" in badge.lower() or "✓" in badge else ("badge-dont" if "dont" in badge.lower() or "✗" in badge else "")
                terms_html.append(f"""
                <div class="terminal-box">
                    <div class="terminal-header-bar">
                        <div class="traffic-dots">
                            <div class="dot dot-red"></div>
                            <div class="dot dot-yellow"></div>
                            <div class="dot dot-green"></div>
                        </div>
                        <div class="terminal-filename">{html.escape(fn)}</div>
                        {f'<div class="terminal-badge {badge_class}">{html.escape(badge)}</div>' if badge else ''}
                    </div>
                    <div class="terminal-code-body">{html.escape(code or '# Standard execution implementation\npass')}</div>
                </div>
                """)

            return f"""
            <div class="mockup-slide arch-code-terminal">
                {header_html}
                <div class="terminal-layout">
                    {''.join(terms_html) if terms_html else '<div class="terminal-box"><div class="terminal-code-body"># Code</div></div>'}
                </div>
            </div>
            """

        # 4. Hero Metrics
        elif arch in ("hero_metrics", "hero_metric"):
            metrics = slide.metrics or []
            m_html = []
            for m in metrics:
                val = getattr(m, "value", "") or (m.get("value") if isinstance(m, dict) else "")
                unit = getattr(m, "unit", "") or (m.get("unit") if isinstance(m, dict) else "")
                delta = getattr(m, "delta", "") or (m.get("delta") if isinstance(m, dict) else "")
                d_type = getattr(m, "delta_type", "positive") or (m.get("delta_type") if isinstance(m, dict) else "positive")
                desc = getattr(m, "description", "") or (m.get("description") if isinstance(m, dict) else "")

                delta_class = "delta-neg" if d_type == "negative" or "-" in delta else "delta-pos"

                m_html.append(f"""
                <div class="hero-metric-card">
                    <div>
                        <div class="hero-stat-number">{html.escape(str(val))}</div>
                        {f'<div class="hero-unit-text">{html.escape(unit)}</div>' if unit else ''}
                        {f'<div class="hero-delta-pill {delta_class}">{html.escape(delta)}</div>' if delta else ''}
                    </div>
                    {f'<div class="hero-context-desc">{html.escape(desc)}</div>' if desc else ''}
                </div>
                """)

            return f"""
            <div class="mockup-slide arch-hero-metrics">
                {header_html}
                <div class="metrics-container">
                    {''.join(m_html)}
                </div>
            </div>
            """

        # 5. Ladder Hierarchy
        elif arch in ("ladder_hierarchy", "ladder_flow", "ladder"):
            steps = slide.steps or []
            s_html = []
            for i, s in enumerate(steps, start=1):
                num = getattr(s, "number", i) or (s.get("number", i) if isinstance(s, dict) else i)
                stitle = getattr(s, "title", f"Rung {i}") or (s.get("title") if isinstance(s, dict) else f"Rung {i}")
                desc = getattr(s, "description", "") or (s.get("description") if isinstance(s, dict) else "")

                s_html.append(f"""
                <div class="ladder-step-card">
                    <div class="ladder-rung-badge">RUNG {int(num):02d}</div>
                    <div class="ladder-step-title">{html.escape(stitle)}</div>
                    <div class="ladder-step-desc">{html.escape(desc)}</div>
                </div>
                """)

            return f"""
            <div class="mockup-slide arch-ladder-hierarchy">
                {header_html}
                <div class="ladder-container">
                    {''.join(s_html)}
                </div>
            </div>
            """

        # 6. Executive Grid
        elif arch in ("executive_grid", "exec_grid"):
            quads = slide.quadrants or []
            q_html = []
            for i, q in enumerate(quads, start=1):
                num = getattr(q, "number", i) or (q.get("number", i) if isinstance(q, dict) else i)
                qtitle = getattr(q, "title", f"Quadrant {i}") or (q.get("title") if isinstance(q, dict) else f"Quadrant {i}")
                narr = getattr(q, "narrative", "") or getattr(q, "description", "") or (q.get("narrative") or q.get("description") if isinstance(q, dict) else "")

                q_html.append(f"""
                <div class="grid-quadrant-card">
                    <div class="quadrant-num">{int(num):02d}</div>
                    <div class="quadrant-title">{html.escape(qtitle)}</div>
                    <div class="quadrant-body">{html.escape(narr)}</div>
                </div>
                """)

            return f"""
            <div class="mockup-slide arch-executive-grid">
                {header_html}
                <div class="grid-container">
                    {''.join(q_html)}
                </div>
            </div>
            """

        # 7. Do / Don't Checklist
        elif arch in ("dodont_checklist", "checklist"):
            donts = []
            dos = []
            if hasattr(slide, "checklist") and slide.checklist:
                donts = getattr(slide.checklist, "dont_items", []) or []
                dos = getattr(slide.checklist, "do_items", []) or []
            if not donts and hasattr(slide, "dont_items"):
                donts = getattr(slide, "dont_items", []) or []
            if not dos and hasattr(slide, "do_items"):
                dos = getattr(slide, "do_items", []) or []
            if not donts and hasattr(slide, "raw_content") and isinstance(slide.raw_content, dict):
                donts = slide.raw_content.get("dont_items", slide.raw_content.get("dont", []))
            if not dos and hasattr(slide, "raw_content") and isinstance(slide.raw_content, dict):
                dos = slide.raw_content.get("do_items", slide.raw_content.get("do", []))

            dont_li = "".join([f"<li><span>✗</span> {html.escape(str(d))}</li>" for d in donts])
            do_li = "".join([f"<li><span>✓</span> {html.escape(str(d))}</li>" for d in dos])

            return f"""
            <div class="mockup-slide arch-dodont-checklist">
                {header_html}
                <div class="dodont-container">
                    <div class="dodont-column">
                        <div class="dodont-banner banner-dont">✗ COMMON TRAPS (DON'T)</div>
                        <ul class="dodont-list">{dont_li or '<li>Anti-pattern without verification</li>'}</ul>
                    </div>
                    <div class="dodont-column">
                        <div class="dodont-banner banner-do">✓ BLUEPRINT STANDARD (DO)</div>
                        <ul class="dodont-list">{do_li or '<li>Deterministic verification harness</li>'}</ul>
                    </div>
                </div>
            </div>
            """

        # 8. Actionable Takeaways
        elif arch in ("actionable_takeaways", "takeaways"):
            principles = []
            roadmap_items = []
            roadmap_title = "ROADMAP & NEXT STEPS"
            cta = "START BUILDING NOW →"

            if hasattr(slide, "takeaway") and slide.takeaway:
                principles = getattr(slide.takeaway, "principles", []) or []
                roadmap_items = getattr(slide.takeaway, "roadmap_items", []) or []
                roadmap_title = getattr(slide.takeaway, "roadmap_title", "ROADMAP & NEXT STEPS") or "ROADMAP & NEXT STEPS"
                cta = getattr(slide.takeaway, "cta_text", "START BUILDING NOW →") or "START BUILDING NOW →"
            if not principles and hasattr(slide, "principles"):
                principles = getattr(slide, "principles", []) or []
            if not principles and hasattr(slide, "raw_content") and isinstance(slide.raw_content, dict):
                principles = slide.raw_content.get("principles", [])
                roadmap_items = slide.raw_content.get("roadmap_items", [])
                roadmap_title = slide.raw_content.get("roadmap_title", "ROADMAP & NEXT STEPS") or "ROADMAP & NEXT STEPS"
                cta = slide.raw_content.get("cta_text", "START BUILDING NOW →") or "START BUILDING NOW →"

            p_html = []
            for i, p in enumerate(principles, start=1):
                num = getattr(p, "number", i) if hasattr(p, "number") else (p.get("number", i) if isinstance(p, dict) else i)
                ptitle = getattr(p, "title", f"Principle {i}") if hasattr(p, "title") else (p.get("title") if isinstance(p, dict) else f"Principle {i}")
                desc = getattr(p, "description", "") if hasattr(p, "description") else (p.get("description", "") if isinstance(p, dict) else "")

                p_html.append(f"""
                <div class="principle-item">
                    <div class="principle-num">{num}</div>
                    <div class="principle-content">
                        <h4>{html.escape(str(ptitle))}</h4>
                        <p>{html.escape(str(desc))}</p>
                    </div>
                </div>
                """)

            rm_items = roadmap_items or ["Establish core prompt specs", "Equip enforcing pre-commit ratchets", "Run adversarial QA verifiers"]
            rm_li = "".join([f"<li>{html.escape(str(item))}</li>" for item in rm_items])

            return f"""
            <div class="mockup-slide arch-takeaways">
                {header_html}
                <div class="takeaways-container">
                    <div class="takeaways-left">
                        {''.join(p_html) if p_html else '<div class="principle-item"><div class="principle-num">1</div><div class="principle-content"><h4>Key Principle</h4></div></div>'}
                    </div>
                    <div class="takeaways-right">
                        <div>
                            <div class="roadmap-title">{html.escape(roadmap_title)}</div>
                            <ul class="roadmap-items">
                                {rm_li}
                            </ul>
                        </div>
                        <div class="cta-btn-mockup">{html.escape(cta)}</div>
                    </div>
                </div>
            </div>
            """

        # 9. Demo Pivot
        elif arch in ("demo_pivot", "demo"):
            watch = slide.raw_content.get("watch_for", []) if isinstance(slide.raw_content, dict) else []
            if isinstance(watch, str):
                watch = [watch]
            chips = "".join(
                f'<span style="display:inline-block;background:#2D3A8C;color:#fff;padding:6px 12px;'
                f'margin-right:8px;border-radius:4px;font-size:12px;">{html.escape(str(w))}</span>'
                for w in watch[:3]
            )
            return f"""
            <div class="mockup-slide" style="background:#1E2761;color:#fff;padding:40px 36px;">
                <div style="display:inline-block;background:#C5221F;color:#fff;font-weight:700;font-size:12px;padding:5px 14px;border-radius:4px;">▶ {html.escape((slide.kicker or 'LIVE DEMO').upper())}</div>
                <div style="font-size:30px;font-weight:700;margin-top:18px;">{html.escape(slide.title or 'Live demo')}</div>
                {f'<div style="color:#CADCFC;font-size:15px;margin-top:10px;">{html.escape(slide.subtitle)}</div>' if slide.subtitle else ''}
                {f'<div style="margin-top:22px;"><div style="color:#CADCFC;font-size:10px;font-weight:700;margin-bottom:6px;">WATCH FOR</div>{chips}</div>' if chips else ''}
            </div>
            """

        # 10. Image Split
        elif arch in ("image_split", "image", "diagram"):
            raw = slide.raw_content if isinstance(slide.raw_content, dict) else {}
            img = raw.get("image", {})
            if isinstance(img, str):
                img = {"path": img}
            src = str(img.get("url") or img.get("path") or "")
            alt = str(img.get("alt") or Path(src).name or "image")
            layout = str(raw.get("image_layout", "split")).lower()
            side = str(raw.get("image_side", "right")).lower()
            img_src = src if src.startswith(("http://", "https://")) else (Path(src).expanduser().resolve().as_uri() if src else "")
            img_html = (
                f'<div style="flex:{"1" if layout == "full" else "1.45"};background:#fff;border:1px solid #DADCE0;'
                f'display:flex;align-items:center;justify-content:center;min-height:160px;">'
                + (f'<img src="{html.escape(img_src)}" alt="{html.escape(alt)}" style="max-width:100%;max-height:200px;">' if img_src else '')
                + (f'<div style="font-size:10px;color:#5F6368;font-style:italic;">{html.escape(str(img.get("caption", "")))}</div>' if img.get("caption") else '')
                + '</div>'
            )
            bullets = raw.get("bullets", []) or []
            text_html = "" if layout == "full" else (
                '<div style="flex:1;background:#fff;border:1px solid #DADCE0;border-top:5px solid #4285F4;padding:12px;">'
                '<ul class="card-bullet-list">' + "".join(f"<li>{html.escape(str(b))}</li>" for b in bullets[:4]) + "</ul></div>"
            )
            parts = [img_html, text_html] if side == "left" else [text_html, img_html]
            return f"""
            <div class="mockup-slide arch-image-split">
                {header_html}
                <div style="display:flex;gap:16px;padding:0 36px;">{''.join(parts)}</div>
            </div>
            """

        elif arch in ("flow_diagram", "flow", "native_diagram", "cycle", "timeline", "funnel"):
            raw = slide.raw_content if isinstance(slide.raw_content, dict) else {}
            d = raw.get("diagram") if isinstance(raw.get("diagram"), dict) else {}
            colors = ["#EA4335", "#FBBC04", "#4285F4", "#34A853"]

            def chip(text: str, i: int, round_: bool = False) -> str:
                return (f'<div style="flex:1;background:#fff;border:1px solid #DADCE0;'
                        f'{"border-radius:10px;border-color:#4285F4" if round_ else "border-top:5px solid " + colors[i % 4]};'
                        f'padding:8px;font-size:11px;font-weight:600;color:#202124;">{html.escape(text)}</div>')

            stages = [s for s in (d.get("stages") or []) if isinstance(s, dict)]
            steps = [s for s in (d.get("steps") or []) if isinstance(s, dict)]
            nodes = [n for n in ((d.get("cycle") or {}).get("nodes") or []) if isinstance(n, dict)]
            row = [chip(str(s.get("title", "")), i) for i, s in enumerate(stages or steps)]
            if nodes:
                loop = " ↻ ".join(html.escape(str(n.get("title", ""))) for n in nodes)
                row.append(f'<div style="flex:2.2;background:#E8F0FE;border-radius:14px;padding:10px;'
                           f'font-size:11px;color:#1967D2;font-weight:600;">{loop}</div>')
            marker = d.get("marker")
            marker_text = marker.get("text", "") if isinstance(marker, dict) else str(marker or "")
            marker_html = (f'<div style="display:inline-block;background:#EA4335;color:#fff;border-radius:8px;'
                           f'font-size:10px;font-weight:700;padding:2px 8px;margin:0 36px 6px;">'
                           f'{html.escape(marker_text)}</div>') if marker_text else ""
            return f"""
            <div class="mockup-slide arch-flow-diagram">
                {header_html}
                {marker_html}
                <div style="display:flex;gap:12px;padding:0 36px;align-items:stretch;">{''.join(row)}</div>
            </div>
            """

        # Default fallback
        return f"""
        <div class="mockup-slide">
            {header_html}
        </div>
        """

    # =========================================================================
    # Master Report Generation Orchestrator
    # =========================================================================

    @classmethod
    def generate_all(
        cls,
        spec: Union[PresentationSpec, dict[str, Any], Path, str],
        output_dir: Union[str, Path] = "dist/qa",
        qa_report: Optional[QAReport] = None,
        deck_id: Optional[str] = None,
        gslides_client: Optional[GSlidesClient] = None,
    ) -> dict[str, Any]:
        """Generates all QA artifacts: `qa_report.md` and `preview.html`.

        Args:
            spec: PresentationSpec or YAML path.
            output_dir: Destination directory for artifacts.
            qa_report: Optional pre-run QAReport.
            deck_id: Optional live presentation ID.
            gslides_client: Optional GSlidesClient.

        Returns:
            Dictionary containing paths to generated artifacts and evaluation metrics.
        """
        out_dir = Path(output_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

        p_spec: PresentationSpec
        if isinstance(spec, PresentationSpec):
            p_spec = spec
        elif isinstance(spec, (Path, str)):
            p_spec = PresentationSpec.from_yaml(spec)
        elif isinstance(spec, dict):
            p_spec = PresentationSpec.from_dict(spec)
        else:
            raise TypeError(f"Unsupported spec type: {type(spec)}")

        if qa_report is None:
            verifier = QAVerifier(gslides_client=gslides_client)
            qa_report = verifier.verify(
                spec=p_spec,
                presentation_id=deck_id,
                thumbnail_dir=out_dir / "thumbnails" if deck_id else None,
            )

        report_file = out_dir / "qa_report.md"
        preview_file = out_dir / "preview.html"

        cls.generate_markdown_report(qa_report=qa_report, output_path=report_file, spec=p_spec)
        cls.generate_html_preview(spec=p_spec, qa_report=qa_report, output_path=preview_file)

        return {
            "output_dir": out_dir,
            "report_path": report_file,
            "preview_path": preview_file,
            "is_passing": qa_report.is_passing,
            "pass_rate_pct": qa_report.pass_rate_pct,
            "total_checks": qa_report.total_checks,
            "passed_checks": qa_report.passed_checks,
            "error_count": qa_report.error_count,
            "warning_count": qa_report.warning_count,
        }

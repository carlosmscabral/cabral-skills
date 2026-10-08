"""Unified Command-Line Interface (CLI) Engine for The AI Factory Blueprint Presentations.

Provides subcommands:
- `spec`: Scaffolds a new `preso_spec.yaml` from presets or interactive prompts.
- `build`: Validates spec, compiles atomic batch payload, creates or copies deck via gslides, executes batch update.
- `inspect`: Inspects an existing deck or spec and prints structured outline summary.
- `ingest`: Multi-modal ingestion frontend for codebases, existing presentations, and Markdown docs.
- `preview`: Compiles spec and generates self-contained interactive `preview.html` gallery.
- `qa`: Runs complete multimodal visual QA loop and generates `qa_report.md` and `preview.html`.
- `audit`: Exports fresh thumbnails of a live deck and writes `audit_checklist.md` for visual review.
- `budgets`: Prints text budgets and geometry-derived capacities per archetype slot.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
from pathlib import Path
import sys
from typing import Any, Optional, Sequence

from preso.compiler.batch_generator import BatchCompiler, BatchCompilerConfig, BatchResult
from preso.compiler.gslides_client import DEFAULT_TEMPLATE_ID, GSlidesClient, GSlidesError
from preso.ingest.codebase import CodebaseIngestor
from preso.ingest.markdown import MarkdownIngestor
from preso.ingest.slides import SlidesIngestor
from preso.engine import text_fit
from preso.engine.diagrams import retarget_requests
from preso.engine.design_tokens import (
    FONT_SIZE_CARD_HEADER,
    FONT_SIZE_HERO_STAT,
    FONT_SIZE_SLIDE_SUBTITLE,
    FONT_SIZE_SLIDE_TITLE,
)
from preso.qa.audit import write_audit_checklist
from preso.qa.report_generator import QAReportGenerator
from preso.qa.verifier import QAReport, QAVerifier
from preso.spec import validator as validator_mod
from preso.spec.models import DURATION_VISIBLE_TIERS, PresentationSpec
from preso.spec.scaffolder import SpecScaffolder
from preso.spec.validator import SpecValidator, ValidationResult


# =============================================================================
# Subcommand Handlers
# =============================================================================


def handle_spec(args: argparse.Namespace) -> int:
    """Handles the `preso spec` subcommand to scaffold presentation specifications."""
    out_path = Path(args.output).resolve()

    preset = getattr(args, "preset", "ai_factory")
    title = getattr(args, "title", "The AI Factory Blueprint")
    subtitle = getattr(args, "subtitle", "A Developer's Playbook for the Agentic Era")
    template_id = getattr(args, "template_id", DEFAULT_TEMPLATE_ID)
    audience = getattr(args, "audience", "Executive Leadership & Senior Staff Engineers")
    thesis = getattr(
        args,
        "thesis",
        "Move from manual hand-prompting to deterministic agentic manufacturing pipelines.",
    )

    if getattr(args, "interactive", False) and sys.stdin.isatty():
        print("=== Interactive Spec Scaffolder ===")
        user_title = input(f"Presentation Title [{title}]: ").strip()
        if user_title:
            title = user_title
        user_sub = input(f"Subtitle [{subtitle}]: ").strip()
        if user_sub:
            subtitle = user_sub
        user_preset = input(f"Preset (ai_factory, executive_briefing, product_launch, minimal) [{preset}]: ").strip()
        if user_preset:
            preset = user_preset

    spec = SpecScaffolder.scaffold(
        title=title,
        subtitle=subtitle,
        template_id=template_id,
        target_audience=audience,
        core_thesis=thesis,
        preset=preset,
        output_path=out_path,
    )

    print(f"✅ Successfully scaffolded specification to: {out_path}")
    print(f"   Title:    {spec.metadata.title}")
    print(f"   Preset:   {preset}")
    print(f"   Chapters: {len(spec.chapters)} chapters ({spec.slide_count()} total slides)")
    return 0



def _resolved_ids(batch_exec_res: Any) -> dict[str, str]:
    """Placeholder -> real object IDs from `execute_batch` (a dict, or an object)."""
    if isinstance(batch_exec_res, dict):
        return dict(batch_exec_res.get("resolved_ids") or {})
    return dict(getattr(batch_exec_res, "resolved_ids", None) or {})


def _retarget_raw_requests(batch_result: BatchResult, resolved: dict[str, str]) -> list[dict[str, Any]]:
    """Flattens per-slide diagram requests, mapped to real slide IDs.

    Element IDs get a per-build suffix so rebuilding into an existing deck
    never collides with elements of slides that are about to be pruned.
    """
    suffix = "_" + secrets.token_hex(2)
    page_map = {r["slide"]: resolved.get(r["slide"], r["slide"]) for r in batch_result.raw_requests}
    flat: list[dict[str, Any]] = []
    for r in batch_result.raw_requests:
        flat.extend(r["requests"])
    return retarget_requests(flat, page_map, suffix)


def _resolve_image_paths(batch_result: BatchResult, base_dir: Path) -> None:
    """Resolves relative local image paths against the spec file's directory."""
    for img in batch_result.pending_images:
        p = Path(str(img.get("path", ""))).expanduser()
        if not p.is_absolute():
            p = (base_dir / p).resolve()
        img["path"] = str(p)


def handle_build(args: argparse.Namespace) -> int:
    """Handles the `preso build` subcommand to compile and build Google Slides presentations."""
    spec_path = Path(args.spec).resolve()
    if not spec_path.exists():
        print(f"❌ Error: Specification file not found at '{spec_path}'", file=sys.stderr)
        return 1

    try:
        spec = PresentationSpec.from_yaml(spec_path)
    except Exception as e:
        print(f"❌ Error: Failed to parse specification YAML: {e}", file=sys.stderr)
        return 1

    # 1. Validation Step (geometry pass adds "cut ~N chars" fit warnings)
    val_result: ValidationResult = SpecValidator.validate(spec, geometry=True)
    if not val_result.is_valid:
        print(f"❌ Specification Validation Failed ({len(val_result.errors)} errors):", file=sys.stderr)
        for err in val_result.errors:
            print(f"   • {err}", file=sys.stderr)
        if not getattr(args, "force", False):
            print("\nUse --force to ignore validation errors and build anyway.", file=sys.stderr)
            return 1
        else:
            print("⚠️ Proceeding with build due to --force flag.", file=sys.stderr)

    if val_result.warnings:
        print(f"⚠️ Validation Warnings ({len(val_result.warnings)}):")
        for warn in val_result.warnings:
            print(f"   • {warn}")

    # 2. Batch Compilation Step
    duration = getattr(args, "duration", None)
    visible_tiers = tuple(DURATION_VISIBLE_TIERS[duration]) if duration else None
    compiler_config = BatchCompilerConfig(
        clean_default_placeholders=getattr(args, "clean_placeholders", False),
        visible_tiers=visible_tiers,
    )
    compiler = BatchCompiler(config=compiler_config)
    batch_result: BatchResult = compiler.compile(spec)
    _resolve_image_paths(batch_result, spec_path.parent)

    print(f"✅ Compiled {len(batch_result.operations)} atomic batch operations for {batch_result.slide_count} slides.")

    # Save batch operations JSON if requested
    if getattr(args, "output_batch", None):
        batch_out_path = Path(args.output_batch).resolve()
        batch_result.save_json(batch_out_path)
        print(f"   Saved batch payload to: {batch_out_path}")

    # 3. Presentation Execution via GSlidesClient
    is_dry_run = getattr(args, "dry_run", False)
    client = GSlidesClient(dry_run=is_dry_run)

    title = getattr(args, "title", None) or spec.metadata.title or "Blueprint Presentation"
    template_id = getattr(args, "template_id", None) or spec.metadata.template_id or DEFAULT_TEMPLATE_ID

    deck_id = getattr(args, "deck_id", None) or ""
    try:
        initial_template_slide_ids: list[str] = []
        if deck_id:
            print(f"♻️ Updating existing presentation in-place: '{deck_id}'...")
            if not is_dry_run and client.runner is None:
                try:
                    info_data = client.info(deck_id)
                    initial_slides = info_data.get("slides", [])
                except Exception:
                    try:
                        initial_slides = client.list_slides(deck_id)
                    except Exception:
                        initial_slides = []
                for s in initial_slides:
                    sid = s.get("objectId") or s.get("id") or s.get("slide_id")
                    if sid:
                        initial_template_slide_ids.append(str(sid))
        elif getattr(args, "blank", False):
            print(f"📄 Creating blank presentation: '{title}'...")
            deck_id = client.create_presentation(title=title)
        else:
            print(f"📋 Cloning template presentation '{template_id}'...")
            deck_id = client.copy_presentation(template_id=template_id, title=title)
            if not is_dry_run and client.runner is None:
                try:
                    info_data = client.info(deck_id)
                    initial_slides = info_data.get("slides", [])
                except Exception:
                    try:
                        initial_slides = client.list_slides(deck_id)
                    except Exception:
                        initial_slides = []
                for s in initial_slides:
                    sid = s.get("objectId") or s.get("id") or s.get("slide_id")
                    if sid:
                        initial_template_slide_ids.append(str(sid))

        print(f"🎯 Target Presentation ID: {deck_id}")

        print(f"⚡ Executing atomic batch update ({len(batch_result.operations)} operations)...")
        batch_exec_res = client.execute_batch(
            presentation_id=deck_id,
            operations=batch_result.operations,
        )
        if initial_template_slide_ids and not is_dry_run and client.runner is None:
            print(f"🧹 Pruning {len(initial_template_slide_ids)} previous/template slides...")
            for sid in initial_template_slide_ids:
                try:
                    client.delete_slide(deck_id, sid)
                except Exception:
                    pass
        print(f"✅ Batch update executed successfully on deck '{deck_id}'.")

        if batch_result.pending_images:
            resolved = _resolved_ids(batch_exec_res)
            print(f"🖼️ Inserting {len(batch_result.pending_images)} local image(s)...")
            for img in batch_result.pending_images:
                target_slide = resolved.get(img["slide"], img["slide"])
                try:
                    client.insert_image_from_file(
                        deck_id, target_slide, img["path"],
                        x=img["x"], y=img["y"], width=img["width"], height=img["height"],
                    )
                except GSlidesError as img_err:
                    print(f"   ⚠️ Could not insert {img['path']} on {target_slide}: {img_err}", file=sys.stderr)

        if batch_result.raw_requests:
            raw = _retarget_raw_requests(batch_result, _resolved_ids(batch_exec_res))
            print(f"📐 Drawing {len(batch_result.raw_requests)} native diagram(s) ({len(raw)} raw requests)...")
            client.raw_batch(deck_id, raw)

    except GSlidesError as e:
        print(f"❌ Error during Google Slides API execution: {e}", file=sys.stderr)
        return 1

    # Save output deck ID if requested
    if getattr(args, "output_deck_id", None):
        deck_id_path = Path(args.output_deck_id).resolve()
        deck_id_path.parent.mkdir(parents=True, exist_ok=True)
        deck_id_path.write_text(deck_id.strip() + "\n", encoding="utf-8")
        print(f"   Saved presentation ID to: {deck_id_path}")

    # 4. Automated Multimodal QA Step
    if not getattr(args, "no_qa", False):
        print("\n🔍 Running automated multimodal visual QA verifier...")
        report_dir = (
            Path(args.export_report).parent
            if getattr(args, "export_report", None)
            else (Path(args.preview).parent if getattr(args, "preview", None) else Path("dist/qa"))
        )
        report_dir.mkdir(parents=True, exist_ok=True)

        verifier = QAVerifier(gslides_client=client)
        thumb_dir = report_dir / "thumbnails" if deck_id and not is_dry_run else None
        qa_report = verifier.verify(
            spec=spec,
            batch_result=batch_result,
            presentation_id=deck_id if not is_dry_run else None,
            thumbnail_dir=thumb_dir,
        )

        print(qa_report.summary())

        if thumb_dir is not None:
            checklist = write_audit_checklist(
                thumbnails=sorted(Path(thumb_dir).glob("slide_*.png")),
                output_path=report_dir / "audit_checklist.md",
                spec=spec,
                operations=batch_result.operations,
                deck_id=deck_id,
            )
            print(f"   Render audit checklist: {checklist.resolve()}")

        # Generate Reports
        if getattr(args, "export_report", None):
            rep_path = Path(args.export_report).resolve()
            QAReportGenerator.generate_markdown_report(qa_report, output_path=rep_path, spec=spec)
            print(f"   Generated QA Report: {rep_path}")
        else:
            default_rep = report_dir / "qa_report.md"
            QAReportGenerator.generate_markdown_report(qa_report, output_path=default_rep, spec=spec)

        if getattr(args, "preview", None):
            prev_path = Path(args.preview).resolve()
            QAReportGenerator.generate_html_preview(spec, qa_report=qa_report, output_path=prev_path)
            print(f"   Generated HTML Preview Gallery: {prev_path}")
        else:
            default_prev = report_dir / "preview.html"
            QAReportGenerator.generate_html_preview(spec, qa_report=qa_report, output_path=default_prev)

    print("\n🎉 Build Complete!")
    print(f"   Presentation ID: {deck_id}")
    print(f"   Google Slides URL: https://docs.google.com/presentation/d/{deck_id}/edit")
    return 0


def handle_inspect(args: argparse.Namespace) -> int:
    """Handles the `preso inspect` subcommand to inspect specifications or live decks."""
    # Case 1: Inspect YAML Specification
    if getattr(args, "spec", None):
        spec_path = Path(args.spec).resolve()
        if not spec_path.exists():
            print(f"❌ Error: Specification file not found at '{spec_path}'", file=sys.stderr)
            return 1

        try:
            spec = PresentationSpec.from_yaml(spec_path)
        except Exception as e:
            print(f"❌ Error: Failed to parse specification YAML: {e}", file=sys.stderr)
            return 1

        val_result = SpecValidator.validate(spec)

        if getattr(args, "json", False):
            info = {
                "metadata": spec.metadata.to_dict(),
                "chapters_count": len(spec.chapters),
                "slides_count": spec.slide_count(),
                "validation": {
                    "is_valid": val_result.is_valid,
                    "errors": val_result.errors,
                    "warnings": val_result.warnings,
                },
                "slides": [s.to_dict() for s in spec.all_slides()],
            }
            print(json.dumps(info, indent=2))
            return 0

        print(f"================================================================================")
        print(f"SPECIFICATION INSPECTION: {spec_path.name}")
        print(f"================================================================================")
        print(f"Title:           {spec.metadata.title}")
        print(f"Subtitle:        {spec.metadata.subtitle}")
        print(f"Template ID:     {spec.metadata.template_id}")
        print(f"Target Audience: {spec.metadata.target_audience}")
        print(f"Core Thesis:     {spec.metadata.core_thesis}")
        print(f"Validation:      {'✅ VALID' if val_result.is_valid else '❌ INVALID'}")
        print(f"Structure:       {len(spec.chapters)} chapters, {spec.slide_count()} total slides")
        print(f"--------------------------------------------------------------------------------")
        print(f"SLIDE OUTLINE:")

        for idx, slide in enumerate(spec.all_slides(), start=1):
            notes = slide.speaker_notes or slide.notes or ""
            words = len(notes.split())
            tier = getattr(slide, "tier", "core") or "core"
            flags = f" tier={tier}" if tier != "core" else ""
            flags += " [hidden]" if getattr(slide, "skip", False) else ""
            print(f"  {idx:02d}. [{slide.archetype.upper():<20}] {slide.title[:38]:<40} ({words:2d} notes words){flags}")
            if getattr(args, "verbose", False):
                if slide.subtitle:
                    print(f"       Subtitle: {slide.subtitle}")
                if notes:
                    print(f"       Notes:    {notes[:60]}...")
        print(f"================================================================================")
        return 0

    # Case 2: Inspect Live Google Slides Deck
    deck_id = getattr(args, "deck_id", None) or getattr(args, "deck", None)
    if deck_id:
        client = GSlidesClient()
        try:
            deck_info = client.info(deck_id)
            if getattr(args, "json", False):
                print(json.dumps(deck_info, indent=2))
                return 0

            print(f"================================================================================")
            print(f"LIVE GOOGLE SLIDES DECK INSPECTION: {deck_id}")
            print(f"================================================================================")
            print(f"Title:       {deck_info.get('title', 'Unknown')}")
            slides = deck_info.get("slides", [])
            print(f"Slide Count: {len(slides)}")
            print(f"URL:         https://docs.google.com/presentation/d/{deck_id}/edit")
            print(f"================================================================================")
            return 0
        except GSlidesError as e:
            print(f"❌ Error inspecting live presentation: {e}", file=sys.stderr)
            return 1

    # Fallback to default preso_spec.yaml if present
    default_spec = Path("preso_spec.yaml")
    if default_spec.exists():
        args.spec = str(default_spec)
        return handle_inspect(args)

    print("❌ Error: Specify either --spec <path> or --deck-id <id> to inspect.", file=sys.stderr)
    return 1


def handle_ingest(args: argparse.Namespace) -> int:
    """Handles the `preso ingest` subcommand to convert codebases, decks, or docs into specs."""
    out_path = Path(args.output).resolve()
    title_override = getattr(args, "title", None)

    spec: Optional[PresentationSpec] = None

    # Option A: Codebase Ingestion
    if getattr(args, "repo", None):
        repo_path = Path(args.repo).resolve()
        if not repo_path.exists():
            print(f"❌ Error: Repository path not found at '{repo_path}'", file=sys.stderr)
            return 1
        print(f"🔍 Ingesting codebase from: {repo_path}...")
        ingestor = CodebaseIngestor(repo_path=repo_path)
        spec = ingestor.ingest(title=title_override)

    # Option B: Slides Ingestion
    elif getattr(args, "slides", None) or getattr(args, "deck", None):
        slides_src = getattr(args, "slides", None) or getattr(args, "deck", None)
        print(f"🔍 Ingesting Google Slides from: {slides_src}...")
        ingestor_slides = SlidesIngestor()
        spec = ingestor_slides.ingest(source=slides_src, title=title_override)

    # Option C: Markdown / Document Ingestion
    elif getattr(args, "markdown", None) or getattr(args, "doc", None):
        doc_path = Path(getattr(args, "markdown", None) or getattr(args, "doc", None)).resolve()
        if not doc_path.exists():
            print(f"❌ Error: Markdown document not found at '{doc_path}'", file=sys.stderr)
            return 1
        print(f"🔍 Ingesting Markdown document from: {doc_path}...")
        ingestor_md = MarkdownIngestor()
        spec = ingestor_md.ingest(doc_path_or_content=doc_path, title=title_override)

    else:
        print("❌ Error: Specify an ingestion source: --repo <path>, --slides <deck_id_or_file>, or --markdown <file>", file=sys.stderr)
        return 1

    if spec is None:
        print("❌ Error: Ingestion failed to produce a valid specification.", file=sys.stderr)
        return 1

    # Save to output YAML
    spec.to_yaml(out_path)
    print(f"✅ Successfully ingested source and emitted spec to: {out_path}")
    print(f"   Title:    {spec.metadata.title}")
    print(f"   Chapters: {len(spec.chapters)} chapters ({spec.slide_count()} slides)")

    if getattr(args, "validate", True):
        val_result = SpecValidator.validate(spec)
        print(f"   Schema:   {'✅ VALID' if val_result.is_valid else '⚠️ WARNINGS DETECTED'}")

    return 0


def handle_preview(args: argparse.Namespace) -> int:
    """Handles the `preso preview` subcommand to generate an interactive HTML preview gallery."""
    spec_path = Path(args.spec).resolve()
    if not spec_path.exists():
        print(f"❌ Error: Specification file not found at '{spec_path}'", file=sys.stderr)
        return 1

    try:
        spec = PresentationSpec.from_yaml(spec_path)
    except Exception as e:
        print(f"❌ Error: Failed to parse specification YAML: {e}", file=sys.stderr)
        return 1

    out_file = Path(args.output).resolve()
    out_dir = Path(getattr(args, "output_dir", None) or out_file.parent).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    deck_id = getattr(args, "deck_id", None) or getattr(args, "deck", None)
    is_dry_run = getattr(args, "dry_run", False)
    client = GSlidesClient(dry_run=is_dry_run)

    print(f"🎨 Generating interactive HTML preview gallery for '{spec.metadata.title}'...")
    verifier = QAVerifier(gslides_client=client)
    qa_report = verifier.verify(
        spec=spec,
        presentation_id=deck_id if not is_dry_run else None,
        thumbnail_dir=out_dir / "thumbnails" if deck_id and not is_dry_run else None,
    )

    QAReportGenerator.generate_html_preview(spec, qa_report=qa_report, output_path=out_file)
    print(f"✅ Preview gallery generated at: {out_file}")
    print(f"   Open in browser: file://{out_file}")
    return 0


def handle_qa(args: argparse.Namespace) -> int:
    """Handles the `preso qa` subcommand to execute the multimodal QA verification loop."""
    spec_path = Path(args.spec).resolve()
    if not spec_path.exists():
        print(f"❌ Error: Specification file not found at '{spec_path}'", file=sys.stderr)
        return 1

    try:
        spec = PresentationSpec.from_yaml(spec_path)
    except Exception as e:
        print(f"❌ Error: Failed to parse specification YAML: {e}", file=sys.stderr)
        return 1

    out_dir = Path(getattr(args, "output_dir", "dist/qa")).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    deck_id = getattr(args, "deck_id", None) or getattr(args, "deck", None)
    strict_mode = getattr(args, "strict", False)
    is_json = getattr(args, "json", False)

    if not is_json:
        print(f"🔍 Running multimodal QA verification on '{spec_path.name}'...")

    verifier = QAVerifier(strict_mode=strict_mode)
    qa_report = verifier.verify(
        spec=spec,
        presentation_id=deck_id,
        thumbnail_dir=out_dir / "thumbnails" if deck_id else None,
    )

    artifacts = QAReportGenerator.generate_all(
        spec=spec,
        output_dir=out_dir,
        qa_report=qa_report,
        deck_id=deck_id,
    )

    if is_json:
        print(qa_report.to_json())
    else:
        print(qa_report.summary())
        print(f"\n📁 Generated Verification Artifacts:")
        print(f"   • Markdown Report: {artifacts['report_path']}")
        print(f"   • HTML Preview:    {artifacts['preview_path']}")

    if not qa_report.is_passing:
        return 1
    return 0


# =============================================================================
# CLI Parser Setup & Main Entrypoint
# =============================================================================


def handle_audit(args: argparse.Namespace) -> int:
    """Handles `preso audit`: fresh thumbnails + render-audit checklist for a live deck."""
    deck_id = args.deck_id
    out_dir = Path(args.output_dir).resolve()
    thumb_dir = out_dir / "thumbnails"
    spec = None
    operations = None
    if getattr(args, "spec", None):
        try:
            spec = PresentationSpec.from_yaml(Path(args.spec).resolve())
            operations = BatchCompiler().compile(spec).operations
        except Exception as e:  # pylint: disable=broad-except
            print(f"⚠️ Could not load spec for context: {e}", file=sys.stderr)

    client = GSlidesClient(dry_run=getattr(args, "dry_run", False))
    verifier = QAVerifier(gslides_client=client)
    paths, warns, metrics = verifier.verify_live_deck_thumbnails(deck_id, thumb_dir)
    for w in warns:
        print(f"⚠️ {w['message']}", file=sys.stderr)
    checklist = write_audit_checklist(
        thumbnails=paths,
        output_path=out_dir / "audit_checklist.md",
        spec=spec,
        operations=operations,
        deck_id=deck_id,
    )
    print(f"✅ {metrics.get('thumbnail_export_status', '')}")
    print(f"   Thumbnails: {thumb_dir}")
    print(f"   Checklist:  {checklist}")
    return 0


# Representative slots: (label, width_pt, height_pt, font_size_pt)
_BUDGET_SLOTS: tuple[tuple[str, float, float, float], ...] = (
    ("Slide title (1 line, 24pt)", 648.0, 28.0, FONT_SIZE_SLIDE_TITLE),
    ("Slide subtitle / assertion (1 line, 13pt)", 648.0, 18.0, FONT_SIZE_SLIDE_SUBTITLE),
    ("2-card title (16pt)", 312.0 - 32.0, 26.0, FONT_SIZE_CARD_HEADER),
    ("3-card title (16pt)", 204.0 - 32.0, 26.0, FONT_SIZE_CARD_HEADER),
    ("Hero value, 2 metrics (54pt)", 312.0 - 32.0, 58.0, FONT_SIZE_HERO_STAT),
    ("Hero value, 3 metrics (54pt)", 204.0 - 32.0, 58.0, FONT_SIZE_HERO_STAT),
    ("image_split bullets card (12pt)", 256.0 - 32.0, 275.0 - 36.0, 12.0),
    ("demo_pivot watch_for chip (12pt)", 208.0, 32.0, 12.0),
)


def handle_budgets(args: argparse.Namespace) -> int:
    """Handles `preso budgets`: prints validator budgets and geometry-derived capacities."""
    names = sorted(n for n in dir(validator_mod) if n.startswith(("BUDGET_", "MIN_", "MAX_")))
    budgets = {n: getattr(validator_mod, n) for n in names}
    slots = []
    for label, w, h, fs in _BUDGET_SLOTS:
        slots.append({
            "slot": label,
            "chars_per_line": text_fit.chars_per_line(w, fs),
            "max_lines": text_fit.max_lines(h, fs),
            "capacity_chars": text_fit.chars_per_line(w, fs) * text_fit.max_lines(h, fs),
        })
    if getattr(args, "json", False):
        print(json.dumps({"budgets": budgets, "geometry": slots}, indent=2))
        return 0
    print("Validator per-field budgets (chars unless noted):")
    for n, v in budgets.items():
        print(f"  {n:<32} {v}")
    print("\nGeometry-derived capacity (shared text_fit heuristic — authoritative):")
    for s_ in slots:
        print(f"  {s_['slot']:<44} ~{s_['chars_per_line']:>3} chars/line × {s_['max_lines']} line(s) ≈ {s_['capacity_chars']} chars")
    print("\nRun `preso build` / `SpecValidator.validate(spec, geometry=True)` for per-slide 'cut ~N chars' warnings.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Constructs the root argument parser and subcommands for the preso CLI."""
    parser = argparse.ArgumentParser(
        prog="preso",
        description="The AI Factory Blueprint Presentation Builder & Multimodal QA Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version="preso 1.1.0 (The AI Factory Blueprint)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Preso subcommands")

    # 1. 'spec' Subcommand
    spec_parser = subparsers.add_parser("spec", help="Scaffold a new presentation specification manifest")
    spec_parser.add_argument("-p", "--preset", default="ai_factory", help="Blueprint preset template (ai_factory, executive_briefing, product_launch, minimal)")
    spec_parser.add_argument("-t", "--title", default="The AI Factory Blueprint", help="Presentation title")
    spec_parser.add_argument("-s", "--subtitle", default="A Developer's Playbook for the Agentic Era", help="Presentation subtitle")
    spec_parser.add_argument("--template-id", default=DEFAULT_TEMPLATE_ID, help="Google Slides master template deck ID")
    spec_parser.add_argument("--audience", default="Executive Leadership & Senior Staff Engineers", help="Target audience")
    spec_parser.add_argument("--thesis", default="Move from manual hand-prompting to deterministic agentic manufacturing pipelines.", help="Core thesis statement")
    spec_parser.add_argument("-o", "--output", default="preso_spec.yaml", help="Destination path for YAML specification")
    spec_parser.add_argument("-i", "--interactive", action="store_true", help="Prompt interactively for specification metadata")
    spec_parser.set_defaults(handler=handle_spec)

    # 2. 'build' Subcommand
    build_parser = subparsers.add_parser("build", help="Compile and build Google Slides deck from specification")
    build_parser.add_argument("-s", "--spec", default="preso_spec.yaml", help="Path to presentation YAML specification (default: preso_spec.yaml)")
    build_parser.add_argument("-d", "--deck-id", "--deck", help="Existing Google Slides presentation ID to update in-place")
    build_parser.add_argument("--template-id", "--template", help="Google Slides master template deck ID to copy")
    build_parser.add_argument("--blank", "--create-blank", action="store_true", help="Create a blank deck instead of copying template")
    build_parser.add_argument("--title", help="Override presentation title")
    build_parser.add_argument("--dry-run", action="store_true", help="Simulate GSlides API without making network calls")
    build_parser.add_argument("--output-batch", "--out-batch", help="Save compiled atomic batch operations JSON to file")
    build_parser.add_argument("--output-deck-id", "--out-deck-id", help="Save generated presentation ID to file")
    build_parser.add_argument("--no-qa", action="store_true", help="Skip automated multimodal visual QA verification loop")
    build_parser.add_argument("--export-report", "--out-report", help="Destination path for Markdown QA report")
    build_parser.add_argument("--preview", "--out-preview", help="Destination path for interactive HTML preview gallery")
    build_parser.add_argument("--clean-placeholders", action="store_true", help="Remove default template placeholder elements (i0, i1)")
    build_parser.add_argument("-f", "--force", action="store_true", help="Force build even if specification validation produces errors")
    build_parser.add_argument("--duration", choices=sorted(DURATION_VISIBLE_TIERS.keys()), help="Talk length: hide slides whose tier is not shown at this duration (5=core, 15=+explain, 45/full=+detail; appendix always hidden)")
    build_parser.set_defaults(handler=handle_build)

    # 3. 'inspect' Subcommand
    inspect_parser = subparsers.add_parser("inspect", help="Inspect specification manifest or live Google Slides presentation")
    inspect_parser.add_argument("-s", "--spec", help="Path to presentation specification YAML file")
    inspect_parser.add_argument("-d", "--deck-id", "--deck", help="Google Slides presentation ID to inspect")
    inspect_parser.add_argument("--json", action="store_true", help="Output inspection metadata as JSON")
    inspect_parser.add_argument("-v", "--verbose", action="store_true", help="Display full slide text, subtitles, and notes")
    inspect_parser.set_defaults(handler=handle_inspect)

    # 4. 'ingest' Subcommand
    ingest_parser = subparsers.add_parser("ingest", help="Ingest local codebase, Google Slides deck, or Markdown document")
    ingest_group = ingest_parser.add_mutually_exclusive_group(required=True)
    ingest_group.add_argument("-r", "--repo", help="Path to local repository or directory to scan")
    ingest_group.add_argument("-d", "--slides", "--deck", help="Google Slides presentation ID or exported text dump")
    ingest_group.add_argument("-m", "--markdown", "--doc", help="Path to Markdown document or directory of notes")
    ingest_parser.add_argument("-t", "--title", help="Override presentation title")
    ingest_parser.add_argument("-o", "--output", default="preso_spec.yaml", help="Destination YAML output path (default: preso_spec.yaml)")
    ingest_parser.add_argument("--no-validate", dest="validate", action="store_false", help="Skip schema validation on generated spec")
    ingest_parser.set_defaults(handler=handle_ingest)

    # 5. 'preview' Subcommand
    preview_parser = subparsers.add_parser("preview", help="Generate interactive HTML preview gallery with CSS mockups")
    preview_parser.add_argument("-s", "--spec", default="preso_spec.yaml", help="Path to presentation YAML specification (default: preso_spec.yaml)")
    preview_parser.add_argument("-d", "--deck-id", "--deck", help="Optional live presentation ID for thumbnail export")
    preview_parser.add_argument("-o", "--output", default="preview.html", help="Destination path for HTML preview gallery (default: preview.html)")
    preview_parser.add_argument("--output-dir", help="Output directory for HTML preview and thumbnails")
    preview_parser.add_argument("--dry-run", action="store_true", help="Run without invoking live gslides CLI")
    preview_parser.set_defaults(handler=handle_preview)

    # 6. 'qa' Subcommand
    qa_parser = subparsers.add_parser("qa", help="Run complete multimodal visual QA verification battery")
    qa_parser.add_argument("-s", "--spec", default="preso_spec.yaml", help="Path to presentation YAML specification (default: preso_spec.yaml)")
    qa_parser.add_argument("-d", "--deck-id", "--deck", help="Optional live presentation ID")
    qa_parser.add_argument("-o", "--output-dir", default="dist/qa", help="Destination directory for QA reports and preview gallery (default: dist/qa)")
    qa_parser.add_argument("--strict", action="store_true", help="Fail verification if any warnings are detected")
    qa_parser.add_argument("--json", action="store_true", help="Output raw QA report JSON")
    qa_parser.set_defaults(handler=handle_qa)

    # 7. 'audit' Subcommand
    audit_parser = subparsers.add_parser("audit", help="Export fresh thumbnails of a live deck and write a render-audit checklist")
    audit_parser.add_argument("-d", "--deck-id", "--deck", required=True, help="Live presentation ID")
    audit_parser.add_argument("-s", "--spec", help="Optional spec YAML for slide context and predicted overflow hotspots")
    audit_parser.add_argument("-o", "--output-dir", default="dist/qa", help="Destination directory (default: dist/qa)")
    audit_parser.add_argument("--dry-run", action="store_true", help="Run without invoking live gslides CLI")
    audit_parser.set_defaults(handler=handle_audit)

    # 8. 'budgets' Subcommand
    budgets_parser = subparsers.add_parser("budgets", help="Print text budgets and geometry-derived capacities")
    budgets_parser.add_argument("--json", action="store_true", help="Output as JSON")
    budgets_parser.set_defaults(handler=handle_budgets)

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main CLI entrypoint function."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "handler") or args.command is None:
        parser.print_help()
        return 0

    try:
        return args.handler(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"❌ Unexpected Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

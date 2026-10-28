#!/usr/bin/env python3
"""Rasterize standalone vector SVGs (e.g. from Dendrite) into Google Slides-calibrated PNGs.

Scales SVG vectors directly in Headless Chrome Skia space up to --max-width (default 1999px)
so Google Slides' server-side `=s2048` image cap performs zero downscaling blur.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _find_chrome() -> str:
    for candidate in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        found = shutil.which(candidate)
        if found:
            return found
    raise RuntimeError("No Chrome/Chromium binary found on PATH.")


def _parse_svg_aspect(svg_text: str) -> tuple[float, float]:
    head = svg_text[:2000]
    vb = re.search(r'\bviewBox=["\']\s*[-0-9.]+\s+[-0-9.]+\s+([0-9.]+)\s+([0-9.]+)\s*["\']', head)
    if vb:
        return float(vb.group(1)), float(vb.group(2))
    mw = re.search(r'\bwidth=["\']([0-9.]+)', head)
    mh = re.search(r'\bheight=["\']([0-9.]+)', head)
    if mw and mh:
        return float(mw.group(1)), float(mh.group(1))
    return 1280.0, 720.0


def render_one(svg_path: Path, out_dir: Path | None, max_width: int, chrome: str) -> Path:
    svg_text = svg_path.read_text(encoding="utf-8")
    vb_w, vb_h = _parse_svg_aspect(svg_text)
    target_w = min(max_width, max(1200, int(round(vb_w * 1.75))))
    target_h = max(200, int(round(target_w * (vb_h / max(vb_w, 1.0)))))

    # Force root <svg> to fill the exact viewport cleanly
    patched_svg = re.sub(
        r"<svg\b([^>]*)>",
        lambda m: (
            "<svg"
            + re.sub(r'\s+\b(?:width|height)=["\'][^"\']*["\']', "", m.group(1))
            + f' width="{target_w}" height="{target_h}" style="display:block">'
        ),
        svg_text,
        count=1,
    )

    dest_dir = out_dir if out_dir else svg_path.parent
    dest_dir.mkdir(parents=True, exist_ok=True)
    stem = svg_path.stem
    out_png = dest_dir / (f"{stem}.png" if stem.endswith(".slide") else f"{stem}.slide.png")

    with tempfile.TemporaryDirectory(prefix="preso_svg_") as tmp:
        html_file = Path(tmp) / "wrap.html"
        html_file.write_text(
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<style>html,body{margin:0;padding:0;overflow:hidden;background:#ffffff;}</style>"
            f"</head><body>{patched_svg}</body></html>",
            encoding="utf-8",
        )
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                f"--window-size={target_w},{target_h}",
                f"--screenshot={out_png}",
                html_file.as_uri(),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return out_png


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("svgs", nargs="+", type=Path, help="Input .svg file(s)")
    parser.add_argument("-o", "--out-dir", type=Path, default=None, help="Output directory")
    parser.add_argument("--max-width", type=int, default=1999, help="Max PNG pixel width (default: 1999)")
    args = parser.parse_args()

    chrome = _find_chrome()
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(4, len(args.svgs))) as pool:
        futures = [pool.submit(render_one, p.resolve(), args.out_dir, args.max_width, chrome) for p in args.svgs]
        for fut in futures:
            out = fut.result()
            print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

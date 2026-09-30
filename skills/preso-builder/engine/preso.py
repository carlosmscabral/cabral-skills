#!/usr/bin/env python3
"""The AI Factory Blueprint Presentation Builder — Executable CLI Entrypoint.

Usage:
    preso spec      # Scaffold a new preso_spec.yaml
    preso build     # Compile and build Google Slides deck
    preso inspect   # Inspect specification manifest or live deck
    preso ingest    # Multi-modal ingestion (codebase, deck, markdown)
    preso preview   # Generate interactive HTML preview gallery
    preso qa        # Run multimodal visual QA verification
"""

from __future__ import annotations

import sys
from preso.cli import main

if __name__ == "__main__":
    sys.exit(main())

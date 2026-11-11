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

# The agent runs this file in place, inside the skill directory.
# Python must not write `__pycache__` there, because `scripts/validate_repo.py`
# rejects bytecode in the repository tree. Set the flag before the first
# `preso` import. A later assignment does not stop the bytecode of that import.
sys.dont_write_bytecode = True

from preso.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())

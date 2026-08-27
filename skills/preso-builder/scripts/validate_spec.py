#!/usr/bin/env python3
"""
Standalone spec validation utility for preso_spec.yaml manifests.
"""

import sys
import os
from pathlib import Path

# Add project root and standard preso-builder workspace paths to sys.path
workspace_paths = [
    Path(__file__).resolve().parents[3],
    Path.home() / "preso-builder",
    Path(os.getcwd()),
]

for p in workspace_paths:
    if p.exists() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    import yaml
    from preso.spec.validator import SpecValidator
except ImportError as e:
    print(f"❌ Error importing validator: {e}", file=sys.stderr)
    print("Ensure preso-builder is installed (`pip install -e ~/preso-builder`) or in PYTHONPATH.", file=sys.stderr)
    sys.exit(1)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 validate_spec.py <path_to_preso_spec.yaml>")
        sys.exit(1)

    spec_path = Path(sys.argv[1])
    if not spec_path.exists():
        print(f"❌ Error: File not found at '{spec_path}'", file=sys.stderr)
        sys.exit(1)

    try:
        with open(spec_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ YAML Syntax Error: {e}", file=sys.stderr)
        sys.exit(1)

    validator = SpecValidator()
    report = validator.validate(data)

    print("=" * 80)
    print(f"SPECIFICATION VALIDATION: {spec_path.name}")
    print("=" * 80)
    print(f"Status:       {'✅ VALID' if report.is_valid else '❌ INVALID'}")
    print(f"Errors:       {len(report.errors)}")
    print(f"Warnings:     {len(report.warnings)}")
    print("-" * 80)

    if report.errors:
        print("\nERRORS:")
        for i, err in enumerate(report.errors, 1):
            if hasattr(err, "slide_index") and hasattr(err, "field"):
                print(f"  {i}. [Slide {err.slide_index}] {err.field}: {err.message}")
            else:
                print(f"  {i}. {err}")

    if report.warnings:
        print("\nWARNINGS:")
        for i, warn in enumerate(report.warnings, 1):
            if hasattr(warn, "slide_index") and hasattr(warn, "field"):
                print(f"  {i}. [Slide {warn.slide_index}] {warn.field}: {warn.message}")
            else:
                print(f"  {i}. {warn}")

    if not report.errors and not report.warnings:
        print("🎉 All schema checks, character limits, and speaker notes rules passed cleanly!")

    print("=" * 80)
    sys.exit(0 if report.is_valid else 1)

if __name__ == "__main__":
    main()

"""Multimodal Visual QA Verifier Module.

Provides deterministic spec, geometry, contrast, and visual verification
along with Markdown and interactive HTML preview gallery generators.
"""

from preso.qa.report_generator import QAReportGenerator
from preso.qa.verifier import (
    QAReport,
    QAVerifier,
    SAFE_BOUNDS_X_MAX,
    SAFE_BOUNDS_X_MIN,
    SAFE_BOUNDS_Y_MAX,
    SAFE_BOUNDS_Y_MIN,
    SAFE_MARGIN_BOTTOM,
    SAFE_MARGIN_LEFT,
    SAFE_MARGIN_RIGHT,
    SAFE_MARGIN_TOP,
)

__all__ = [
    "QAVerifier",
    "QAReport",
    "QAReportGenerator",
    "SAFE_MARGIN_LEFT",
    "SAFE_MARGIN_RIGHT",
    "SAFE_MARGIN_TOP",
    "SAFE_MARGIN_BOTTOM",
    "SAFE_BOUNDS_X_MIN",
    "SAFE_BOUNDS_Y_MIN",
    "SAFE_BOUNDS_X_MAX",
    "SAFE_BOUNDS_Y_MAX",
]

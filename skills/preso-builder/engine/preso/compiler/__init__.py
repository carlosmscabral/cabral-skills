"""Presentation Compiler and Google Slides CLI Integration Package."""

from preso.compiler.batch_generator import (
    BatchCompiler,
    BatchCompilerConfig,
    BatchResult,
    ChapterManifest,
    PresentationManifest,
    SlideManifest,
)
from preso.compiler.gslides_client import (
    DEFAULT_GSLIDES_BINARY,
    DEFAULT_TEMPLATE_ID,
    DEFAULT_TIMEOUT_SECONDS,
    BatchExecutionResult,
    GSlidesCLIError,
    GSlidesClient,
    GSlidesError,
    GSlidesNotFoundError,
    GSlidesTimeoutError,
)

__all__ = [
    # GSlides Client & Exceptions
    "GSlidesClient",
    "GSlidesError",
    "GSlidesNotFoundError",
    "GSlidesCLIError",
    "GSlidesTimeoutError",
    "BatchExecutionResult",
    "DEFAULT_GSLIDES_BINARY",
    "DEFAULT_TEMPLATE_ID",
    "DEFAULT_TIMEOUT_SECONDS",
    # Batch Compiler & Manifests
    "BatchCompiler",
    "BatchCompilerConfig",
    "BatchResult",
    "SlideManifest",
    "ChapterManifest",
    "PresentationManifest",
]

"""Multi-Modal Ingestion Pipeline for The AI Factory Blueprint.

Ingests heterogeneous sources (local codebases, existing Google Slides decks,
and Markdown docs/notes) and maps them into structured PresentationSpec models.
"""

from preso.ingest.codebase import (
    CodeSymbol,
    CodebaseIngestor,
    CodebaseSummary,
)
from preso.ingest.markdown import (
    MarkdownIngestor,
    RawSection,
)
from preso.ingest.slides import (
    SlidesIngestor,
)

__all__ = [
    "CodebaseIngestor",
    "CodebaseSummary",
    "CodeSymbol",
    "SlidesIngestor",
    "MarkdownIngestor",
    "RawSection",
]

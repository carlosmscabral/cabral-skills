"""Structured Blueprint Specification Framework for preso_spec.yaml."""

from preso.spec.models import (
    CardSpec,
    ChapterSpec,
    ChecklistSpec,
    CodeBlockSpec,
    HeroMetricSpec,
    LadderStepSpec,
    MetadataSpec,
    MetricSpec,
    PresentationSpec,
    PrincipleSpec,
    QuadrantSpec,
    SlideSpec,
    StepSpec,
    TakeawaySpec,
    TerminalSpec,
)
from preso.spec.scaffolder import SpecScaffolder
from preso.spec.validator import (
    ARCHETYPE_ALIASES,
    CANONICAL_ARCHETYPES,
    SpecValidator,
    ValidationResult,
)

__all__ = [
    # Models
    "MetadataSpec",
    "CardSpec",
    "CodeBlockSpec",
    "TerminalSpec",
    "HeroMetricSpec",
    "MetricSpec",
    "LadderStepSpec",
    "StepSpec",
    "QuadrantSpec",
    "ChecklistSpec",
    "PrincipleSpec",
    "TakeawaySpec",
    "SlideSpec",
    "ChapterSpec",
    "PresentationSpec",
    # Validator
    "SpecValidator",
    "ValidationResult",
    "CANONICAL_ARCHETYPES",
    "ARCHETYPE_ALIASES",
    # Scaffolder
    "SpecScaffolder",
]

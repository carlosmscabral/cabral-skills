"""Presentation Specification Scaffolder and Template Generator.

Provides the `SpecScaffolder` engine to generate production-ready, validated
`preso_spec.yaml` manifests from minimal user inputs or domain presets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional, Union

import yaml

from preso.spec.models import (
    CardSpec,
    ChapterSpec,
    ChecklistSpec,
    CodeBlockSpec,
    HeroMetricSpec,
    LadderStepSpec,
    MetadataSpec,
    PresentationSpec,
    PrincipleSpec,
    QuadrantSpec,
    SlideSpec,
    TakeawaySpec,
)


class SpecScaffolder:
    """Generates structured presentation specifications from prompts, outlines, or presets."""

    DEFAULT_TEMPLATE_ID = "1FJ4wCMDlI1zW3XCbIXXn-ejOOjq5iQ1Mit_9MuGnO-U"

    @classmethod
    def scaffold_default(cls) -> PresentationSpec:
        """Returns the default AI Factory Blueprint presentation specification."""
        return cls.scaffold_preset("ai_factory")

    @classmethod
    def scaffold(
        cls,
        title: str = "The AI Factory Blueprint",
        subtitle: str = "Deterministic Engineering for the Agentic Era",
        template_id: str = DEFAULT_TEMPLATE_ID,
        target_audience: str = "Executive Leadership & Senior Staff Engineers",
        core_thesis: str = "Move from manual hand-prompting to deterministic agentic manufacturing pipelines.",
        preset: str = "ai_factory",
        output_path: Optional[Union[str, Path]] = None,
    ) -> PresentationSpec:
        """Scaffolds a complete PresentationSpec customized with given parameters.

        Args:
            title: Presentation title.
            subtitle: Presentation subtitle.
            template_id: Master Google Slides template deck ID.
            target_audience: Intended audience.
            core_thesis: Primary thesis statement.
            preset: Preset blueprint structure ('ai_factory', 'executive_briefing', 'product_launch', 'minimal').
            output_path: Optional file path to write generated YAML manifest.

        Returns:
            Instantiated PresentationSpec.
        """
        spec = cls.scaffold_preset(
            preset_name=preset,
            title=title,
            subtitle=subtitle,
            template_id=template_id,
            target_audience=target_audience,
            core_thesis=core_thesis,
        )

        if output_path:
            cls.save_to_yaml(spec, output_path)

        return spec

    @classmethod
    def scaffold_preset(
        cls,
        preset_name: str = "ai_factory",
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        template_id: str = DEFAULT_TEMPLATE_ID,
        target_audience: Optional[str] = None,
        core_thesis: Optional[str] = None,
    ) -> PresentationSpec:
        """Generates a PresentationSpec based on a named archetype preset."""
        clean_preset = preset_name.lower().replace("-", "_").strip()

        if clean_preset in ("ai_factory", "enterprise_architecture", "full"):
            return cls._build_ai_factory_preset(
                title=title or "The AI Factory Blueprint",
                subtitle=subtitle or "Deterministic Engineering for the Agentic Era",
                template_id=template_id,
                target_audience=target_audience or "Executive Leadership & Senior Staff Engineers",
                core_thesis=core_thesis or "Move from manual hand-prompting to deterministic agentic manufacturing pipelines.",
            )

        elif clean_preset in ("executive_briefing", "executive", "briefing"):
            return cls._build_executive_briefing_preset(
                title=title or "Executive Strategy Briefing",
                subtitle=subtitle or "Accelerating Engineering Velocity with AI Factories",
                template_id=template_id,
                target_audience=target_audience or "VP of Engineering & Business Leaders",
                core_thesis=core_thesis or "High-performing teams replace prompt guessing with verified automation harnesses.",
            )

        elif clean_preset in ("product_launch", "launch", "tech_demo"):
            return cls._build_product_launch_preset(
                title=title or "Platform Next: AI Architecture",
                subtitle=subtitle or "Production Release & Technical Deep Dive",
                template_id=template_id,
                target_audience=target_audience or "Engineering Teams & Technical Customers",
                core_thesis=core_thesis or "Delivering 10x developer leverage through automated verified workflows.",
            )

        elif clean_preset in ("minimal", "starter"):
            return cls._build_minimal_preset(
                title=title or "Blueprint Presentation",
                subtitle=subtitle or "Executive Overview",
                template_id=template_id,
                target_audience=target_audience or "General Engineering Audience",
                core_thesis=core_thesis or "Structured presentation blueprint.",
            )

        else:
            # Default fallback to AI Factory
            return cls._build_ai_factory_preset(
                title=title or "The AI Factory Blueprint",
                subtitle=subtitle or "Deterministic Engineering for the Agentic Era",
                template_id=template_id,
                target_audience=target_audience or "Executive Leadership & Senior Staff Engineers",
                core_thesis=core_thesis or "Move from manual hand-prompting to deterministic agentic manufacturing pipelines.",
            )

    @classmethod
    def save_to_yaml(cls, spec: PresentationSpec, path: Union[str, Path]) -> str:
        """Serializes spec to YAML with helpful header comments."""
        yaml_content = spec.to_yaml()
        header = (
            "# =============================================================================\n"
            "# AI FACTORY BLUEPRINT PRESENTATION SPECIFICATION (preso_spec.yaml)\n"
            "# =============================================================================\n"
            "# Character Budgets & Constraints:\n"
            "#   - Slide Title: <= 60 chars | Subtitle: <= 120 chars | Kicker: <= 30 chars\n"
            "#   - Card Title: <= 35 chars  | Bullet: <= 90 chars (max 4 bullets/card)\n"
            "#   - Code: <= 16 lines        | Hero Metric Stat: <= 12 chars\n"
            "#   - Speaker Notes: Non-empty, >= 15 characters (required for every slide)\n"
            "# Archetypes:\n"
            "#   1. chapter_divider    2. split_cards      3. code_terminal\n"
            "#   4. hero_metrics       5. ladder_hierarchy 6. executive_grid\n"
            "#   7. dodont_checklist   8. actionable_takeaways\n"
            "# =============================================================================\n\n"
        )
        full_text = header + yaml_content
        Path(path).write_text(full_text, encoding="utf-8")
        return full_text

    # -------------------------------------------------------------------------
    # Preset Generators
    # -------------------------------------------------------------------------

    @classmethod
    def _build_ai_factory_preset(
        cls,
        title: str,
        subtitle: str,
        template_id: str,
        target_audience: str,
        core_thesis: str,
    ) -> PresentationSpec:
        """Builds a rich 3-chapter, 10-slide deck covering all 8 Blueprint archetypes."""
        meta = MetadataSpec(
            title=title,
            subtitle=subtitle,
            template_id=template_id,
            target_audience=target_audience,
            core_thesis=core_thesis,
            theme={
                "palette": "blueprint",
                "primary_color": "#1E2761",
                "accent_color": "#1A73E8",
                "dark_background": "#1E2761",
                "light_background": "#FFFFFF",
                "card_background": "#F8F9FA",
            },
        )

        ch1_slides = [
            SlideSpec(
                archetype="chapter_divider",
                title="Foundation & Architecture",
                subtitle="From isolated prompts to systematic engineering",
                kicker="CHAPTER",
                chapter_number=1,
                notes="Welcome everyone. Today we are exploring the paradigm shift from ad-hoc prompting to deterministic agentic manufacturing pipelines.",
            ),
            SlideSpec(
                archetype="split_cards",
                title="Two Paradigms of Agent Development",
                subtitle="Comparing ad-hoc prompting with deterministic pipelines",
                kicker="PARADIGM COMPARISON",
                cards=[
                    CardSpec(
                        title="Ad-Hoc Prompting",
                        kicker="TRADITIONAL",
                        bullets=[
                            "Manual copy-pasting of context into web chat",
                            "Unpredictable outputs and silent regressions",
                            "Zero test harness or automated verification",
                        ],
                        theme="#1A73E8",
                    ),
                    CardSpec(
                        title="Deterministic Harness",
                        kicker="AI FACTORY",
                        bullets=[
                            "Automated context injection via file mounts",
                            "Enforcing hooks that block commits on failure",
                            "Adversarial evaluator sub-agents grade runs",
                        ],
                        theme="#1E8E3E",
                    ),
                ],
                notes="On the left is how teams start: manual trial and error. On the right is the AI Factory model with structured specs and automated verification loops.",
            ),
            SlideSpec(
                archetype="code_terminal",
                title="The Enforcing Ratchet in Practice",
                subtitle="Make failures impossible to repeat with pre-commit hooks",
                kicker="CODE & RATCHETS",
                terminals=[
                    CodeBlockSpec(
                        filename=".agent/hooks/pre-commit",
                        code="#!/bin/sh\ntypecheck && lint\ntest --bail || exit 1   # red = blocked\n\n# Enforce zero regressions\necho '✓ Validation passed'",
                        language="bash",
                        status="do",
                        badge_text="✓ DO: RATCHETED",
                    ),
                    CodeBlockSpec(
                        filename="scripts/run_and_hope.sh",
                        code="#!/bin/sh\n# Blindly retry prompt\npython run_agent.py \\\n  --retry 10 \\\n  --ignore-errors\n# Regressions recur silently",
                        language="bash",
                        status="dont",
                        badge_text="✗ DON'T: HOPE-BASED",
                    ),
                ],
                notes="Here is the concrete implementation of a ratchet. The agent cannot commit code unless the entire typecheck and test suite passes cleanly.",
            ),
        ]

        ch2_slides = [
            SlideSpec(
                archetype="chapter_divider",
                title="Economics & Engineering Disciplines",
                subtitle="Why strong harnesses yield 10x ROI over naked models",
                kicker="CHAPTER",
                chapter_number=2,
                notes="In this chapter we look at the economics of agentic systems and the four disciplines required to scale reliably.",
            ),
            SlideSpec(
                archetype="hero_metrics",
                title="The Economics of Skipping Basics",
                subtitle="Harness investment vs token waste in real experiments",
                kicker="ECONOMIC ANALYSIS",
                metrics=[
                    HeroMetricSpec(
                        value="$9",
                        unit="· 20 min",
                        label="SOLO MODEL",
                        delta="-85%",
                        delta_type="negative",
                        description="Broken mechanics, failed physics, wasted UI. A toy you throw away.",
                        accent_color="#D93025",
                    ),
                    HeroMetricSpec(
                        value="$200",
                        unit="· 6 hours",
                        label="FULL HARNESS",
                        delta="+10x",
                        delta_type="positive",
                        description="Functional game engine, rich editors, verified integrations. Shippable.",
                        is_hero=True,
                        accent_color="#1E8E3E",
                    ),
                ],
                notes="Look at these economics. A solo model costs 9 dollars but yields a toy. A 200-dollar full harness yields shippable, enterprise-grade software.",
            ),
            SlideSpec(
                archetype="ladder_hierarchy",
                title="The Four Disciplines of Agentic Systems",
                subtitle="Master each rung sequentially before adopting frameworks",
                kicker="DISCIPLINE LADDER",
                steps=[
                    LadderStepSpec(
                        step_number=1,
                        title="Prompt Engineering",
                        description="GCCD framework: Goal, Context, Constraints, Done-when criteria.",
                        badge="RUNG 01",
                    ),
                    LadderStepSpec(
                        step_number=2,
                        title="Context Architecture",
                        description="Compact, offload, reset, and persist memory to external files.",
                        badge="RUNG 02",
                    ),
                    LadderStepSpec(
                        step_number=3,
                        title="Harness & Ratchet",
                        description="Equip tools, sandboxes, enforcing hooks, and adversarial evaluators.",
                        badge="RUNG 03",
                    ),
                    LadderStepSpec(
                        step_number=4,
                        title="Loop Engineering",
                        description="Automate prompters on schedules with humans in the review seat.",
                        badge="RUNG 04",
                    ),
                ],
                notes="We structure the discipline into a 4-step ladder: Prompt, Context, Harness, and Loop. Each rung builds upon the last.",
            ),
            SlideSpec(
                archetype="executive_grid",
                title="The AI Factory Blueprint in One Line Each",
                subtitle="Summary of core operational pillars",
                kicker="EXECUTIVE SUMMARY",
                quadrants=[
                    QuadrantSpec(
                        number="01",
                        title="Prompt",
                        narrative="Guide intent with GCCD: Goal, Context, Constraints, Done-when criteria.",
                    ),
                    QuadrantSpec(
                        number="02",
                        title="Context",
                        narrative="Curate the window: compact, offload, reset, persist state to files.",
                    ),
                    QuadrantSpec(
                        number="03",
                        title="Harness",
                        narrative="Give it state, tools, hooks, and an adversarial evaluator.",
                    ),
                    QuadrantSpec(
                        number="04",
                        title="Loop",
                        narrative="Automate the prompter; keep yourself in the review seat.",
                    ),
                ],
                notes="Here is the executive 4-quadrant summary. Prompt, Context, Harness, and Loop. Each pillar must be solid.",
            ),
        ]

        ch3_slides = [
            SlideSpec(
                archetype="chapter_divider",
                title="Operational Excellence & Next Steps",
                subtitle="Actionable guidance for adopting agentic workflows",
                kicker="CHAPTER",
                chapter_number=3,
                notes="In our final chapter, we cover operational best practices and key action items for technical leadership.",
            ),
            SlideSpec(
                archetype="dodont_checklist",
                title="Agentic Tool Adoption: Do's and Don'ts",
                subtitle="Operationalize what you learned rather than bypassing disciplines",
                kicker="BEST PRACTICES",
                checklist=ChecklistSpec(
                    do_title="BLUEPRINT STANDARD (DO)",
                    dont_title="ANTI-PATTERN (DON'T)",
                    do_items=[
                        "Define verifiable 'done-when' criteria before runs",
                        "Isolate parallel tasks in separate worktrees",
                        "Employ independent checker sub-agents to grade work",
                    ],
                    dont_items=[
                        "Fanning out vague requirements to 20 agents",
                        "Letting loops merge code directly with no human gate",
                        "Relying on model retries instead of ratcheted hooks",
                    ],
                    takeaway="Tools amplify whatever you bring them: mastery or waste.",
                ),
                notes="Review our do and don't checklist when adopting agentic tooling across engineering teams.",
            ),
            SlideSpec(
                archetype="actionable_takeaways",
                title="Build the Factory. Learn the Floor First.",
                subtitle="Key takeaways and next steps for engineering leaders",
                kicker="ACTION PLAN",
                takeaway=TakeawaySpec(
                    thesis="Engineering shifts from a keystroke activity to a judgment activity.",
                    principles=[
                        PrincipleSpec(
                            number=1,
                            title="Decompose Problems",
                            description="Break complex work into scoped subtasks with testable success criteria.",
                        ),
                        PrincipleSpec(
                            number=2,
                            title="Enforce Quality Gates",
                            description="Catch errors at the harness layer to eliminate recurring regressions.",
                        ),
                        PrincipleSpec(
                            number=3,
                            title="Automate with Human Gates",
                            description="Design automated loops with review gates at pull-request boundaries.",
                        ),
                    ],
                    roadmap_title="30-DAY EXECUTION ROADMAP",
                    roadmap_items=[
                        "Week 1: Audit prompt specs & done-when gates",
                        "Week 2: Implement pre-commit ratchet hooks",
                        "Week 3: Stand up adversarial QA checker agent",
                        "Week 4: Roll out automated build pipeline",
                    ],
                    cta_text="START WITH RUNG 01 TODAY →",
                    contact_info="go/ai-factory-blueprint · feedback@google.com",
                ),
                notes="To wrap up: master the disciplines sequentially. Build the factory, but ensure your teams understand the floor first.",
            ),
        ]

        chapters = [
            ChapterSpec(number=1, title="Foundation & Architecture", subtitle="From isolated prompts to systematic engineering", slides=ch1_slides),
            ChapterSpec(number=2, title="Economics & Engineering Disciplines", subtitle="Why strong harnesses yield 10x ROI over naked models", slides=ch2_slides),
            ChapterSpec(number=3, title="Operational Excellence & Next Steps", subtitle="Actionable guidance for adopting agentic workflows", slides=ch3_slides),
        ]

        return PresentationSpec(version="1.0", metadata=meta, chapters=chapters)

    @classmethod
    def _build_executive_briefing_preset(
        cls,
        title: str,
        subtitle: str,
        template_id: str,
        target_audience: str,
        core_thesis: str,
    ) -> PresentationSpec:
        """Builds a condensed 5-slide executive briefing deck."""
        meta = MetadataSpec(
            title=title,
            subtitle=subtitle,
            template_id=template_id,
            target_audience=target_audience,
            core_thesis=core_thesis,
        )

        slides = [
            SlideSpec(
                archetype="chapter_divider",
                title=title,
                subtitle=subtitle,
                chapter_number=1,
                notes="Welcome leaders. Today we present our executive roadmap for automated presentation engineering.",
            ),
            SlideSpec(
                archetype="split_cards",
                title="Strategic Shift: Manual vs Automated",
                subtitle="Transitioning to automated executive artifact generation",
                kicker="STRATEGY",
                cards=[
                    CardSpec(
                        title="Manual Deck Assembly",
                        kicker="LEGACY",
                        bullets=[
                            "4-8 hours spent manually arranging shapes and fonts",
                            "Inconsistent typography and WCAG contrast failures",
                            "Stale figures disconnected from codebases",
                        ],
                    ),
                    CardSpec(
                        title="Automated AI Factory",
                        kicker="MODERN",
                        bullets=[
                            "Single-click generation from declarative YAML specs",
                            "Strict WCAG AA contrast and zero text overflow",
                            "Direct AST synchronization with repository source",
                        ],
                    ),
                ],
                notes="Comparing the high time cost of manual slide preparation against automated single-pass compilation.",
            ),
            SlideSpec(
                archetype="hero_metrics",
                title="Operational Velocity Gains",
                subtitle="Measured productivity improvements across pilot teams",
                kicker="METRICS",
                metrics=[
                    HeroMetricSpec(
                        value="95%",
                        unit="time saved",
                        label="DECK GENERATION",
                        delta="-7.5 hrs",
                        description="Reduction in time required to produce executive-ready decks.",
                    ),
                    HeroMetricSpec(
                        value="100%",
                        unit="compliance",
                        label="BRAND FIDELITY",
                        delta="0 errors",
                        description="Zero typography, contrast, or canvas bounding-box violations.",
                        is_hero=True,
                    ),
                ],
                notes="These metrics reflect pilot results across engineering divisions using automated slide compilation.",
            ),
            SlideSpec(
                archetype="executive_grid",
                title="Executive Overview Pillars",
                subtitle="The four cornerstones of scalable presentation generation",
                kicker="PILLARS",
                quadrants=[
                    QuadrantSpec(number="01", title="Declarative Specs", narrative="Manage presentation content in version-controlled YAML."),
                    QuadrantSpec(number="02", title="Design Tokens", narrative="Enforce Google Sans typography and Blueprint palettes."),
                    QuadrantSpec(number="03", title="Single-Pass Batch", narrative="Atomic slide creation via gslides batch operations."),
                    QuadrantSpec(number="04", title="Multimodal QA", narrative="Automated visual verification on exported thumbnails."),
                ],
                notes="Each of the four pillars guarantees consistent quality without manual designer intervention.",
            ),
            SlideSpec(
                archetype="actionable_takeaways",
                title="Executive Next Steps",
                subtitle="Timeline and recommendations for organization rollout",
                kicker="ROADMAP",
                takeaway=TakeawaySpec(
                    thesis="Automating slide creation frees senior engineers to focus on architecture.",
                    principles=[
                        PrincipleSpec(number=1, title="Adopt Spec Standard", description="Standardize team presentation decks on preso_spec.yaml."),
                        PrincipleSpec(number=2, title="Integrate CI/CD", description="Generate architecture update decks automatically on release."),
                    ],
                    roadmap_items=[
                        "Phase 1: Pilot team onboarding and training",
                        "Phase 2: CI/CD repo doc generator integration",
                        "Phase 3: Organization-wide standard rollout",
                    ],
                    cta_text="SCHEDULE PILOT DEMO →",
                ),
                notes="Our proposed rollout plan transitions teams smoothly over the next quarter.",
            ),
        ]

        chapters = [ChapterSpec(number=1, title="Executive Strategy", subtitle=subtitle, slides=slides)]
        return PresentationSpec(version="1.0", metadata=meta, chapters=chapters)

    @classmethod
    def _build_product_launch_preset(
        cls,
        title: str,
        subtitle: str,
        template_id: str,
        target_audience: str,
        core_thesis: str,
    ) -> PresentationSpec:
        """Builds a technical product release presentation."""
        meta = MetadataSpec(
            title=title,
            subtitle=subtitle,
            template_id=template_id,
            target_audience=target_audience,
            core_thesis=core_thesis,
        )

        slides = [
            SlideSpec(
                archetype="chapter_divider",
                title=title,
                subtitle=subtitle,
                chapter_number=1,
                notes="Welcome to the product launch presentation. Today we walk through the architecture, benchmarks, and rollout.",
            ),
            SlideSpec(
                archetype="split_cards",
                title="Architecture & Key Features",
                subtitle="Core technical capabilities of the new platform",
                kicker="CAPABILITIES",
                cards=[
                    CardSpec(
                        title="Multi-Modal Ingest",
                        kicker="INGESTION",
                        bullets=[
                            "AST scanning of Python, Go, and TypeScript",
                            "Parsing legacy Google Slides and markdown docs",
                            "Auto-detection of architectural archetypes",
                        ],
                    ),
                    CardSpec(
                        title="Batch Compiler",
                        kicker="COMPILER",
                        bullets=[
                            "Single-pass atomic gslides batch payload generation",
                            "Deterministic placeholder ID resolution",
                            "Automated speaker notes attachment",
                        ],
                    ),
                ],
                notes="The architecture separates multi-modal source ingestion from deterministic batch payload compilation.",
            ),
            SlideSpec(
                archetype="hero_metrics",
                title="Performance & Scale Benchmarks",
                subtitle="High-throughput batch compilation and low latency",
                kicker="BENCHMARKS",
                metrics=[
                    HeroMetricSpec(
                        value="<50ms",
                        unit="per slide",
                        label="COMPILE TIME",
                        delta="-90%",
                        description="Ultra-fast single-pass AST parsing and batch generation.",
                    ),
                    HeroMetricSpec(
                        value="100%",
                        unit="deterministic",
                        label="VERIFIED ACCURACY",
                        delta="0 drift",
                        description="Deterministic geometry and WCAG AA contrast compliance.",
                        is_hero=True,
                    ),
                ],
                notes="Our performance benchmarks demonstrate sub-50 millisecond compilation and 100 percent deterministic geometry.",
            ),
            SlideSpec(
                archetype="code_terminal",
                title="Unified CLI Interface",
                subtitle="Simple, declarative developer workflow",
                kicker="CLI WORKFLOW",
                terminals=[
                    CodeBlockSpec(
                        filename="cli_example.sh",
                        code="# 1. Ingest repo and scaffold spec\npreso spec --repo . --output spec.yaml\n\n# 2. Build deck via gslides\npreso build --spec spec.yaml",
                        language="bash",
                        status="do",
                        badge_text="✓ PRODUCTION READY",
                    )
                ],
                notes="Developers can scaffold, inspect, build, and preview presentations entirely from the terminal.",
            ),
            SlideSpec(
                archetype="ladder_hierarchy",
                title="Release & Rollout Schedule",
                subtitle="Four-stage graduated deployment strategy",
                kicker="TIMELINE",
                steps=[
                    LadderStepSpec(step_number=1, title="Internal Alpha", description="Testing with core infra teams.", badge="STAGE 1"),
                    LadderStepSpec(step_number=2, title="Beta Program", description="Expanded access for 50 early teams.", badge="STAGE 2"),
                    LadderStepSpec(step_number=3, title="General Availability", description="Full release to all engineering orgs.", badge="STAGE 3"),
                    LadderStepSpec(step_number=4, title="Ecosystem Skills", description="Integration with agent workflows.", badge="STAGE 4"),
                ],
                notes="Our four-stage rollout ensures stability and reliability before general availability.",
            ),
            SlideSpec(
                archetype="actionable_takeaways",
                title="Get Started with Platform Next",
                subtitle="Resources and documentation links",
                kicker="NEXT STEPS",
                takeaway=TakeawaySpec(
                    thesis="The easiest way to build executive slides from codebases.",
                    principles=[
                        PrincipleSpec(number=1, title="Clone Starter Repo", description="Run git clone and install the CLI tool locally."),
                        PrincipleSpec(number=2, title="Run First Build", description="Execute preso build --spec sample_spec.yaml."),
                    ],
                    roadmap_items=[
                        "Step 1: Install preso CLI tool",
                        "Step 2: Authenticate with Google Slides",
                        "Step 3: Generate first custom deck",
                    ],
                    cta_text="EXPLORE DOCS TODAY →",
                ),
                notes="Thank you everyone. Please try the CLI and join our feedback channel for questions.",
            ),
        ]

        chapters = [ChapterSpec(number=1, title="Platform Release", subtitle=subtitle, slides=slides)]
        return PresentationSpec(version="1.0", metadata=meta, chapters=chapters)

    @classmethod
    def _build_minimal_preset(
        cls,
        title: str,
        subtitle: str,
        template_id: str,
        target_audience: str,
        core_thesis: str,
    ) -> PresentationSpec:
        """Builds a minimal 2-slide presentation."""
        meta = MetadataSpec(
            title=title,
            subtitle=subtitle,
            template_id=template_id,
            target_audience=target_audience,
            core_thesis=core_thesis,
        )

        slides = [
            SlideSpec(
                archetype="chapter_divider",
                title=title,
                subtitle=subtitle,
                chapter_number=1,
                notes="Welcome to the presentation. Here is our executive starter deck.",
            ),
            SlideSpec(
                archetype="split_cards",
                title="Overview & Key Highlights",
                subtitle="Summary of primary objectives and milestones",
                kicker="OVERVIEW",
                cards=[
                    CardSpec(
                        title="Objective Alpha",
                        kicker="PRIORITY 1",
                        bullets=[
                            "Establish automated deck generation pipeline",
                            "Validate design token fidelity and layout",
                        ],
                    ),
                    CardSpec(
                        title="Objective Beta",
                        kicker="PRIORITY 2",
                        bullets=[
                            "Enable multi-modal codebase ingestion",
                            "Deploy multimodal visual QA verification",
                        ],
                    ),
                ],
                notes="This slide summarizes our two core strategic objectives for the quarter.",
            ),
        ]

        chapters = [ChapterSpec(number=1, title="Executive Summary", subtitle=subtitle, slides=slides)]
        return PresentationSpec(version="1.0", metadata=meta, chapters=chapters)

---
name: architecture-research-blueprint
description: >
  Use this skill when researching, designing, or evaluating software, cloud, and Google Cloud
  Platform architectures. Orchestrates parallel specialist subagents, independent adversarial
  reviews across the 6 Well-Architected pillars, multi-tier executive consolidation, and
  interactive web reports with zero-defect Mermaid.js and fullscreen Zoom/Pan lightboxes.
---

# Architecture Research & Interactive Blueprint Skill

This skill defines a deterministic, multi-agent workflow for conducting deep-dive architectural investigations, evaluating complex cloud/software trade-offs, auditing resilience and security postures, and publishing publication-grade interactive web reports.

---

## When to Use This Skill

### Positive Triggers (Use this skill when:)
- Conducting exhaustive architectural investigations across complex software, distributed systems, or Google Cloud topologies.
- Evaluating multi-dimensional trade-offs requiring parallel specialized research across infrastructure layers (Edge, Compute, Data, Security, FinOps).
- Performing independent adversarial architectural reviews (Security/Zero-Trust, Reliability/Fault Tolerance, FinOps/Cost, Performance, Operational Excellence).
- Generating structured multi-tier deliverables (Foundations → Domain Deep Dives → Master Decision Matrix/ADRs → Executive Slides → Interactive Web Report).

---

## Orchestration & Delegation Contract

To guarantee context isolation, high grounding, and unbiased adversarial reviews, this skill uses **hierarchical multi-agent delegation**:

```
                               ROOT ORCHESTRATOR
                                      │
           ┌──────────────────────────┴──────────────────────────┐
           ▼                                                     ▼
  PHASE 1: SPECIALISTS (Parallel)                       PHASE 2: QUALITY GATE & REVIEWERS
  ├── Domain 1 Specialist                               Stage 2.1: Grounding/Depth Gate
  ├── Domain 2 Specialist                                        │ (Pass / In-Place Fix)
  ├── Domain 3 Specialist                                        ▼
  └── Domain 4 Specialist                               Stage 2.2: Adversarial Reviewers (Parallel)
                                                        ├── Reviewer A (Security & Privacy)
                                                        ├── Reviewer B (Reliability & Performance)
                                                        └── Reviewer C (FinOps & System Design)
```

### Delegation Rules for AI Coding Assistants:
1. **Google Antigravity (Primary):**
   - Call `define_subagent` with `name: "architecture_specialist"` and `enable_write_tools: true` to equip subagents with research and file writing capabilities.
   - Call `invoke_subagent` in batch (`Subagents: [...]`) with `TypeName: "architecture_specialist"`.
   - Subagents write their respective files (`01_...md`, `reviews/...md`) directly in parallel and notify the orchestrator when finished.
2. **Generic AI Coding Environments (Portability Fallback):**
   - If the host environment provides a subagent or task tool (e.g., Claude Code `Task`/`Agent`, Roo/Cline sub-tasks), dispatch tasks through that native mechanism.
   - If the host environment is strictly single-threaded without subagent tools, the agent must execute phases sequentially, completing and verifying each domain file before moving to the next.

---

## The 4-Phase Execution Lifecycle

| Phase | Core Objective | Key Deliverables |
|---|---|---|
| **Phase 1: Parallel Specialist Research** | Spawn 4–6 domain subagents concurrently to explore orthogonal problem spaces. | Standalone domain reports with verified official citations (`https://cloud.google.com/...`). |
| **Phase 2: Independent Adversarial Review & Quality Gate** | **Stage 2.1:** Audit grounding/depth per report → **FIX gaps in place** → **Stage 2.2:** Well-Architected 6-pillar audit. | Pre-flight audit, remediated specialist reports, and formal critique files in `reviews/`. |
| **Phase 3: Multi-Tier Consolidation** | Synthesize domain findings, remediations, and decision records into master artifacts. | `00_system_context_and_foundations.md`, `01_`–`0N_` deep dives, `master_architecture.md`, and slide blueprint. |
| **Phase 4: Interactive Web Report** | Publish an interactive single-page app with Clean Engineering UI, wizards, and Mermaid lightboxes. | Standalone `web_report/` SPA (`index.html`, `styles.css`, `app.js`). |

---

## Phase 1: Parallel Specialist Subagents

> [!IMPORTANT]
> **MANDATORY SUBAGENT DEFINITION & INVOCATION (DO NOT SIMULATE IN MAIN CONTEXT):**  
> When running in Google Antigravity, you **MUST** first register the architecture specialist subagent type via `define_subagent` (with `enable_write_tools: true`), then spawn all domain specialists concurrently via `invoke_subagent`. Do NOT write domain deep-dives directly in the parent context. Subagents ensure dedicated context windows, parallel documentation research, and direct file authoring.

1. **Decompose into Orthogonal Macro-Domains:**
   Break down the problem space into 4 to 6 mutually exclusive domains. Consult [`references/domain-archetypes.md`](./references/domain-archetypes.md) for canonical blueprints (Cloud-Native Microservices, GenAI / ADK Agent Platforms, Data Mesh, Multi-Tenant SaaS, Hybrid Networking).

2. **Step 1 — Register the Subagent Type via `define_subagent` (Once):**
   ```json
   {
     "name": "architecture_specialist",
     "description": "Specialist subagent that researches cloud/software architectures with official grounding and authors domain deep-dive markdown files directly.",
     "enable_write_tools": true,
     "system_prompt": "You are a specialized Senior Cloud & Software Architect. Conduct exhaustive research with verified official documentation links (https://cloud.google.com/...), design concrete schemas/topologies, and write your assigned domain markdown report (01_...md through 0N_...md) directly using write_to_file."
   }
   ```

3. **Step 2 — Dispatch Domain Specialists Concurrently via `invoke_subagent`:**
   Launch all domain specialists in a single batch call:
   ```json
   {
     "Subagents": [
       {
         "TypeName": "architecture_specialist",
         "Role": "Domain 1 Specialist (e.g. Ingress & Routing)",
         "Prompt": "Research and author 01_domain_name.md covering... Strict requirement: Ground every technical assertion and quota limit with official vendor documentation links (https://cloud.google.com/...). Write the complete file directly using write_to_file. Include concrete configuration schemas, trade-off matrices, and clean Mermaid diagrams."
       },
       {
         "TypeName": "architecture_specialist",
         "Role": "Domain 2 Specialist (e.g. Identity & Security)",
         "Prompt": "Research and author 02_domain_name.md covering... Write the complete file directly using write_to_file."
       }
     ]
   }
   ```

---

## Phase 2: Independent Adversarial Review & Quality Gate

Adversarial review runs in two sequential stages separated by a **mandatory quality gate** (see [`references/architecture-review-pillars.md`](./references/architecture-review-pillars.md)):

### Stage 2.1: Pre-Flight Grounding & Depth Quality Gate
Rigorously audit **each prior specialist domain analysis** before initiating pillar reviews:
1. **Grounding & Veracity:** Verify that all APIs, SDK methods, service limits, and architectural claims cite official documentation (`https://cloud.google.com/...`) with zero hallucinations or deprecated assumptions.
2. **Completeness & Technical Depth:** Verify that analyses contain concrete schemas, error-handling mechanisms, failure recovery paths, and cross-domain integration contracts rather than superficial hand-waving.

> [!IMPORTANT]
> **MANDATORY QUALITY GATE & REMEDIATION LOOP:**  
> If any grounding gaps, missing citations, hallucinations, or shallow sections are discovered during Stage 2.1, **DO NOT proceed to Stage 2.2**. You must **FIX and deepen the specialist reports directly in place** first. Re-verify that all documents meet the quality bar before triggering Well-Architected reviewers.

### Stage 2.2: Well-Architected Framework Adversarial Stress-Testing

> [!IMPORTANT]
> **MANDATORY INDEPENDENT REVIEWERS (DO NOT SELF-REVIEW IN MAIN CONTEXT):**  
> Spawn Reviewers A, B, and C as distinct subagents via `invoke_subagent` with `TypeName: "architecture_specialist"`. Spawning separate subagents eliminates author confirmation bias and ensures uncompromised critique written directly to `reviews/`.

Once all specialist reports are verified, grounded, and remediated, spawn 3 parallel reviewer subagents:
- **Reviewer A (Security, Privacy & Compliance):** Audits Zero-Trust identity, least privilege, VPC-SC perimeters, CMEK, data isolation, and regulatory compliance. Writes `reviews/reviewer_a_security_compliance.md`.
- **Reviewer B (Reliability, Scalability & Performance):** Audits multi-region failover, rate limiting, connection pooling, backpressure, and latency SLAs under load. Writes `reviews/reviewer_b_reliability_performance.md`.
- **Reviewer C (FinOps, Operational Excellence & System Design):** Audits unit economics, context caching/pricing optimization, IaC reproducibility, and modular API boundaries. Writes `reviews/reviewer_c_finops_ops_design.md`.

Each reviewer writes a formal critique to `reviews/`, providing defensive architectural countermeasures to incorporate during consolidation.

---

## Phase 3: Multi-Tier Consolidation

Synthesize all findings and reviewer remediations into structured, multi-tier artifacts:
- **`00_system_context_and_foundations.md`:** Executive context, problem statement, business goals, quality attribute scenarios (ISO/IEC 25010), and technology-agnostic mental models.
- **`01_...md` to `0N_...md`:** In-depth technical domain reports incorporating reviewer remediations and grounded diagrams.
- **`master_architecture.md`:** Executive synthesis with a multidimensional decision matrix, Architectural Decision Records (ADRs), and clear selection heuristics.
- **`presentation_slides_blueprint.md`:** Structured slide-by-slide storyline for C-level and technical leadership presentations.

*Tip:* For large research initiatives with 5+ domains, consolidate incrementally (synthesize the Cross-Domain Matrix first, then author the Master Decision Record & ADRs) to optimize context efficiency.

---

## Phase 4: Interactive Web Report Application (`web_report/`)

Publish the architecture as a high-grade, interactive single-page application adhering to [`references/interactive-web-report-standards.md`](./references/interactive-web-report-standards.md):

1. **Google Cloud Clean Engineering Aesthetic (`styles.css`):**
   - HSL-tailored color tokens with seamless Dark/Light theme switching (`localStorage`).
   - Sticky sidebar navigation tracked via `IntersectionObserver`.
2. **Interactive Decision Engine (`app.js`):**
   - **Architecture Selection Wizard:** Dynamic questionnaire matching workload scale, compliance, and latency constraints to the optimal model.
   - **Sizing & TCO Calculator:** Dynamic pricing sliders with transparent cost allocation equations.
   - **Copy-to-Clipboard & Code Tabs.**
3. **Zero-Defect Mermaid & Fullscreen Zoom & Pan Modal:**
   - Individual async `mermaid.render()` with `try/catch` isolation per diagram.
   - Built-in **Lightbox Modal** with Zoom In (+), Zoom Out (-), Reset (100%), Fit-to-Screen, Mouse Drag Pan, Wheel Zoom, and Keyboard navigation (<kbd>ESC</kbd>, <kbd>+</kbd>, <kbd>-</kbd>, <kbd>0</kbd>).
   - **Automated Math Sanitization:** Run `scripts/sanitize_web_report.py` to convert all `$math$` / `$O(N)$` tokens to clean semantic HTML, backed by `autoCleanDomMath()` in `app.js`.

---

## Reference Guides & Examples

### Starter Kit & Templates
- [`examples/web-report-starter/styles.css`](./examples/web-report-starter/styles.css) — Ready-to-use Google Cloud Clean Engineering stylesheet (Dark/Light theme, tokens, responsive layout, cards, badges, and zoom lightbox).
- [`examples/web-report-starter/app.js`](./examples/web-report-starter/app.js) — Battle-tested JS engine with DOM math sanitizer, async Mermaid 10 rendering, full Zoom & Pan modal lightbox, and navigation tracking.
- [`examples/web-report-starter/index.html`](./examples/web-report-starter/index.html) — Canonical HTML template demonstrating sticky sidebar, hero banner, diagram wrappers, and pedagogical callouts.

### Scripts & Utilities
- [`scripts/sanitize_web_report.py`](./scripts/sanitize_web_report.py) — CLI utility to scan and sanitize LaTeX math notations into clean HTML across all report files.

### Deep-Dive Standards
- [`references/domain-archetypes.md`](./references/domain-archetypes.md) — 5 canonical domain decomposition archetypes (Microservices, GenAI/ADK, Data Mesh, SaaS, Hybrid).
- [`references/architecture-review-pillars.md`](./references/architecture-review-pillars.md) — Deep-dive audit checklists across the 6 Well-Architected Framework pillars.
- [`references/interactive-web-report-standards.md`](./references/interactive-web-report-standards.md) — Mandatory frontend, Mermaid, and typography quality rules.

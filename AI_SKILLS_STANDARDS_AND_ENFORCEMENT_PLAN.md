# AI Skills Standards, Best Practices & Repository Enforcement Plan (Revised)

## Executive Summary & Background

This document details the standards, security controls, developer ergonomics, and concrete enforcement phases for **AI Agent Skills** across standalone skills (`skills/`) and plugin-bundled skills (`plugins/adk-developer/skills/`) in `carlosmscabral/cabral-skills`.

The plan incorporates a comprehensive multi-agent evaluation by a **Security & Governance Architect** and a **Developer Experience & Pragmatism Lead**, eliminating internal contradictions, hardening supply-chain/network sandbox controls, and reducing developer friction.

---

## Research Synthesis & Core Standards

```
+-----------------------------------------------------------------------------------+
|                            CORE PILLARS OF AI SKILL STANDARDS                     |
+--------------------------+--------------------------+-----------------------------+
| 1. SCHEMA & LAYOUT       | 2. CONTEXT OPTIMIZATION  | 3. SECURITY & SANDBOXING    |
| • agentskills.io layout  | • Progressive Disclosure | • Offline-first execution   |
| • Lean SKILL.md (<10KB)  | • Tier 1 Discovery index | • Explicit opt-in net egress|
| • Positive/Negative      | • Lazy reference loading | • Secret masking & Prompt   |
|   trigger sections       | • PEP 723 for 3rd-party  |   Injection scanning        |
+--------------------------+--------------------------+-----------------------------+
| 4. VENDOR PROVENANCE     | 5. DEVELOPER ERGONOMICS & CI                            |
| • SHA-256 tree digests in vendored.json             | • `validate_repo.py --fix` auto-repair |
| • Upstream patch mechanism (`scripts/patches/`)    | • Graceful script degradation & CI gate|
+-----------------------------------------------------------------------------------+
```

### 1. External Standards (`agentskills.io`, MCP, PEP 723)
* **Directory Layout**: Kebab-case directory naming with a root `SKILL.md`, optional `scripts/`, `references/`, and `assets/`.
* **Lean Schema Specification**:
  * **Standalone Skills (`skills/`)**: Mandatory YAML frontmatter requires only `name` and `description` per open `agentskills.io` specification. Nested `metadata` blocks (`author`, `version`, `category`, `license`) are optional.
  * **Plugin Skills (`plugins/<plugin>/skills/`)**: Full frontmatter including plugin manifest metadata.
* **Progressive Disclosure Architecture**:
  * **Tier 1 (Discovery)**: `name` and `description` (~100 tokens/skill) injected into active agent context.
  * **Tier 2 (Activation)**: Full `SKILL.md` body loaded on intent match.
  * **Tier 3 (Execution)**: Auxiliary markdown references (`references/*.md`) or helper scripts (`scripts/*.py`) executed lazily.
* **Inline Dependencies**: PEP 723 metadata headers reserved for Python scripts requiring third-party PyPI libraries.

### 2. Google Internal Best Practices & ADK Conventions
* **Skill Defragmentation**: Physical proximity for related rules and constraints.
* **Always-On Rules vs Ephemeral Skills**: Reserve `AGENTS.md` and plugin `rules/*.md` for global system constraints (Priority 0). Use `SKILL.md` exclusively for procedural domain tasks.
* **Disambiguated Triggers**: Explicit `## When to Use This Skill` sections with positive and negative triggers to eliminate subagent loop risks.

### 3. Adversarial Security & Risk Mitigation
* **Prompt Injection Defense**: Frontmatter `description` fields and AST-generated workspace artifacts (e.g. `migration_manifest.json`) undergo injection scanning to prevent context hijacking.
* **Vendor Integrity Pinning**: `vendored.json` tracks SHA-256 tree digests for all vendored files, enforced by CI to detect in-tree tampering.

### 4. Developer Experience & Pragmatism (DX)
* **Automated Remediation**: `validate_repo.py --fix` automatically repairs permissions (`chmod +x`), cleans bytecode artifacts (`__pycache__`), and formats frontmatter defaults.
* **Graceful Script Degradation**: Local verification scripts check for required local binaries (e.g. `mmdc`) and skip/warn gracefully rather than hard-crashing when developer dependencies are absent.
* **Pragmatic Patch Layer**: Upstream sync (`scripts/vendor-agents-cli.sh`) supports applying local patches (`scripts/patches/`) post-sync, allowing urgent local fixes without breaking upstream provenance tracking.

---

## Proposed Enforcement Roadmap

---

### Phase 1: Repository Hygiene

#### [DELETE] `__pycache__` & Bytecode Artifacts
- Purge checked-in Python bytecode (`*.pyc`) and `__pycache__` directories under `skills/aws-lambda-*/scripts/`.
- Add `__pycache__/` and `*.pyc` to `.gitignore`.

---

### Phase 2: Schema, Trigger Disambiguation & Patch Support

#### [MODIFY] Authored Plugin & Standalone `SKILL.md` Files:
- [google-agents-cli-adk-frontend/SKILL.md](file:///usr/local/google/home/carloscabral/cabral-skills/plugins/adk-developer/skills/google-agents-cli-adk-frontend/SKILL.md)
- [google-agents-cli-adk-auth/SKILL.md](file:///usr/local/google/home/carloscabral/cabral-skills/plugins/adk-developer/skills/google-agents-cli-adk-auth/SKILL.md)
- [aws-lambda-fleet-to-cloud-run/SKILL.md](file:///usr/local/google/home/carloscabral/cabral-skills/skills/aws-lambda-fleet-to-cloud-run/SKILL.md)
- [aws-lambda-to-cloud-run-migration/SKILL.md](file:///usr/local/google/home/carloscabral/cabral-skills/skills/aws-lambda-to-cloud-run-migration/SKILL.md)

*Add explicit `## When to Use This Skill` sections with positive and negative triggers to disambiguate fleet-wide analysis from individual function migrations.*

#### [MODIFY] [vendor-agents-cli.sh](file:///usr/local/google/home/carloscabral/cabral-skills/scripts/vendor-agents-cli.sh)
- Compute and store file SHA-256 tree digests in `vendored.json`.
- Add support for applying local patches from `scripts/patches/google-agents-cli/` post-sync.

---

### Phase 3: Repository Validator CLI (`scripts/validate_repo.py`)

#### [NEW] [validate_repo.py](file:///usr/local/google/home/carloscabral/cabral-skills/scripts/validate_repo.py)
- Create a Python CLI validator with `--fix` auto-remediation mode.
- Automated Checks:
  1. **Manifest Parity**: `plugin.json` lists existing skills under `plugins/<name>/skills/`.
  2. **Frontmatter & Injection Check**: Validates required YAML frontmatter and scans `description` fields for prompt injection patterns.
  3. **Script Permissions**: Ensures `.sh` and `.py` files under `scripts/` have executable permissions (`chmod +x`).
  4. **Clean Workspace**: Confirms absence of `__pycache__`, `*.pyc`, and `.env` files.
  5. **Link Integrity**: Resolves all relative markdown links.
  6. **Vendor Digest Integrity**: Computes recursive SHA-256 tree digests of `plugins/adk-developer/skills/` and verifies against `vendored.json` to prevent silent in-tree tampering.
  7. **Trigger Overlap Scanner**: Warns if skill descriptions exhibit high keyword/Jaccard overlap causing potential trigger collisions.

#### [MODIFY] [AGENTS.md](file:///usr/local/google/home/carloscabral/cabral-skills/AGENTS.md)
- Update validation checklist section to reference `scripts/validate_repo.py`.

---

### Phase 4: Hardened CI / GitHub Actions Workflow

#### [NEW] [.github/workflows/skill-audit.yml](file:///usr/local/google/home/carloscabral/cabral-skills/.github/workflows/skill-audit.yml)
- Create GitHub Actions workflow for pushes and pull requests.
- Hardening Controls:
  - Minimal permissions: `permissions: contents: read`.
  - Pin all GitHub Actions to full 40-character commit SHAs.
  - Run `python3 scripts/validate_repo.py` and `shellcheck -S error` on all shell scripts.

---

## Verification Plan

### Automated Verification
```bash
# 1. Run repo validator in report mode
python3 scripts/validate_repo.py

# 2. Run repo validator in auto-remediation mode
python3 scripts/validate_repo.py --fix

# 3. Verify workspace clean status
git status
```

### Manual Verification
- Verify `vendored.json` records SHA-256 tree digests for all vendored skills.

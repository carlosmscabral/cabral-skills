---
name: aws-lambda-fleet-to-cloud-run
description: Migrates large estates of AWS Lambda functions (10–100+ Lambdas in monorepos) to Google Cloud Run. Provides fleet-level discovery, grouping strategy (1:1 vs. consolidation), dependency-graph-based migration wave sequencing, and a consolidated Migration Program Document. Designed to complement the aws-lambda-to-cloud-run-migration skill for per-function deep analysis.
---

# AWS Lambda Fleet → Google Cloud Run Migration Skill

This skill handles **fleet-level** migrations: multiple Lambda functions deployed from a monorepo or shared account. It discovers all functions across a repository, builds a dependency graph, groups them into Cloud Run services, and sequences migrations into waves.

> [!IMPORTANT]
> **Prerequisite Skill**: This skill assumes `aws-lambda-to-cloud-run-migration` is also installed. That skill performs deep, per-function analysis (containerization, SDK refactoring, IaC translation). This skill calls into it for each migration wave. Never duplicate that skill's guidance here.

---

## When to Use Which Skill

| Scenario | Use |
|---|---|
| Single Lambda function to migrate | `aws-lambda-to-cloud-run-migration` |
| 2+ Lambdas, a monorepo, or a shared AWS account to migrate | **This skill** |
| Need per-function Dockerfile, IaC, or SDK refactoring detail | Delegate to `aws-lambda-to-cloud-run-migration` after grouping |

---

## Available Resources

Load the following resources as needed during the workflow:

- **`scripts/analyze_fleet.py`**: Run this first on the monorepo root. Recursively discovers all Lambda functions and produces `fleet_manifest.json` (function inventory + dependency edges). Use `--summary` for a human-readable terminal table. **Read the JSON file immediately after running.**
- **`references/fleet_strategy.md`**: Decision framework for grouping N Lambdas into M Cloud Run services. Covers 1:1, Domain Consolidation, and Sidecar/Platform patterns with a scored decision matrix.
- **`references/dependency_graph.md`**: How to read `dependency_edges` from the fleet manifest, apply topological sort to define migration waves, and maintain a cross-cloud invocation bridge during the transition window.
- **`references/consolidation_patterns.md`**: Step-by-step mechanics for merging multiple Lambda handlers into a single Cloud Run service (Router Pattern, Handler-as-Module, shared initialization).

---

## 3-Phase Fleet Migration Workflow

### Phase 1 — Fleet Discovery

**Goal:** Build a complete inventory of all Lambdas and their relationships.

1. Run the fleet analysis script against the monorepo root:
   ```bash
   python scripts/analyze_fleet.py <repo_root> --output <output_dir> --summary
   ```
2. **Read `fleet_manifest.json` immediately.** Focus on:
   - `fleet_summary`: total function count, runtime distribution, trigger type breakdown.
   - `functions[]`: per-function details (name, runtime, memory, timeout, triggers, layers, VPC).
   - `dependency_edges[]`: directed edges showing which functions invoke or share resources with others.
3. Present the user with the fleet summary table before proceeding.

### Phase 2 — Grouping & Sequencing

**Goal:** Decide which Lambdas become which Cloud Run services, and in what order to migrate them.

1. Load **`references/fleet_strategy.md`** and apply the decision matrix to each function or domain group.
2. Propose a grouping to the user. For each proposed Cloud Run service, state:
   - Which Lambda(s) it replaces
   - The chosen pattern (1:1, Domain Consolidation, or Sidecar)
   - The rationale (ownership, runtime, scaling, shared state)
3. Load **`references/dependency_graph.md`** and perform the topological sort on `dependency_edges`.
4. Propose **Migration Waves** — leaf functions (no outbound dependencies) migrate first. Present the wave plan as a table:

   | Wave | Lambda(s) | Target Cloud Run Service | Pattern | Rationale |
   |---|---|---|---|---|
   | 1 | `FnA`, `FnB` | `svc-orders` | Domain Consolidation | Same data store, same IAM |
   | 2 | `FnC` | `svc-notifications` | 1:1 | Independent scaling need |
   | 3 | `FnD` | `job-reconcile` | 1:1 (Job) | EventBridge cron → Cloud Run Job |

5. Confirm the wave plan with the user before proceeding to Phase 3.

### Phase 3 — Per-Function Migration (Wave Execution)

**Goal:** Migrate each wave using the existing per-function skill.

For each wave:
1. **If consolidating multiple Lambdas:** Load `references/consolidation_patterns.md` and apply the Router or Handler-as-Module pattern to produce a single containerized service.
2. **For each function in the wave:** Invoke the `aws-lambda-to-cloud-run-migration` skill workflow:
   - Run `scripts/analyze_lambda.py <function_dir>` for per-function depth.
   - Apply containerization, SDK refactoring, IaC translation as directed by that skill.
3. **Cross-wave bridge:** While migrating a wave, consult `references/dependency_graph.md` §4 to keep already-migrated services and not-yet-migrated Lambdas talking to each other.
4. After each wave completes, update the Migration Program Document (see §Final Deliverable).

---

## Recommended External Tools

If available in the user's environment:
- **AWS Documentation Tools (`mcp_aws-docs_*`)**: Use `search_documentation` to look up Lambda event source mapping, Step Functions ASL, or EventBridge rule schemas that affect dependency detection.
- **Google Developer Knowledge Tools (`mcp_developer-knowledge_*`)**: Use `search_documents` to find Cloud Run service naming conventions, traffic splitting, and multi-service architectures.

---

## Interactive Guidance

If information is missing, prompt the user:
- "Can you share the monorepo root path or a zip of the project so I can run `analyze_fleet.py`?"
- "Do any of these Lambdas share a DynamoDB table, SNS topic, or SQS queue? If so, which ones?"
- "Are different Lambda functions owned by different teams? That's a strong signal for 1:1 migration over consolidation."
- "Does your organization prefer **Terraform** (Path A) or **scripted `gcloud run deploy`** (Path B) for the resulting IaC? *(→ delegate to `aws-lambda-to-cloud-run-migration` `references/iac_translation.md` for details)*"

---

## Final Deliverable: Migration Program Document

Produce a **Migration Program Document** (markdown) containing:

1. **Fleet Inventory Table** — All discovered functions with runtime, trigger type, memory, and migration complexity rating (Low/Medium/High).
2. **Dependency Graph Summary** — List of `dependency_edges` with a plain-English description of each relationship.
3. **Grouping Decision** — For each proposed Cloud Run service: which Lambdas it replaces, chosen pattern, and rationale.
4. **Wave Plan** — The sequenced migration table (Wave → Functions → Cloud Run Service → Pattern → Rationale).
5. **Cross-Cloud Bridge Notes** — Any temporary bridge patterns needed during transition (Lambda calling Cloud Run, or vice versa).
6. **Per-Function Migration Links** — For each function, a pointer to its individual migration report (produced by `aws-lambda-to-cloud-run-migration`).

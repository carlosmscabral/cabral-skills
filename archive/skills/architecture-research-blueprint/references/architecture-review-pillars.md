# Core Architectural Review & Adversarial Quality Framework

When executing **Phase 2 (Independent Adversarial Review & Quality Gate)** of the `architecture-research-blueprint` workflow, review subagents execute in two sequential stages separated by a **mandatory quality gate**:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        PHASE 2 EXECUTION & QUALITY GATE FLOW                           │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│   [ Phase 1 Specialist Reports (01_... to 0N_...) ]                                    │
│                         │                                                              │
│                         ▼                                                              │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ STAGE 2.1: Pre-Flight Grounding & Depth Quality Gate                           │   │
│   │ • Verify official documentation citations (https://cloud.google.com/...)       │   │
│   │ • Validate API/SDK precision and eliminate hallucinations                      │   │
│   │ • Audit completeness: failure modes, error recovery, concrete schemas          │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
│                         │                                                              │
│                         ▼                                                              │
│             [ Any Defect or Gap Found? ] ───► YES ───► [ MANDATORY REMEDIATION LOOP ]  │
│                         │                                  Fix & Deepen Specialist     │
│                        NO                                  Reports Directly in Place   │
│                         │                                             │                │
│                         ├─────────────────────────────────────────────┘                │
│                         ▼                                                              │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ STAGE 2.2: Well-Architected Framework Review (6 Pillars)                       │   │
│   │ • Reviewer A: Security, Privacy, Zero-Trust, Sandboxing & Compliance           │   │
│   │ • Reviewer B: Reliability, Resilience, Fault Tolerance & Performance SLAs      │   │
│   │ • Reviewer C: FinOps, Unit Economics, IaC Reproducibility & System Design      │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
│                         │                                                              │
│                         ▼                                                              │
│   [ Consolidated Defensive Countermeasures Output to reviews/ ]                        │
│                                                                                        │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Stage 2.1: Pre-Flight Grounding & Depth Quality Gate

Before triggering Well-Architected pillar evaluations, reviewers must audit **each prior specialist document**:

### 1. Grounding & Veracity Verification (Groundness)
- [ ] **Official Documentation Citations:** Is every technical claim, architectural mechanism, service limit, and SDK recommendation backed by valid, official vendor links (`https://cloud.google.com/...` or official upstream docs)?
- [ ] **API, SDK & Feature Accuracy:** Are the referenced APIs, SDK methods, and service features currently available and accurate (no deprecated tools, hallucinated configuration parameters, or non-existent GCP features)?
- [ ] **SLA & Quota Realism:** Are latency metrics (e.g., p95/p99 TTFT, DB query times), throughput numbers, and quota assumptions grounded in published benchmarks and platform invariants rather than optimistic guesses?
- [ ] **Absence of Hand-Waving:** Are concrete service tiers and SKUs specified (e.g., "AlloyDB Omni with pgvector" or "Vertex AI Vector Search with ScaNN index endpoint") rather than generic placeholders (e.g., "use a vector database")?

### 2. Completeness & Technical Depth
- [ ] **Actionable Technical Substance:** Does the analysis contain concrete architectural schemas, configuration snippets, IaC patterns, or data models sufficient for implementation, rather than high-level bullet points?
- [ ] **Failure Modes & Edge Cases:** Does the analysis explicitly detail failure modes (e.g., network partitions, quota exhaustion, poison pills, cold starts, retry storms) and how the component recovers?
- [ ] **Cross-Domain Integration Contracts:** Is it clearly defined how this domain exchanges data, authenticates, and handles backpressure with adjacent orthogonal domains?
- [ ] **Quantitative Trade-offs:** Are architectural decisions supported by quantitative comparisons (cost vs. latency vs. operational overhead) rather than one-sided advocacy?

---

## ⛔ Quality Gate & In-Place Remediation Directive

If **any** specialist document fails Stage 2.1 criteria:
1. **HALT Progression:** Do not spawn or trigger Stage 2.2 Well-Architected reviewers.
2. **Remediate in Place:** Update the specialist markdown document directly (`01_...md` through `0N_...md`) to provide missing citations, replace hallucinated flags with valid API parameters, and detail missing edge cases / schemas.
3. **Re-Verify:** Re-run the Stage 2.1 pre-flight check until all specialist documents achieve 100% compliance.

---

## Stage 2.2: The 6 Well-Architected Framework Review Pillars

Once all specialist reports pass the Stage 2.1 gate, reviewers audit the proposed topologies against the 6 pillars:

### Pillar 1: Security, Privacy & Compliance
**Reviewer Objective:** Ensure defense-in-depth, least-privilege access, perimeter isolation, and compliance alignment across all components.
- [ ] **Zero-Trust & Identity:** Are service-to-service calls authenticated via mTLS / Workload Identity Federation instead of static API keys or long-lived service account keys?
- [ ] **Perimeter Defense & Data Exfiltration:** Are VPC Service Controls (VPC-SC) and Private Service Connect (PSC) configured to protect sensitive APIs and storage buckets from exfiltration?
- [ ] **Data Protection at Rest & Transit:** Is data encrypted in transit (TLS 1.3) and at rest with Customer-Managed Encryption Keys (CMEK / Cloud KMS) where required?
- [ ] **Blast Radius & Sandboxing:** If a workload is compromised (e.g., RCE), is the kernel/container boundary isolated (gVisor, GKE Sandbox, or dedicated projects)?
- [ ] **Access & Multi-Tenancy Scoping (if applicable):** Are data queries and tenant contexts verified via tamper-proof JWT claims rather than unverified client headers?
- [ ] **Auditability & Compliance:** Are administrative and data access logs exported to an immutable, retention-locked sink (Cloud Storage Bucket Lock WORM / BigQuery) for regulatory compliance (SOC2, ISO 27001, HIPAA, GDPR/LGPD)?

---

### Pillar 2: Reliability, Resilience & Fault Tolerance
**Reviewer Objective:** Guarantee that the system meets its availability, recovery time (RTO), and recovery point (RPO) objectives under high concurrency, cascading failures, or regional outages.
- [ ] **Redundancy & Regional Topology:** Is the architecture deployed across multiple zones or dual/multi-regions with automated health checking and failover routing?
- [ ] **Backpressure, Rate Limiting & Bulkheads:** Are rate limiters (token bucket / sliding window) and circuit breakers implemented at ingress points to protect downstream dependencies from surges?
- [ ] **Connection & Resource Pool Exhaustion:** Are connection poolers (e.g., PgBouncer, AlloyDB built-in pooler) and client retry backoffs (exponential jitter) sized to prevent database/thread exhaustion?
- [ ] **Graceful Degradation:** Can non-critical features degrade gracefully (e.g., fallback to cached data, asynchronous queueing) during partial downstream outages?
- [ ] **Disaster Recovery & Backup Automation:** Are automated, point-in-time recovery (PITR) backups enabled, tested, and validated with clear RTO/RPO metrics?

---

### Pillar 3: FinOps, Cost Optimization & Unit Economics
**Reviewer Objective:** Ensure infrastructure is economically sustainable, rightsized, and aligned with transparent unit economics and cost attribution.
- [ ] **Right-Sizing & Auto-Scaling Bounds:** Are compute workloads configured with realistic min/max scaling thresholds, CPU/memory requests, and limits to avoid overprovisioning waste?
- [ ] **Pricing Model Selection:** Are architectural choices evaluated against workload profiles (Serverless/Pay-per-use vs. GKE Autopilot vs. Committed Use Discounts / CUDs)?
- [ ] **Cost Attribution & Metering:** Can consumption (compute, memory, storage, egress) be accurately mapped to cost centers, teams, or customer tiers (e.g., GKE Cost Allocation export to BigQuery)?
- [ ] **Data Lifecycle & Tiering:** Are storage lifecycle rules configured to transition cold data to Nearline/Coldline/Archive storage classes automatically?
- [ ] **Network Egress Optimization:** Is cross-region and internet egress minimized via CDN caching, PSC endpoints, and localized traffic routing?

---

### Pillar 4: Performance & Scalability
**Reviewer Objective:** Ensure the system sustains latency targets (p95/p99 SLA) and scales elastically without architectural bottlenecks.
- [ ] **Latency Budgets & Caching Hierarchy:** Are multi-tier caching strategies (Edge CDN, Memorystore Redis, in-memory app cache) in place for hot read paths?
- [ ] **Database I/O & Sharding Limits:** Are relational query plans indexed, statement timeouts set, and read-heavy queries offloaded to replicas or analytical layers?
- [ ] **Asynchronous Decoupling:** Are long-running, CPU-intensive, or I/O-bound tasks offloaded to asynchronous message queues (Pub/Sub, Cloud Tasks) instead of blocking synchronous request threads?
- [ ] **Network Acceleration:** Are Anycast global routing, HTTP/3, and keep-alive connection reuse leveraged across ingress gateways?

---

### Pillar 5: Operational Excellence & Developer Experience
**Reviewer Objective:** Ensure the architecture can be deployed, operated, monitored, and evolved safely with minimal manual intervention.
- [ ] **Infrastructure as Code (IaC):** Is 100% of the topology declared in reproducible IaC (Terraform, Config Connector, Helm)?
- [ ] **Deployment Safety & Zero Downtime:** Are canary rollouts, blue/green deployments, and database schema expand/contract patterns defined to eliminate maintenance downtime?
- [ ] **Observability & SLIs/SLOs:** Are golden signals (Latency, Traffic, Errors, Saturation) tracked with structured logging, OpenTelemetry tracing, and alerting policies?
- [ ] **Automated Onboarding & Provisioning:** Can new environments, microservices, or tenant boundaries be provisioned programmatically in minutes via automated CI/CD pipelines?
- [ ] **Runbooks & Chaos Engineering:** Are failure modes documented with actionable runbooks and verified through chaos testing experiments?

---

### Pillar 6: System Design, Modularity & Architectural Elegance
**Reviewer Objective:** Validate loose coupling, clear domain boundaries, clean API contracts, and technology-agnostic sound engineering.
- [ ] **Domain Boundary Cohesion:** Are service and data boundaries aligned with business capabilities (Bounded Contexts) rather than arbitrary technical splits?
- [ ] **API Contract Evolution:** Are API contracts versioned (semantic versioning, Protobuf backwards-compatibility) with deprecation policies?
- [ ] **Architectural Decision Records (ADRs):** Are non-obvious trade-offs documented with explicit rationale, alternatives considered, and consequences accepted?
- [ ] **Vendor Neutrality vs. Managed Leverage:** Is there a clear, intentional balance between adopting high-productivity managed services (e.g., Spanner, BigQuery) vs. avoiding unnecessary proprietary lock-in?

---

## Standardized Review Output Schema

Reviewers must format their findings under `reviews/` using this structure:

```markdown
# Adversarial Review: [Domain Name / Review Focus]

## 1. Stage 2.1 Pre-Flight Grounding & Depth Verification
- **Document Audited:** `01_domain_name.md`
- **Citation & Veracity Check:** [PASS / DEFECT — citations, API validity, quota realism]
- **Completeness & Depth Check:** [PASS / DEFECT — failure modes, concrete schemas, edge cases]
- **Remediations Applied in Place:** [Details of any in-place fixes made before proceeding]

## 2. Stage 2.2 Well-Architected Framework Audit Findings
- **Finding [Pillar.ID]:** [Description of vulnerability, bottleneck, or unaddressed risk]
  - *Risk / Impact:* [Why this is problematic under production conditions]
  - *Defensive Countermeasure:* [Concrete architectural fix to incorporate during consolidation]
```

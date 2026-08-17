# The 3 Core Architectural Review Pillars

When executing Phase 2 (Adversarial Review) of the `architecture-research-blueprint` workflow, reviewer subagents must rigorously audit specialist reports against these three audit pillars:

---

## Pillar 1: Security, Tenant Isolation & Blast Radius

**Reviewer Objective:** Ensure that no single failure, compromise, or misconfiguration in one tenant can compromise another tenant's data, identity, or resource boundaries.

### Checklist:
- [ ] **Cross-Tenant Data Leakage:** Are persistence queries strictly scoped (e.g., Row-Level Security in PostgreSQL, FGAC in Spanner, or physical DB/Schema isolation)?
- [ ] **Identity & Token Impersonation:** Is tenant context passed via tamper-proof claims (e.g., verified JWT claims injected at Ingress/API Gateway) rather than unverified client headers?
- [ ] **Perimeter & Exfiltration Defense:** Are VPC Service Controls (VPC-SC) perimeters and Private Service Connect (PSC) service attachments correctly partitioned?
- [ ] **Regulatory Compliance:** Does the architecture satisfy data residency, Customer-Managed Encryption Keys (CMEK/BYOK), and immutable audit logging (Bucket Lock WORM / Cloud Audit Logs)?
- [ ] **Blast Radius Containment:** What happens if Tenant A's container is exploited via an RCE? Does gVisor (GKE Sandbox) or dedicated compute isolate the kernel?

---

## Pillar 2: Reliability, Contention & Noisy Neighbor Mitigation

**Reviewer Objective:** Guarantee that unexpected spikes, rogue queries, or heavy workloads from one tenant do not degrade the latency, throughput, or availability of peer tenants.

### Checklist:
- [ ] **Ingress & API Rate Limiting:** Are token-bucket or sliding-window rate limiters enforced per `tenant_id` at the edge (Cloud Armor / Apigee) to prevent DDoS or runaway API consumers?
- [ ] **Database Connection Pool Exhaustion:** Are connection poolers (PgBouncer, AlloyDB built-in pooler) sized appropriately to avoid exhausting database worker limits when thousands of tenants connect simultaneously?
- [ ] **Compute Resource Slicing:** Are Kubernetes `ResourceQuotas`, `LimitRanges`, and PriorityClasses configured per tenant namespace?
- [ ] **Database I/O & CPU Starvation:** In shared databases, are query timeout guards, statement timeouts, and read replica offloading in place for heavy analytical reporting?
- [ ] **Graceful Degradation & Bulkheads:** Are VIP/Enterprise tenants segregated onto dedicated node pools or silo instances to insulate core revenue streams from trial tier turbulence?

---

## Pillar 3: FinOps, Cost Allocation & Operational Overhead

**Reviewer Objective:** Ensure the platform remains economically viable, maintainable at scale, and capable of precise gross margin attribution per customer.

### Checklist:
- [ ] **Cost per Tenant Attribution:** Can infrastructure consumption (compute, memory, storage, egress) be deterministically mapped back to individual tenant IDs (e.g., GKE Cost Allocation to BigQuery)?
- [ ] **Idle Capacity Overhead (The Silo Tax):** If proposing Silo (Single-Tenant) topologies, is the cost of overprovisioned, idle baseline infrastructure accounted for in pricing tiers?
- [ ] **Schema Migration Scaling ($O(N)$ vs $O(1)$):** Does releasing a database migration require updating 5,000 isolated schemas sequentially (high failure risk, long maintenance windows) or a single shared schema with zero-downtime expand/contract patterns?
- [ ] **Automated Tenant Onboarding:** Can a new tenant be fully provisioned (IAM, DNS, Database, Namespace) programmatically via Terraform / Kubernetes Operators in under 60 seconds without manual SRE intervention?
- [ ] **Offboarding & Data Sanitization:** Is there an automated, auditable process for hard data purging and crypto-erasure upon contract termination?
